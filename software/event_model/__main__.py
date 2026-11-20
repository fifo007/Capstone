"""Command-line entry point for the event-model simulation pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .connectome import load_connectome_model, load_flywire_connectome
from .decoder import FeatureDecoder
from .events import load_event_windows
from .network import NetworkConfig, simulate_event_window
from .pipeline import calibrate_labeled_windows, run_synthetic_sweep, validate_decoder_compatibility


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the hardware-free pulse-driven Fly Brain ADC demo")
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo", help="run a labeled synthetic pulse-frequency sweep")
    demo.add_argument("--data-dir", default="biowire", help="directory containing the FlyWire CSV.GZ tables")
    demo.add_argument("--output-dir", default="runs/event_model_demo")
    demo.add_argument("--samples", type=int, default=64)
    demo.add_argument("--duration-s", type=float, default=0.2)
    demo.add_argument("--frequency-min-hz", type=float, default=50.0)
    demo.add_argument("--frequency-max-hz", type=float, default=400.0)
    demo.add_argument("--event-gain", type=float, default=1.0)
    demo.add_argument("--w-scale", type=float, default=0.5)
    demo.add_argument("--event-source", choices=("periodic", "poisson"), default="periodic")
    demo.add_argument("--seed", type=int, default=42)
    demo.add_argument("--model-size", type=int, default=100)
    calibrate = subparsers.add_parser("calibrate", help="fit a decoder from labeled event-window CSV files")
    calibrate.add_argument("--events-csv", required=True)
    calibrate.add_argument("--windows-csv", required=True)
    calibrate.add_argument("--data-dir", default="biowire")
    calibrate.add_argument("--output-dir", required=True)
    calibrate.add_argument("--event-gain", type=float, required=True)
    calibrate.add_argument("--w-scale", type=float, default=0.2)
    calibrate.add_argument("--seed", type=int, default=42)
    calibrate.add_argument("--model-size", type=int, default=100)
    calibrate.add_argument("--connectome-file", help="use a prebuilt compact .npz model instead of loading FlyWire CSVs")
    calibrate.add_argument("--allow-synthetic", action="store_true")
    infer = subparsers.add_parser("infer", help="decode one stored timestamped event window")
    infer.add_argument("--events-csv", required=True)
    infer.add_argument("--windows-csv", required=True)
    infer.add_argument("--sample-id", required=True)
    infer.add_argument("--decoder", required=True)
    infer.add_argument("--data-dir", default="biowire")
    infer.add_argument("--output", required=True)
    infer.add_argument("--event-gain", type=float, required=True)
    infer.add_argument("--w-scale", type=float, default=0.2)
    infer.add_argument("--seed", type=int, default=42)
    infer.add_argument("--model-size", type=int, default=100)
    infer.add_argument("--connectome-file", help="use a prebuilt compact .npz model instead of loading FlyWire CSVs")
    args = parser.parse_args()

    if args.command == "demo":
        result = run_synthetic_sweep(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            sample_count=args.samples,
            duration_s=args.duration_s,
            frequency_min_hz=args.frequency_min_hz,
            frequency_max_hz=args.frequency_max_hz,
            event_gain=args.event_gain,
            w_scale=args.w_scale,
            event_source=args.event_source,
            seed=args.seed,
            model_size=args.model_size,
        )
        print(json.dumps(result["heldout_metrics"], indent=2))
        print(f"Artifacts written to: {args.output_dir}")
        print("Synthetic simulation only; no hardware or LM331 calibration was used.")
    elif args.command == "calibrate":
        result = calibrate_labeled_windows(
            events_csv=args.events_csv,
            windows_csv=args.windows_csv,
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            event_gain=args.event_gain,
            w_scale=args.w_scale,
            seed=args.seed,
            model_size=args.model_size,
            allow_synthetic=args.allow_synthetic,
            connectome_file=args.connectome_file,
        )
        print(json.dumps(result["heldout_metrics"], indent=2))
        print(f"Decoder and calibration results written to: {args.output_dir}")
    elif args.command == "infer":
        windows = load_event_windows(args.events_csv, args.windows_csv)
        matches = [window for window in windows if window.sample_id == args.sample_id]
        if len(matches) != 1:
            parser.error(f"sample_id {args.sample_id!r} was not found exactly once")
        decoder = FeatureDecoder.load(args.decoder)
        model = (
            load_connectome_model(args.connectome_file)
            if args.connectome_file
            else load_flywire_connectome(args.data_dir, model_size=args.model_size)
        )
        readouts = tuple(name for name in ("L1", "Mi1") if name in model.type_to_index)
        config = NetworkConfig(w_scale=args.w_scale, seed=args.seed, readout_types=readouts)
        validate_decoder_compatibility(decoder, connectome=model, config=config, event_gain=args.event_gain)
        features = simulate_event_window(model, matches[0], event_gain=args.event_gain, config=config)
        result = {
            **features,
            "input_voltage_v": matches[0].input_voltage_v,
            "decoded_voltage_v": float(decoder.predict_voltage([features])[0]),
            "decoded_code_6bit": int(decoder.predict_code([features])[0]),
            "input_source": matches[0].source,
            "synthetic_events": matches[0].synthetic,
            "warning": "Hardware meaning depends on measured calibration and matching network parameters.",
        }
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        result_json = json.dumps(result, indent=2, allow_nan=False)
        target.write_text(result_json + "\n", encoding="utf-8")
        print(result_json)
        print(f"Inference record written to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
