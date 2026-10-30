import unittest
import numpy as np
from fc_pipeline_v2.signal_rank import signal_basis,project_numerical_residue


class SignalRankTests(unittest.TestCase):
    def test_projection_preserves_mean_outside_varying_subspace(self):
        import mne
        rng=np.random.default_rng(19)
        x=np.zeros((8,4000));x[:3]=rng.normal(size=(3,4000))*1e-6
        x-=x.mean(axis=1,keepdims=True)
        x[7]=5e-6
        raw=mne.io.RawArray(x.copy(),mne.create_info(8,1000,'eeg'),verbose=False)
        audit=project_numerical_residue(raw)
        self.assertEqual(audit['rank'],3)
        np.testing.assert_allclose(raw.get_data(),x,atol=1e-18)
        self.assertLess(audit['varying_relative_change'],1e-12)

    def test_float32_storage_residue_is_not_extra_signal(self):
        rng=np.random.default_rng(8)
        x=((rng.normal(size=(20,5))@rng.normal(size=(5,4000)))*1e-6).astype('float32').astype(float)
        basis,_=signal_basis(x)
        self.assertEqual(basis.shape[1],5)
        self.assertLess(np.linalg.norm(x-basis@(basis.T@x))/np.linalg.norm(x),1e-6)

    def test_full_rank_signal_preserved(self):
        rng=np.random.default_rng(8);x=rng.normal(size=(20,4000))
        basis,_=signal_basis(x)
        self.assertEqual(basis.shape[1],20)
        np.testing.assert_allclose(basis@(basis.T@x),x,atol=1e-12)

    def test_pooled_rank_not_minimum_block_rank(self):
        rng=np.random.default_rng(8)
        a=np.zeros((10,1000));b=a.copy()
        a[:3]=rng.normal(size=(3,1000));b[3:7]=rng.normal(size=(4,1000))
        self.assertEqual(signal_basis(np.concatenate([a,b],axis=1))[0].shape[1],7)

    def test_rank_independent_of_physical_units(self):
        rng=np.random.default_rng(18)
        x=rng.normal(size=(20,5))@rng.normal(size=(5,4000))
        for scale in [1.,1e-6,1e-18]:
            self.assertEqual(signal_basis(x*scale)[0].shape[1],5)

    def test_invalid_inputs_fail(self):
        for data in [np.zeros((4,100)),np.full((4,100),np.nan)]:
            with self.assertRaises(ValueError):signal_basis(data)
