"""Run with the project environment's mne-connectivity dependency installed."""
import unittest
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from fc_pipeline_v2.corrected import pairwise_fc, symmetric_fc


class MNEReferenceTests(unittest.TestCase):
    def test_step0_resampling_and_correlation(self):
        from mne.filter import resample
        from scipy.signal import hilbert
        from fc_pipeline_v2.connectivity import symmetric_orthogonalize
        rng = np.random.default_rng(72)
        X = rng.normal(size=(14, 5100))
        parts = [X[:, :2100], X[:, 2100:]]
        actual, _ = symmetric_fc(parts, sfreq=1000, envelope_hz=10)
        centered = X - X.mean(axis=1, keepdims=True)
        orth = symmetric_orthogonalize(centered)
        env = [np.abs(hilbert(orth[:, a:b], axis=1))
               for a, b in [(0, 2100), (2100, 5100)]]
        reference = np.corrcoef(np.concatenate([
            resample(e, down=100, npad='auto', verbose=False) for e in env
        ], axis=1))
        np.testing.assert_allclose(actual, reference, atol=1e-12)

    def test_pairwise_against_mne(self):
        from mne_connectivity import envelope_correlation
        rng = np.random.default_rng(21)
        X = rng.normal(size=(7, 4000))
        X -= X.mean(1, keepdims=True)
        result, _ = pairwise_fc([X])
        reference = envelope_correlation(X[np.newaxis], orthogonalize='pairwise',
                                         absolute=False, log=False).get_data(output='dense')[0, :, :, 0]
        np.fill_diagonal(reference, 1)
        np.testing.assert_allclose(result, reference, atol=1e-12)

    def test_symmetric_signal_before_envelope(self):
        rng = np.random.default_rng(11)
        X = rng.normal(size=(14, 5000))
        X[1] += .6 * X[0]
        fc, residual = symmetric_fc([X[:, :2000], X[:, 2000:]], block=10)
        self.assertLess(residual, 1e-6)
        self.assertTrue(np.isfinite(fc).all())
        np.testing.assert_allclose(fc, fc.T, atol=1e-12)
        np.testing.assert_allclose(np.diag(fc), 1)


if __name__ == '__main__':
    unittest.main()
