from __future__ import annotations

from pathlib import Path
from typing import Any

import mne
import numpy as np


def apply_hernandez_montage(
    raw: mne.io.BaseRaw,
    montage_path: Path,
    channel_config: dict[str, Any],
) -> mne.io.BaseRaw:
    rename_map = {
        old: new
        for old, new in channel_config.get("rename_map", {}).items()
        if old in raw.ch_names
    }
    if rename_map:
        raw.rename_channels(rename_map)

    montage = mne.channels.read_custom_montage(montage_path)
    montage = match_montage_name_case(montage, raw.ch_names)
    raw.set_montage(montage, on_missing="warn")

    channel_types = {
        ch: ch_type
        for ch, ch_type in channel_config.get("channel_types", {}).items()
        if ch in raw.ch_names
    }
    if channel_types:
        raw.set_channel_types(channel_types)

    patch_fpz_location(raw)
    return raw


def match_montage_name_case(montage: mne.channels.DigMontage, raw_ch_names: list[str]) -> mne.channels.DigMontage:
    """Make montage channel-name case match the raw data where names differ only by case."""
    raw_by_lower = {ch.lower(): ch for ch in raw_ch_names}
    rename = {}
    for montage_ch in montage.ch_names:
        raw_ch = raw_by_lower.get(montage_ch.lower())
        if raw_ch and raw_ch != montage_ch:
            rename[montage_ch] = raw_ch

    if rename:
        montage = montage.copy()
        montage.rename_channels(rename)
    return montage


def patch_fpz_location(raw: mne.io.BaseRaw) -> None:
    fp1 = pick_channel_case_insensitive(raw.ch_names, "Fp1")
    fp2 = pick_channel_case_insensitive(raw.ch_names, "Fp2")
    fpz = pick_channel_case_insensitive(raw.ch_names, "FPz")
    if not (fp1 and fp2 and fpz):
        return

    fp1_loc = raw.info["chs"][raw.ch_names.index(fp1)]["loc"][:3]
    fp2_loc = raw.info["chs"][raw.ch_names.index(fp2)]["loc"][:3]
    if np.any(np.isnan(fp1_loc)) or np.any(np.isnan(fp2_loc)):
        return

    fpz_loc = (fp1_loc + fp2_loc) / 2
    raw.info["chs"][raw.ch_names.index(fpz)]["loc"][:3] = fpz_loc


def pick_channel_case_insensitive(ch_names: list[str], target: str) -> str | None:
    target_lower = target.lower()
    for ch_name in ch_names:
        if ch_name.lower() == target_lower:
            return ch_name
    return None
