"""A small, serializable readout from neural spike features to a 6-bit code."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np


def spike_feature_names(readout_types: Sequence[str]) -> tuple[str, ...]:
    """Feature schema uses neural outputs only, never input rate/count labels."""
    suffixes = ("spike_count", "first_latency_ms", "mean_isi_ms")
    return tuple(f"{name}_{suffix}" for name in readout_types for suffix in suffixes)


def _matrix(rows: Iterable[Mapping[str, object]], feature_names: Sequence[str]) -> np.ndarray:
    row_list = list(rows)
    if not row_list:
        raise ValueError("at least one feature row is required")
    missing = [key for key in feature_names if key not in row_list[0]]
    if missing:
        raise ValueError(f"feature rows are missing columns: {missing}")
    values = np.asarray([[float(row[key]) for key in feature_names] for row in row_list])
    if values.ndim != 2 or not np.isfinite(values).all():
        raise ValueError("feature rows must contain finite numeric values")
    return values


@dataclass(frozen=True)
class FeatureDecoder:
    """Ridge-linear decoder with explicit feature scaling and 6-bit quantizer."""

    feature_names: tuple[str, ...]
    mean: tuple[float, ...]
    scale: tuple[float, ...]
    coefficients: tuple[float, ...]
    intercept: float
    ridge_alpha: float
    training_samples: int
    calibration_source: str
    training_metadata: dict[str, object] | None = None

    @classmethod
    def fit(
        cls,
        rows: Iterable[Mapping[str, object]],
        target_voltage_v: Sequence[float],
        *,
        feature_names: Sequence[str],
        ridge_alpha: float = 1e-3,
        calibration_source: str,
        training_metadata: Mapping[str, object] | None = None,
    ) -> "FeatureDecoder":
        if not feature_names:
            raise ValueError("feature_names must not be empty")
        if ridge_alpha < 0 or not np.isfinite(ridge_alpha):
            raise ValueError("ridge_alpha must be finite and non-negative")
        x = _matrix(rows, feature_names)
        y = np.asarray(target_voltage_v, dtype=float)
        if y.ndim != 1 or len(y) != len(x):
            raise ValueError("one target voltage is required for every feature row")
        if not np.isfinite(y).all() or np.any((y < 0.0) | (y > 1.0)):
            raise ValueError("target voltages must be finite and within [0, 1] V")

        mean = x.mean(axis=0)
        scale = x.std(axis=0)
        scale[scale == 0.0] = 1.0
        standardized = (x - mean) / scale
        x_center = standardized - standardized.mean(axis=0)
        y_mean = float(y.mean())
        y_center = y - y_mean
        gram = x_center.T @ x_center
        coef = np.linalg.solve(gram + ridge_alpha * np.eye(gram.shape[0]), x_center.T @ y_center)
        intercept = y_mean - float(standardized.mean(axis=0) @ coef)
        return cls(
            feature_names=tuple(feature_names),
            mean=tuple(float(v) for v in mean),
            scale=tuple(float(v) for v in scale),
            coefficients=tuple(float(v) for v in coef),
            intercept=intercept,
            ridge_alpha=float(ridge_alpha),
            training_samples=len(y),
            calibration_source=calibration_source,
            training_metadata=dict(training_metadata or {}),
        )

    def predict_voltage(self, rows: Iterable[Mapping[str, object]]) -> np.ndarray:
        x = _matrix(rows, self.feature_names)
        standardized = (x - np.asarray(self.mean)) / np.asarray(self.scale)
        return np.clip(standardized @ np.asarray(self.coefficients) + self.intercept, 0.0, 1.0)

    def predict_code(self, rows: Iterable[Mapping[str, object]]) -> np.ndarray:
        """Map [0, 1] V to nearest of 64 endpoint-spaced codes, 0 through 63."""
        voltage = self.predict_voltage(rows)
        return np.rint(voltage * 63.0).astype(np.uint8)

    def to_dict(self) -> dict[str, object]:
        return {
            "format": "fly-brain-adc-feature-decoder-v1",
            "feature_names": list(self.feature_names),
            "mean": list(self.mean),
            "scale": list(self.scale),
            "coefficients": list(self.coefficients),
            "intercept": self.intercept,
            "ridge_alpha": self.ridge_alpha,
            "training_samples": self.training_samples,
            "calibration_source": self.calibration_source,
            "training_metadata": self.training_metadata or {},
            "quantizer": "round(clip(voltage_v, 0, 1) * 63)",
        }

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "FeatureDecoder":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("format") != "fly-brain-adc-feature-decoder-v1":
            raise ValueError("unsupported decoder format")
        return cls(
            feature_names=tuple(data["feature_names"]),
            mean=tuple(float(v) for v in data["mean"]),
            scale=tuple(float(v) for v in data["scale"]),
            coefficients=tuple(float(v) for v in data["coefficients"]),
            intercept=float(data["intercept"]),
            ridge_alpha=float(data["ridge_alpha"]),
            training_samples=int(data["training_samples"]),
            calibration_source=str(data["calibration_source"]),
            training_metadata=dict(data.get("training_metadata", {})),
        )
