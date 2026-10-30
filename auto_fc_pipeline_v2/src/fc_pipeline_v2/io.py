from __future__ import annotations

import re
from pathlib import Path
from typing import Any


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
