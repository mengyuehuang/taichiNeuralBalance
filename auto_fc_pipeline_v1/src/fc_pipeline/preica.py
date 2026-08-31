from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import mne
import numpy as np
import pandas as pd
from scipy.stats import kurtosis, zscore


@dataclass
class ChunkQcResult:
    annotations: mne.Annotations
    report: pd.DataFrame


def annotate_noisy_fixed_chunks(
    raw: mne.io.BaseRaw,
    qc_config: dict[str, Any],
) -> ChunkQcResult:
    """Mark Yang-style 1-second noisy chunks without silently concatenating data.

    Yang's MATLAB script creates fixed 1-second events so EEGLAB can reject noisy
    epochs before ICA. In Python we keep the Raw object continuous and add BAD
    annotations for suspicious chunks. MNE's ICA fitting can then skip those
    annotated spans with reject_by_annotation=True.
    """
    chunk_len = float(qc_config.get("chunk_length_seconds", 1.0))
    threshold = float(qc_config.get("zscore_threshold", 6.0))
    description = str(qc_config.get("annotation_description", "BAD_preICA_auto"))

    picks = _qc_picks(raw, qc_config)
    if len(picks) == 0:
        raise ValueError("No channels were selected for pre-ICA chunk QC.")

    starts = np.arange(0.0, raw.times[-1], chunk_len)
    rows: list[dict[str, float | int | bool]] = []

    # First pass: compute robust-ish window metrics over the requested channels.
    for chunk_idx, onset in enumerate(starts):
        stop = min(onset + chunk_len, raw.times[-1])
        if stop <= onset:
            continue

        start_sample = raw.time_as_index(onset)[0]
        stop_sample = raw.time_as_index(stop)[0]
        data = raw.get_data(picks=picks, start=start_sample, stop=stop_sample)
        if data.size == 0:
            continue

        peak_to_peak = float(np.nanmax(data) - np.nanmin(data))
        abs_mean = float(np.nanmean(np.abs(data)))
        kurt = float(np.nanmean(kurtosis(data, axis=1, fisher=True, nan_policy="omit")))
        rows.append(
            {
                "chunk_index": chunk_idx,
                "onset_seconds": float(onset),
                "duration_seconds": float(stop - onset),
                "peak_to_peak": peak_to_peak,
                "abs_mean": abs_mean,
                "kurtosis": kurt,
            }
        )

    report = pd.DataFrame(rows)
    if report.empty:
        return ChunkQcResult(mne.Annotations([], [], []), report)

    metric_cols = ["peak_to_peak", "abs_mean", "kurtosis"]
    zscores = np.abs(report[metric_cols].apply(_safe_zscore))
    report["max_abs_zscore"] = zscores.max(axis=1)
    report["auto_reject"] = report["max_abs_zscore"] >= threshold

    bad_rows = report[report["auto_reject"]]
    annotations = mne.Annotations(
        onset=bad_rows["onset_seconds"].to_numpy(),
        duration=bad_rows["duration_seconds"].to_numpy(),
        description=[description] * len(bad_rows),
        orig_time=raw.annotations.orig_time,
    )
    return ChunkQcResult(annotations, report)


def _qc_picks(raw: mne.io.BaseRaw, qc_config: dict[str, Any]) -> list[int]:
    names = [name for name in qc_config.get("reject_channel_names", []) if name in raw.ch_names]
    if names:
        return list(mne.pick_channels(raw.ch_names, include=names))

    one_based = qc_config.get("reject_channel_indices_1based_after_loading", [])
    if one_based:
        return [
            int(idx) - 1
            for idx in one_based
            if 0 <= int(idx) - 1 < len(raw.ch_names)
        ]

    return list(mne.pick_types(raw.info, eeg=True, eog=False, emg=False, misc=False))


def _safe_zscore(values: pd.Series) -> np.ndarray:
    arr = values.to_numpy(dtype=float)
    if np.allclose(arr, arr[0], equal_nan=True):
        return np.zeros_like(arr)
    return np.nan_to_num(zscore(arr, nan_policy="omit"))
