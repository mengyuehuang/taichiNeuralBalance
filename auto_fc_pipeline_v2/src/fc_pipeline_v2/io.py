from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np


def find_files(folder: Path, pattern: str) -> list[Path]:
    return sorted(folder.glob(pattern))


def read_backprojected_eeglab_set(file_path: Path):
    """Read an EEGLAB .set backprojected file as an MNE Raw or Epochs object."""
    import mne

    try:
        return mne.io.read_raw_eeglab(file_path, preload=True)
    except Exception as raw_error:
        try:
            return mne.read_epochs_eeglab(file_path)
        except Exception as epochs_error:
            raise RuntimeError(
                f"Could not read {file_path} as EEGLAB Raw or Epochs. "
                f"Raw error: {raw_error}; Epochs error: {epochs_error}"
            ) from epochs_error


def summarize_mne_object(eeg) -> dict[str, Any]:
    info = eeg.info
    summary = {
        "type": type(eeg).__name__,
        "sfreq": float(info["sfreq"]),
        "n_channels": len(info["ch_names"]),
        "channel_names": list(info["ch_names"]),
        "bads": list(info.get("bads", [])),
    }
    if hasattr(eeg, "n_times"):
        summary["n_times"] = int(eeg.n_times)
    if hasattr(eeg, "times"):
        summary["duration_seconds"] = float(eeg.times[-1] - eeg.times[0]) if len(eeg.times) else 0.0
    if hasattr(eeg, "events"):
        summary["n_epochs"] = int(len(eeg.events))
    return summary


def infer_subject_id(file_path: Path, subject_regex: str) -> str:
    match = re.search(subject_regex, file_path.stem)
    if not match:
        raise ValueError(f"Could not infer subject id from {file_path.name!r}")
    return match.group(1)


def infer_block_name(file_path: Path, block_patterns: dict[str, list[str]]) -> str:
    stem_lower = file_path.stem.lower()
    for block_name, patterns in block_patterns.items():
        for pattern in patterns:
            if pattern.lower() in stem_lower:
                return block_name
    raise ValueError(f"Could not infer block type from {file_path.name!r}")


def infer_hc_label(file_path: Path) -> str:
    match = re.search(r"HC\d+", file_path.stem, flags=re.IGNORECASE)
    return match.group(0).upper() if match else ""


def load_parcel_timeseries(file_path: Path, timeseries_config: dict[str, Any]) -> np.ndarray:
    data = np.load(file_path)
    if data.ndim != 2:
        raise ValueError(f"Expected a 2D parcel time-series array, got shape {data.shape} from {file_path}")

    orientation = timeseries_config.get("orientation", "parcels_by_time")
    if orientation == "parcels_by_time":
        parcels_by_time = data
    elif orientation == "time_by_parcels":
        parcels_by_time = data.T
    else:
        raise ValueError(f"Unsupported timeseries.orientation={orientation!r}")

    drop_last_n = int(timeseries_config.get("drop_last_n_labels") or 0)
    if drop_last_n > 0:
        parcels_by_time = parcels_by_time[:-drop_last_n, :]

    expected = timeseries_config.get("expected_n_parcels")
    if expected is not None and parcels_by_time.shape[0] != int(expected):
        raise ValueError(
            f"Expected {expected} parcels after medial-wall handling, "
            f"got {parcels_by_time.shape[0]} for {file_path.name}"
        )

    return parcels_by_time.astype(float, copy=False)
