from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import resolve_path


def corrected_output_root(config: dict[str, Any]) -> Path:
    configured = config["paths"].get("corrected_output_root")
    if configured:
        return resolve_path(config, configured)

    raise ValueError('Set paths.corrected_output_root in the current HC config; legacy global output paths are not supported.')


def participant_output_paths(config: dict[str, Any], subject: str) -> dict[str, Path]:
    root = corrected_output_root(config) / str(subject)
    static = root / "04_static_fc"
    return {
        "root": root,
        "blocks": root / "01_block_level_eeg",
        "montage_aligned": root / "01_block_level_eeg" / "montage_aligned",
        "source_model": root / "02_source_model",
        "roi_timeseries": root / "03_roi_timeseries",
        "static_fc": static,
        "matrices": static / "matrices",
        "figures": static / "figures",
        "tables": static / "tables",
    }


def ensure_participant_output_paths(config: dict[str, Any], subject: str) -> dict[str, Path]:
    paths = participant_output_paths(config, subject)
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths
