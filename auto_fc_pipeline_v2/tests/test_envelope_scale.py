import unittest
import numpy as np
from fc_pipeline_v2.corrected import standardize, pairwise_fc


class EnvelopeScaleTests(unittest.TestCase):
    def test_small_source_units_preserve_standardization(self):
        x = np.random.default_rng(9).uniform(0.1, 2, (4, 500))
        np.testing.assert_allclose(standardize(x), standardize(x * 1e-18), atol=1e-13)

    def test_pairwise_correlation_preserves_source_units(self):
        x = np.random.default_rng(9).normal(size=(4, 1000))
        a, _ = pairwise_fc([x], 10)
        b, _ = pairwise_fc([x * 1e-18], 10)
        np.testing.assert_allclose(a, b, atol=1e-12)

    def test_constant_and_nonfinite_envelopes_fail(self):
        for x in (np.ones((2, 100)), np.zeros((2, 100)), np.full((2,100),np.nan)):
            with self.assertRaises(ValueError):
                standardize(x)
