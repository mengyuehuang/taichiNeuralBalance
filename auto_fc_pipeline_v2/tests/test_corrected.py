import sys
import unittest
import runpy
from unittest.mock import patch
from pathlib import Path
import numpy as np
from scipy.signal import hilbert
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from fc_pipeline_v2.corrected import continuous_segments, pairwise_fc, network_features, NETWORK_ORDER
from fc_pipeline_v2.connectivity import symmetric_orthogonalize


class ReviewInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[2]
        cls.review = runpy.run_path(str(root / 'auto_fc_pipeline_v1/scripts/04_run_ica.py'))
        cls.runner = runpy.run_path(str(root / 'auto_fc_pipeline_v2/scripts/run_participant.py'))

    def test_v1_relative_output_matches_v1_loader(self):
        config = Path(__file__).resolve().parents[2] / 'auto_fc_pipeline_v1/config.local.json'
        actual = self.runner['v1_output_path'](config, {'paths': {'output_dir': 'outputs/example'}})
        self.assertEqual(actual, config.parent / 'outputs/example')

    def test_review_boolean_normalization_and_invalid_value(self):
        import pandas as pd
        table = pd.DataFrame({'component': [0, 1, 2, 3],
                              'review_exclude1': [' TRUE ', 1.0, '', False]})
        self.assertEqual(self.review['exclusions_from_review'](table), [0, 1])
        table.loc[2, 'review_exclude1'] = 'maybe'
        with self.assertRaisesRegex(ValueError, 'Invalid'):
            self.review['exclusions_from_review'](table)

    def test_component_ids_match_saved_model(self):
        import pandas as pd
        with self.assertRaisesRegex(ValueError, 'component IDs'):
            self.review['check_component_ids'](pd.DataFrame({'component': [0, 0]}), 2)

    def test_unsynchronized_workbook_is_not_overwritten(self):
        import pandas as pd
        table = self.review['build_review_table'](['brain'], [0.9], {})
        changed = table.copy()
        changed.loc[0, 'reviewer1_note'] = 'new human decision'
        with patch('pandas.read_csv', return_value=table), patch('pandas.read_excel', return_value=changed), patch.object(Path, 'exists', return_value=True):
            with self.assertRaisesRegex(ValueError, 'XLSX/CSV'):
                self.review['read_review_table'](Path('review.csv'))

    def test_ica_psd_does_not_join_bad_intervals(self):
        trace = np.r_[np.zeros(250), np.full(10, np.nan), np.full(250, 100.)]
        _, psd = self.review['segment_psd'](trace, 100, np.zeros(len(trace), dtype=bool))
        np.testing.assert_allclose(psd, 0, atol=1e-12)

    def test_ica_psd_respects_zero_duration_boundary(self):
        trace = np.r_[np.zeros(250), np.full(250, 100.)]
        boundary = np.zeros(500, dtype=bool)
        boundary[250] = True
        _, psd = self.review['segment_psd'](trace, 100, boundary)
        np.testing.assert_allclose(psd, 0, atol=1e-12)


class CorrectedTests(unittest.TestCase):
    def test_bad_interval_and_zero_duration_boundary(self):
        starts, stops = continuous_segments([1, 1, 0, 0, 1, 1, 1], [1, 0, 0, 0, 0, 1, 0])
        np.testing.assert_array_equal(starts, [0, 4, 5])
        np.testing.assert_array_equal(stops, [2, 5, 7])

    def test_pairwise_signed_correlations_and_segments(self):
        rng = np.random.default_rng(42)
        parts = [rng.normal(size=(5, 400)), rng.normal(size=(5, 600))]
        result, _ = pairwise_fc(parts)
        mean = np.concatenate(parts, axis=1).mean(1, keepdims=True)
        analytic = np.concatenate([hilbert(p - mean, axis=1) for p in parts], axis=1)
        expected = np.eye(5)
        for i in range(5):
            for j in range(i):
                x, y = analytic[i], analytic[j]
                a = np.corrcoef(np.abs(x), np.abs(np.imag(y * x.conj() / np.abs(x))))[0, 1]
                b = np.corrcoef(np.abs(y), np.abs(np.imag(x * y.conj() / np.abs(y))))[0, 1]
                expected[i, j] = expected[j, i] = (a + b) / 2
        np.testing.assert_allclose(result, expected, atol=1e-12)
        self.assertTrue((result[np.triu_indices(5, 1)] < 0).any())

    def test_rank_deficient_symmetric_rejected(self):
        rng = np.random.default_rng(1)
        low_rank = rng.normal(size=(100, 10)) @ rng.normal(size=(10, 1000))
        with self.assertRaisesRegex(ValueError, 'rank'):
            symmetric_orthogonalize(low_rank)

    def test_pairwise_100_accepts_lower_rank(self):
        rng = np.random.default_rng(9)
        signals = rng.normal(size=(100, 20)) @ rng.normal(size=(20, 2000))
        matrix, unc = pairwise_fc([signals[:, :1000], signals[:, 1000:]], block=10)
        self.assertEqual(matrix.shape, (100, 100))
        self.assertTrue(np.isfinite(matrix).all())
        np.testing.assert_allclose(matrix, matrix.T, atol=1e-12)
        np.testing.assert_allclose(np.diag(matrix), 1)

    def test_network_features_exclude_diagonal_and_pool_hemispheres(self):
        matrix = np.full((14, 14), .2)
        np.fill_diagonal(matrix, 1)
        features = network_features(matrix, NETWORK_ORDER * 2)
        self.assertEqual(len(features), 28)
        np.testing.assert_allclose(list(features.values()), np.arctanh(.2))


if __name__ == '__main__':
    unittest.main()
