from __future__ import annotations

import numpy as np
from scipy.signal import butter, hilbert, sosfiltfilt


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


def symmetric_orthogonalize(parcels_by_time: np.ndarray) -> np.ndarray:
    """Symmetric orthogonalization using the closest orthogonal basis in least squares."""
    # Source leakage can make parcels look connected just because nearby source
    # estimates mix together. This step reduces shared zero-lag signal before
    # computing amplitude-envelope correlations.
    demeaned = parcels_by_time - parcels_by_time.mean(axis=1, keepdims=True)
    u, _, vt = np.linalg.svd(demeaned.T, full_matrices=False)
    orth = (u @ vt).T

    original_std = demeaned.std(axis=1, keepdims=True)
    orth_std = orth.std(axis=1, keepdims=True)
    orth_std[orth_std == 0] = 1.0
    return orth * (original_std / orth_std)


def amplitude_envelopes(parcels_by_time: np.ndarray) -> np.ndarray:
    analytic = hilbert(parcels_by_time, axis=1)
    return np.abs(analytic)


def correlation_matrix(parcels_by_time: np.ndarray, apply_absolute_value: bool = False) -> np.ndarray:
    corr = np.corrcoef(parcels_by_time)
    if apply_absolute_value:
        corr = np.abs(corr)
    np.fill_diagonal(corr, 1.0)
    return corr


def fisher_r_to_z(corr: np.ndarray) -> np.ndarray:
    clipped = np.clip(corr, -0.999999, 0.999999)
    z = np.arctanh(clipped)
    np.fill_diagonal(z, 0.0)
    return z


def compute_static_amplitude_connectivity(
    signed_parcels_by_time: np.ndarray,
    sfreq: float,
    band: tuple[float, float],
    filter_order: int,
    edge_trim_seconds: float,
    orthogonalization: str,
    apply_absolute_value: bool,
) -> tuple[np.ndarray, np.ndarray]:
    # For each band: filter signed parcel signals, trim filter edges, reduce
    # leakage, convert to amplitude envelopes, then correlate parcels.
    filtered = bandpass_filter(signed_parcels_by_time, sfreq, band[0], band[1], order=filter_order)
    filtered = trim_edges(filtered, sfreq, edge_trim_seconds)

    if orthogonalization == "symmetric":
        filtered = symmetric_orthogonalize(filtered)
    elif orthogonalization in {"none", "off"}:
        pass
    else:
        raise ValueError(f"Unsupported orthogonalization={orthogonalization!r}")

    envelopes = amplitude_envelopes(filtered)
    r = correlation_matrix(envelopes, apply_absolute_value=apply_absolute_value)
    z = fisher_r_to_z(r)
    return r, z
