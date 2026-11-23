import unittest
import numpy as np
from fc_pipeline_v2.qc_validation import split_parts,pairwise_split_fc,double_center,prepare_qc_segments
from fc_pipeline_v2.corrected import pairwise_fc


class QCTests(unittest.TestCase):
    def test_full_fc_does_not_inherit_half_boundary(self):
        rng=np.random.default_rng(12);x=rng.normal(size=(5,2053))
        x[:,1026:]+=np.arange(5)[:,None]*4
        actual,_=pairwise_split_fc([x],16)
        expected,_=pairwise_fc([x],16)
        np.testing.assert_allclose(actual[0],expected,atol=1e-12)

    def test_preparation_retains_short_native_segment_and_envelope_interval(self):
        rng=np.random.default_rng(13);x=rng.normal(size=(3,10000))
        parts,rate,block=prepare_qc_segments(x,[0,2500],[2500,10000],500)
        self.assertEqual(len(parts),2)
        self.assertAlmostEqual(rate/block,500/62)
        self.assertGreaterEqual(rate,256)

    def test_split_preserves_order_and_boundaries(self):
        x=np.arange(30).reshape(3,10)
        a,b=split_parts([x[:,:3],x[:,3:]])
        np.testing.assert_array_equal(np.concatenate(a,axis=1),x[:,:5])
        np.testing.assert_array_equal(np.concatenate(b,axis=1),x[:,5:])

    def test_independent_halves_match_reference(self):
        rng=np.random.default_rng(5);x=rng.normal(size=(5,2048))
        matrices,_=pairwise_split_fc([x],16)
        for actual,half in zip(matrices[1:],[x[:,:1024],x[:,1024:]]):
            expected,_=pairwise_fc([half],16)
            np.testing.assert_allclose(actual,expected,atol=1e-12)

    def test_reference_double_center_is_offset_invariant(self):
        rng=np.random.default_rng(3);x=rng.normal(size=(10,10));x=(x+x.T)/2
        np.testing.assert_allclose(double_center(x),double_center(x+3),atol=1e-12,equal_nan=True)
