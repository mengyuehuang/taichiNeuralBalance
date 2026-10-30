"""Audit the centered projection change against historical PCD inputs, read-only.

This measures input and pooled empirical covariance differences, not FC equivalence.
Historical source/FC outputs are never changed by this audit.
"""
import os
for key in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[key] = '2'
from pathlib import Path
import importlib.util, json, sys
ROOT = Path(__file__).resolve().parents[1]
os.environ['_MNE_FAKE_HOME_DIR'] = str(ROOT.parent/'.mne_fake_home')
os.environ['MNE_USE_NUMBA'] = 'false'
sys.path.insert(0, str(ROOT/'src'))
import numpy as np
from fc_pipeline_v2.signal_rank import signal_basis
from fc_pipeline_v2.cohort_policy import is_excluded


def main():
    run = ROOT/'extra_data_pipeline/rank_corrected'
    cfg = json.loads((run/'config.rank_corrected.json').read_text())
    spec = importlib.util.spec_from_file_location('source_step', ROOT/'scripts/02_source_localization_hc_blocks.py')
    source = importlib.util.module_from_spec(spec); spec.loader.exec_module(source)
    target = run/'projection_compatibility.json'
    result = {'status':'running','old_policy':'uncentered_projection','new_policy':'centered_preserve_mean_v2',
              'scope':'All samples, including annotated samples; empirical covariance diagnostic, not the fitted shrunk covariance or FC equivalence test',
              'participants':{}, 'fc_equivalence_verified':False}
    def save():
        tmp=target.with_suffix('.tmp'); tmp.write_text(json.dumps(result,indent=2),encoding='utf-8'); tmp.replace(target)
    save()
    try:
        for folder in sorted((run/'outputs').iterdir()):
            if not folder.is_dir() or is_excluded(folder.name): continue
            files=sorted((folder/'01_block_level_eeg/montage_aligned').glob('*.fif'))
            if not files: continue
            entry={'blocks':{}}; result['participants'][folder.name]=entry
            moments=[None,None]; totals=[None,None]; n=0; sampled=[[],[]]
            for path in files:
                raw=source.read_raw_block(path,cfg['source_localization']['exclude_channels'],True)
                x=raw.get_data(); basis,_=signal_basis(x)
                mean=x.mean(axis=1,keepdims=True)
                delta=mean-basis@(basis.T@mean)
                norm2=0.
                for start in range(0,x.shape[1],20000):
                    chunk=x[:,start:start+20000]; old=basis@(basis.T@chunk); new=old+delta
                    norm2+=float(np.sum(old*old))
                    for i,y in enumerate([old,new]):
                        gram=y@y.T; total=y.sum(axis=1)
                        moments[i]=gram if moments[i] is None else moments[i]+gram
                        totals[i]=total if totals[i] is None else totals[i]+total
                take=x[:,::max(1,x.shape[1]//3000)]
                old=basis@(basis.T@take)
                sampled[0].append(old); sampled[1].append(old+delta)
                entry['blocks'][path.name]={'rank':int(basis.shape[1]),'max_mean_difference_uv':float(np.max(abs(delta))*1e6),
                    'relative_input_difference':float(np.sqrt(x.shape[1]*np.sum(delta*delta)/norm2))}
                n+=x.shape[1]
                del raw,x
            cov=[(moments[i]-np.outer(totals[i],totals[i])/n)/(n-1) for i in range(2)]
            entry['pooled_empirical_covariance_relative_difference']=float(np.linalg.norm(cov[1]-cov[0])/np.linalg.norm(cov[0]))
            entry['pooled_rank_old_new']=[int(signal_basis(np.concatenate(s,axis=1),max_samples=sum(a.shape[1] for a in s))[0].shape[1]) for s in sampled]
            save(); print(folder.name,entry['pooled_empirical_covariance_relative_difference'],flush=True)
        result['status']='completed';save()
    except Exception as exc:
        result.update(status='failed',error=str(exc));save();raise


if __name__=='__main__':main()
