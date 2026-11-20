"""Rebuild the notebook's top-100 ME_L type-to-type connectome matrix."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


# Keep aligned with BioWire notebook Step 4. The sign is applied to the
# presynaptic row, as in W_4bit_signed = W_4bit_unsigned * signs[:, None].
INHIBITORY_TYPES = frozenset({
    "C2", "C3", "Mi9", "Dm1", "Dm2", "Dm3", "Dm4", "Dm7", "Dm8", "Dm9",
    "Dm10", "Dm11", "Dm12", "Dm13", "Dm14", "Am", "Pm1", "Pm2", "Lai",
    "aMe12", "OA-AL2b1", "L4", "Tm4", "Tm9", "Tm20", "TmY4", "TmY5a",
    "TmY10", "Lawf1", "Lawf2",
})
OFF_TYPES = frozenset({"L2", "Tm1", "T5a", "T5b", "T5c", "T5d", "C3"})
T4T5_SUBTYPES = ("T4a", "T4b", "T4c", "T4d", "T5a", "T5b", "T5c", "T5d")


@dataclass(frozen=True)
class ConnectomeModel:
    type_names: tuple[str, ...]
    weights_signed: np.ndarray
    weights_unsigned: np.ndarray
    raw_global_max: float
    model_size: int
    source_mode: str
    source_hashes: dict[str, str]

    @property
    def type_to_index(self) -> dict[str, int]:
        return {name: i for i, name in enumerate(self.type_names)}

    def manifest(self) -> dict[str, object]:
        return {
            "model": "BioWire notebook ME_L top-type network",
            "model_size": self.model_size,
            "type_names": list(self.type_names),
            "raw_global_max": self.raw_global_max,
            "weight_quantization": "round(clip(raw/global_max, 0, 1) * 15)",
            "inhibitory_sign": "presynaptic type row sign, matching notebook Step 4",
            "source_mode": self.source_mode,
            "source_hashes_sha256": self.source_hashes,
            "pulse_input_node": "L1",
            "pulse_input_rationale": (
                "The ME_L extracted network has no R1-6 node; LM331 events enter at its L1 boundary node."
            ),
        }


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_top_type_connectome(
    cell_types: pd.DataFrame,
    connections: pd.DataFrame,
    *,
    model_size: int = 100,
    force_t4_t5: bool = True,
    source_mode: str = "provided-tables",
    source_hashes: dict[str, str] | None = None,
) -> ConnectomeModel:
    """Build signed quantized type-level weights using the notebook's method."""
    if model_size < 2:
        raise ValueError("model_size must be at least 2")
    required_cells = {"root_id", "primary_type"}
    required_connections = {"pre_root_id", "post_root_id", "syn_count", "neuropil"}
    if not required_cells.issubset(cell_types.columns):
        raise ValueError(f"cell_types missing columns: {sorted(required_cells - set(cell_types.columns))}")
    if not required_connections.issubset(connections.columns):
        raise ValueError(
            f"connections missing columns: {sorted(required_connections - set(connections.columns))}"
        )

    me_l = connections.loc[connections["neuropil"].eq("ME_L")].copy()
    if me_l.empty:
        raise ValueError("No ME_L connections found")
    me_l_ids = set(me_l["pre_root_id"].unique()) | set(me_l["post_root_id"].unique())
    me_l_types = cell_types.loc[cell_types["root_id"].isin(me_l_ids), ["root_id", "primary_type"]]
    if me_l_types.empty:
        raise ValueError("No ME_L neuron types matched the cell type table")
    type_counts = me_l_types["primary_type"].value_counts()
    top_pool = type_counts.index.tolist()
    if force_t4_t5:
        present = [name for name in T4T5_SUBTYPES if name in type_counts.index]
        forced = [name for name in present if name not in top_pool[:model_size]]
        selected = (forced + [name for name in top_pool if name not in forced])[:model_size]
    else:
        selected = top_pool[:model_size]
    if "L1" not in selected:
        raise ValueError("The selected ME_L model has no L1 node for the documented input boundary")

    # Match the notebook's joins and type-to-type synapse-count aggregation.
    typed = me_l.merge(
        cell_types.rename(columns={"root_id": "pre_root_id", "primary_type": "pre_type"})[
            ["pre_root_id", "pre_type"]
        ], on="pre_root_id", how="left"
    ).merge(
        cell_types.rename(columns={"root_id": "post_root_id", "primary_type": "post_type"})[
            ["post_root_id", "post_type"]
        ], on="post_root_id", how="left"
    )
    typed = typed.loc[typed["pre_type"].isin(selected) & typed["post_type"].isin(selected)]
    grouped = typed.groupby(["pre_type", "post_type"], sort=False)["syn_count"].sum()
    if grouped.empty:
        raise ValueError("No type-to-type connections remain in the selected ME_L model")

    index = {name: i for i, name in enumerate(selected)}
    raw = np.zeros((len(selected), len(selected)), dtype=np.float64)
    for (pre_type, post_type), syn_count in grouped.items():
        raw[index[pre_type], index[post_type]] = float(syn_count)
    global_max = float(raw.max())
    if not np.isfinite(global_max) or global_max <= 0:
        raise ValueError("Invalid global maximum in type-to-type connection matrix")

    unsigned = np.rint(np.clip(raw / global_max, 0.0, 1.0) * 15.0).astype(np.int8)
    signs = np.array([-1 if name in INHIBITORY_TYPES else 1 for name in selected], dtype=np.int8)
    signed = (unsigned * signs[:, None]).astype(np.int8)
    return ConnectomeModel(
        type_names=tuple(selected),
        weights_signed=signed,
        weights_unsigned=unsigned,
        raw_global_max=global_max,
        model_size=len(selected),
        source_mode=source_mode,
        source_hashes=source_hashes or {},
    )


def load_flywire_connectome(data_dir: str | Path, *, model_size: int = 100) -> ConnectomeModel:
    """Load the existing FlyWire CSV.GZ files and rebuild the notebook model."""
    root = Path(data_dir)
    cells_path = root / "consolidated_cell_types.csv.gz"
    connections_path = root / "connections_princeton_no_threshold.csv.gz"
    for path in (cells_path, connections_path):
        if not path.exists():
            raise FileNotFoundError(f"Required FlyWire table not found: {path}")
        if path.stat().st_size < 1024:
            raise ValueError(f"{path} appears to be missing or an unresolved Git LFS pointer")
    cells = pd.read_csv(cells_path, usecols=["root_id", "primary_type"])
    connections = pd.read_csv(
        connections_path,
        usecols=["pre_root_id", "post_root_id", "syn_count", "neuropil"],
    )
    hashes = {
        cells_path.name: _hash_file(cells_path),
        connections_path.name: _hash_file(connections_path),
    }
    return build_top_type_connectome(
        cells,
        connections,
        model_size=model_size,
        source_mode="flywire-csv",
        source_hashes=hashes,
    )


def save_connectome_model(model: ConnectomeModel, path: str | Path) -> None:
    """Write the compact signed network and its source provenance to NPZ."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "format": "fly-brain-adc-connectome-v1",
        "type_names": list(model.type_names),
        "raw_global_max": model.raw_global_max,
        "model_size": model.model_size,
        "source_mode": model.source_mode,
        "source_hashes": model.source_hashes,
    }
    with target.open("wb") as f:
        np.savez_compressed(
            f,
            weights_signed=model.weights_signed.astype(np.int8),
            weights_unsigned=model.weights_unsigned.astype(np.int8),
            metadata=np.asarray(json.dumps(metadata, sort_keys=True)),
        )


def load_connectome_model(path: str | Path) -> ConnectomeModel:
    """Load a compact prebuilt model without loading the large FlyWire CSVs."""
    source = Path(path)
    with np.load(source, allow_pickle=False) as archive:
        if set(archive.files) != {"weights_signed", "weights_unsigned", "metadata"}:
            raise ValueError(f"{source} is not a supported connectome NPZ")
        metadata = json.loads(str(archive["metadata"].item()))
        if metadata.get("format") != "fly-brain-adc-connectome-v1":
            raise ValueError("unsupported connectome model format")
        type_names = tuple(str(name) for name in metadata["type_names"])
        signed = np.asarray(archive["weights_signed"], dtype=np.int8)
        unsigned = np.asarray(archive["weights_unsigned"], dtype=np.int8)
    expected_shape = (len(type_names), len(type_names))
    if not type_names or signed.shape != expected_shape or unsigned.shape != expected_shape:
        raise ValueError("connectome matrices do not match the declared type-name dimensions")
    if int(metadata["model_size"]) != len(type_names):
        raise ValueError("connectome model_size does not match the type-name dimensions")
    raw_global_max = float(metadata["raw_global_max"])
    if not np.isfinite(raw_global_max) or raw_global_max <= 0:
        raise ValueError("connectome raw_global_max must be finite and positive")
    if np.any(unsigned < 0) or np.any(unsigned > 15) or np.any(np.abs(signed) > 15):
        raise ValueError("connectome weights are outside the 4-bit range")
    if not np.array_equal(np.abs(signed), unsigned):
        raise ValueError("signed/unsigned connectome matrices are inconsistent")
    return ConnectomeModel(
        type_names=type_names,
        weights_signed=signed,
        weights_unsigned=unsigned,
        raw_global_max=raw_global_max,
        model_size=int(metadata["model_size"]),
        source_mode=str(metadata["source_mode"]),
        source_hashes={str(k): str(v) for k, v in metadata.get("source_hashes", {}).items()},
    )
