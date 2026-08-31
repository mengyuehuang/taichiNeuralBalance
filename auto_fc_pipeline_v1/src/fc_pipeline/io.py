from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import mne


def find_raw_files(raw_data_dir: Path, file_glob: str) -> list[Path]:
    return sorted(raw_data_dir.glob(file_glob))


def infer_subject_id(file_path: Path, subject_regex: str) -> str:
    match = re.search(subject_regex, file_path.stem)
    if not match:
        raise ValueError(f"Could not infer subject id from {file_path.name!r}")
    if match.lastindex and match.lastindex > 1:
        return "_".join(group for group in match.groups() if group)
    return match.group(1)


def read_raw(file_path: Path, file_format: str, preload: bool = True) -> mne.io.BaseRaw:
    fmt = file_format.lower()
    if fmt in {"brainvision", "vhdr"}:
        return mne.io.read_raw_brainvision(file_path, preload=preload)
    if fmt == "edf":
        return mne.io.read_raw_edf(file_path, preload=preload)
    if fmt == "cnt":
        return mne.io.read_raw_cnt(file_path, preload=preload)
    if fmt == "bdf":
        return mne.io.read_raw_bdf(file_path, preload=preload)
    if fmt == "fif":
        return mne.io.read_raw_fif(file_path, preload=preload)
    raise ValueError(
        f"Unsupported raw.file_format={file_format!r}. "
        "Add a reader in fc_pipeline.io.read_raw after the real data format is confirmed."
    )


def drop_configured_channels(raw: mne.io.BaseRaw, raw_config: dict[str, Any]) -> None:
    keep_indices = raw_config.get("load_channel_indices_1based")
    if keep_indices:
        keep_zero_based = {int(idx) - 1 for idx in keep_indices}
        to_drop = [
            ch_name
            for idx, ch_name in enumerate(raw.ch_names)
            if idx not in keep_zero_based
        ]
        if to_drop:
            raw.drop_channels(to_drop)

    drop_last_n = int(raw_config.get("drop_last_n_channels") or 0)
    if drop_last_n > 0:
        raw.drop_channels(raw.ch_names[-drop_last_n:])

    configured = [ch for ch in raw_config.get("drop_channels", []) if ch in raw.ch_names]
    if configured:
        raw.drop_channels(configured)
