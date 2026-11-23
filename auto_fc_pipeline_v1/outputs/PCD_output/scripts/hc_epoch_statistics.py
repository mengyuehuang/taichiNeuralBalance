"""HC epoch scoring from EEGLAB 2020.0 jointprob, realproba and rejkurt."""

import numpy as np
from scipy.stats import kurtosis


def sample_surprisal(values):
    """Negative log empirical probability, using EEGLAB's 1000 discrete bins."""
    low = values.min()
    span = values.max() - low
    if span == 0 or not np.isfinite(span):
        raise ValueError("Undefined probability bins: check flat channels or nonfinite data.")
    bins = np.floor((values - low) / span * 999).astype(np.intp)
    counts = np.bincount(bins.ravel(), minlength=1000)
    return -np.log(counts[bins] / values.size)


def epoch_z(scores):
    # MATLAB std uses the sample standard deviation across complete epochs.
    with np.errstate(invalid="ignore", divide="ignore"):
        return (scores - scores.mean(axis=-1, keepdims=True)) / scores.std(
            axis=-1, ddof=1, keepdims=True)


def epoch_statistics(voltage, sf, local):
    """Return local (channel x epoch) and global (epoch) standardized scores."""
    count = voltage.shape[1] // sf
    if count < 2:
        raise ValueError("Need at least two complete one-second epochs.")
    epochs = voltage[:, :count * sf].reshape(len(voltage), count, sf)
    jp_local = []
    kurt_local = []
    for channel in local:
        signal = epochs[channel]
        jp_local.append(sample_surprisal(signal).sum(axis=1))
        kurt_local.append(kurtosis(signal, axis=1, fisher=False, bias=True))

    # pop_jointprob reshapes to epochs x (channels * samples). Each epoch
    # has its own global histogram; local histograms span the whole channel.
    jp_global = []
    kurt_global = []
    for epoch in epochs.transpose(1, 0, 2):
        jp_global.append(sample_surprisal(epoch).sum())
        kurt_global.append(kurtosis(epoch, axis=None, fisher=False, bias=True))
    return tuple(epoch_z(np.asarray(score)) for score in
                 (jp_local, kurt_local, jp_global, kurt_global))
