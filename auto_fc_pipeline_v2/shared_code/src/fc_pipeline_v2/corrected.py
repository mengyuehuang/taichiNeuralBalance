"""Step0/0b mathematics adapted to continuous HC blocks."""
from itertools import combinations
import numpy as np
from scipy.signal import hilbert
from .connectivity import bandpass_filter, trim_edges, fisher_r_to_z, symmetric_orthogonalize

NETWORK_ORDER = ['Vis', 'SomMot', 'DorsAttn', 'SalVentAttn', 'Limbic', 'Cont', 'Default']


def continuous_segments(valid, boundaries):
    valid = np.asarray(valid, dtype=bool)
    boundaries = np.asarray(boundaries, dtype=bool)
    if valid.ndim != 1 or valid.shape != boundaries.shape:
        raise ValueError('Validity and boundary arrays must have the same 1D shape')
    starts = np.flatnonzero(valid & (np.r_[True, ~valid[:-1]] | boundaries))
    stops = np.flatnonzero(valid & np.r_[~valid[1:] | boundaries[1:], True]) + 1
    if not len(starts):
        raise ValueError('No clean samples remain')
    return starts, stops


def prepare_segments(X, starts, stops, sfreq, band=None, trim_seconds=0, order=4):
    if X.ndim != 2 or not np.isfinite(X).all():
        raise ValueError('Expected finite signed signals of shape (regions, samples)')
    parts = []
    for start, stop in zip(starts, stops, strict=True):
        if not 0 <= start < stop <= X.shape[1]:
            raise ValueError('Invalid segment range')
        part = X[:, start:stop].astype(float)
        # Rejected 1-second chunks can leave tiny clean islands at annotation
        # boundaries. They contain too little data for filtfilt/edge trimming
        # and should not invalidate the rest of an otherwise usable recording.
        trim_samples = int(round(trim_seconds * sfreq))
        min_samples = max(2, 2 * trim_samples + 32) if band is not None else 2
        if part.shape[1] < min_samples:
            continue
        if band is not None:
            part = bandpass_filter(part, sfreq, *band, order=order)
        part = trim_edges(part, sfreq, trim_seconds)
        if part.shape[1] < 2:
            continue
        parts.append(part)
    if not parts:
        raise ValueError('No continuous segments')
    return parts


def smooth_segments(parts, block):
    if block < 1:
        raise ValueError('Smoothing block must be positive')
    out = []
    for part in parts:
        n = part.shape[-1] // block * block
        if n < block:
            raise ValueError('Continuous segment shorter than smoothing block')
        out.append(part[..., :n].reshape(*part.shape[:-1], -1, block).mean(-1))
    return np.concatenate(out, axis=-1)


def standardize(X):
    # Correlation is invariant to amplitude units. An absolute epsilon rejects
    # valid small source-current envelopes, so normalize row scale first.
    X = np.asarray(X, dtype=float)
    scale = np.max(np.abs(X), axis=-1, keepdims=True)
    if not np.isfinite(X).all() or np.any(scale == 0):
        raise ValueError('Constant/invalid envelope; FC is undefined')
    scaled = X / scale
    centered = scaled - scaled.mean(-1, keepdims=True)
    sd = centered.std(-1, keepdims=True)
    if np.any(sd <= np.finfo(float).eps) or not np.isfinite(sd).all():
        raise ValueError('Constant/invalid envelope; FC is undefined')
    return centered / sd


def pairwise_fc(parts, block=1):
    # Hilbert separately within each segment. Pool envelopes over the full HC
    # recording, never average separate epoch correlations.
    mean = sum(p.sum(axis=1, keepdims=True) for p in parts) / sum(p.shape[1] for p in parts)
    analytic = [hilbert(p - mean, axis=1) for p in parts]
    seeds = standardize(smooth_segments([np.abs(z) for z in analytic], block))
    n = seeds.shape[0]
    C = np.zeros((n, n))
    for i in range(n):
        others = np.arange(n) != i
        envelopes = []
        for z in analytic:
            amplitude = np.abs(z[i])
            if np.any(amplitude == 0):
                raise ValueError('Zero analytic seed amplitude; pairwise correction undefined')
            orth = np.imag(z[others] * (z[i].conj() / amplitude))
            envelopes.append(np.abs(orth))
        targets = standardize(smooth_segments(envelopes, block))
        C[i, others] = targets @ seeds[i] / seeds.shape[1]
    C = (C + C.T) / 2
    np.fill_diagonal(C, 1)
    unc = np.corrcoef(seeds)
    return C, unc


def resample_envelopes(parts, sfreq, envelope_hz):
    from mne.filter import resample
    if not 0 < envelope_hz <= sfreq:
        raise ValueError('Envelope sampling rate must be positive and <= input rate')
    return np.concatenate([
        resample(p.astype(np.float64), down=sfreq / envelope_hz,
                 npad='auto', verbose=False) for p in parts
    ], axis=-1)


def symmetric_fc(parts, block=1, *, sfreq=None, envelope_hz=10):
    if not parts:
        raise ValueError('No continuous segments available for symmetric correction')
    X = np.concatenate(parts, axis=1)
    X -= X.mean(1, keepdims=True)
    singular = np.linalg.svd(X, compute_uv=False)
    rank = int(np.sum(singular > singular[0] * 1e-6))
    if rank < X.shape[0]:
        raise ValueError(f'Signal rank {rank} < {X.shape[0]} ROIs; symmetric correction invalid')
    orth = symmetric_orthogonalize(X)
    offsets = np.cumsum([0] + [p.shape[1] for p in parts])
    env = [np.abs(hilbert(orth[:, a:b], axis=1)) for a, b in zip(offsets[:-1], offsets[1:])]
    reduced = (smooth_segments(env, block) if sfreq is None
               else resample_envelopes(env, sfreq, envelope_hz))
    return np.corrcoef(standardize(reduced)), float(np.max(np.abs((np.corrcoef(orth) - np.eye(X.shape[0])))))


def network_features(matrix, networks):
    z = fisher_r_to_z(matrix)
    networks = np.asarray(networks)
    result = {}
    for net in NETWORK_ORDER:
        indices = np.flatnonzero(networks == net)
        edges = z[np.ix_(indices, indices)][np.triu_indices(len(indices), 1)]
        result[f'within__{net}'] = float(edges.mean())
    for a, b in combinations(NETWORK_ORDER, 2):
        result[f'between__{a}__{b}'] = float(z[np.ix_(networks == a, networks == b)].mean())
    return result
