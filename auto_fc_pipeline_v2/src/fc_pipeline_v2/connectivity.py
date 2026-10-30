from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfiltfilt


def bandpass_filter(
    parcels_by_time: np.ndarray,
    sfreq: float,
    low_hz: float,
    high_hz: float,
    order: int = 4,
) -> np.ndarray:
    nyquist = sfreq / 2.0
    if low_hz <= 0 or high_hz >= nyquist:
        raise ValueError(f"Invalid band {low_hz}-{high_hz} Hz for sfreq={sfreq}")

    sos = butter(order, [low_hz / nyquist, high_hz / nyquist], btype="bandpass", output="sos")
    return sosfiltfilt(sos, parcels_by_time, axis=1)


def trim_edges(parcels_by_time: np.ndarray, sfreq: float, trim_seconds: float) -> np.ndarray:
    trim_samples = int(round(trim_seconds * sfreq))
    if trim_samples <= 0:
        return parcels_by_time
    if parcels_by_time.shape[1] <= 2 * trim_samples:
        raise ValueError(
            f"Cannot trim {trim_seconds}s from each edge; only "
            f"{parcels_by_time.shape[1]} samples available."
        )
    return parcels_by_time[:, trim_samples:-trim_samples]


def symmetric_orthogonalize(
    parcels_by_time: np.ndarray,
    n_iter: int = 50,
    tol: float = 1e-6,
) -> np.ndarray:
    """Colclough symmetric orthogonalization, matching MNE-Connectivity."""
    # Source leakage can make parcels look connected just because nearby source
    # estimates mix together. This step reduces shared zero-lag signal before
    # computing amplitude-envelope correlations.
    demeaned = parcels_by_time - parcels_by_time.mean(axis=1, keepdims=True)
    singular = np.linalg.svd(demeaned, compute_uv=False)
    rank = int(np.sum(singular >= singular[0] * 1e-6))
    if rank < demeaned.shape[0]:
        raise ValueError("Signal rank is below ROI count; use pairwise correction for 100 parcels")

    # This is the Colclough et al. iterative least-squares algorithm used by
    # mne_connectivity.envelope.symmetric_orth. Keeping the small calculation
    # local avoids importing the full connectivity package for every FC run.
    n_signals = demeaned.shape[0]
    scales = np.ones(n_signals)
    last_error = np.inf
    power = np.linalg.norm(demeaned, "fro") ** 2 or 1.0
    result = None
    for _ in range(n_iter):
        u, _, vh = np.linalg.svd(demeaned.T * scales, full_matrices=False)
        orthogonal = vh.T @ u.T
        scales = np.einsum("ij,ij->i", demeaned, orthogonal)
        orthogonal *= scales[:, np.newaxis]
        result = orthogonal
        error = np.linalg.norm(demeaned - result, "fro") ** 2 / power
        delta = 0.0 if error == 0 else (last_error - error) / error
        if error == 0 or delta < tol:
            break
        last_error = error
    if result is None:
        raise RuntimeError("Symmetric orthogonalization did not run")
    return result


def fisher_r_to_z(corr: np.ndarray) -> np.ndarray:
    clipped = np.clip(corr, -0.999999, 0.999999)
    z = np.arctanh(clipped)
    np.fill_diagonal(z, 0.0)
    return z
