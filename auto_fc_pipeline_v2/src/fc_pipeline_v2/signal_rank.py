"""Remove storage-rounding null-space residue without changing ICA decisions."""
import numpy as np


def signal_basis(data, relative_tolerance=1e-6, max_samples=6000):
    if not 0 < relative_tolerance < 1:
        raise ValueError('Rank tolerance must be between zero and one')
    x=np.asarray(data,dtype=float)
    if x.ndim!=2 or not np.isfinite(x).all():
        raise ValueError('Expected finite channel-by-time data')
    sample=x[:,::max(1,x.shape[1]//max_samples)].copy()
    sample-=sample.mean(1,keepdims=True)
    u,s,_=np.linalg.svd(sample,full_matrices=False)
    if s[0]==0:raise ValueError('No varying signal')
    rank=int(np.sum(s>s[0]*relative_tolerance))
    return u[:,:rank],s/s[0]


def project_numerical_residue(raw, relative_tolerance=1e-6):
    basis,spectrum=signal_basis(raw.get_data(),relative_tolerance)
    # signal_basis estimates rank after centering. Apply that projection to
    # centered samples too, preserving the channel-wise DC offset. Projecting
    # uncentered samples can remove a valid mean outside the varying subspace.
    mean=raw.get_data().mean(axis=1,keepdims=True)
    before=0.;discarded=0.;varying=0.
    for start in range(0,raw.n_times,20000):
        end=min(start+20000,raw.n_times)
        x=raw._data[:,start:end]
        centered=x-mean
        y=basis@(basis.T@centered)+mean
        before+=float(np.sum(x*x));discarded+=float(np.sum((x-y)**2))
        varying+=float(np.sum(centered*centered))
        raw._data[:,start:end]=y
    change=float(np.sqrt(discarded/before))
    varying_change=float(np.sqrt(discarded/varying))
    if max(change,varying_change)>1e-5:
        raise ValueError(f'Rank projection changed {change:.3g} of signal norm / {varying_change:.3g} of varying signal norm; review before continuing')
    return {'rank':basis.shape[1],'relative_change':change,'varying_relative_change':varying_change,'projection_policy':'centered_preserve_mean_v2','relative_singular_values':spectrum.tolist()}
