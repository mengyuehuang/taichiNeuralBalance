"""Validate inverse whitening against the numerical rank of provided Clean BP.

Reuse saved forward/covariance models; never modify provided files or ICA decisions.
Write isolated diagnostic results rather than overwrite existing analysis outputs.
"""
from pathlib import Path
import argparse,importlib.util,json,os
ROOT=Path(__file__).resolve().parents[2]
os.environ.setdefault('_MNE_FAKE_HOME_DIR',str(ROOT/'.mne_fake_home'))
os.environ.setdefault('NUMBA_CACHE_DIR',str(ROOT/'.numba_cache'))
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
import mne
import numpy as np


def sampled_rank(raw, max_samples=6000):
    data=raw.get_data()[:,::max(1,raw.n_times//max_samples)]
    data-=data.mean(axis=1,keepdims=True)
    singular=np.linalg.svd(data,compute_uv=False)
    return int(np.sum(singular>singular[0]*1e-6)),(singular/singular[0]).tolist()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subject',default='PCD107')
    parser.add_argument('--sample-block',help='Optional block for diagnostic inverse application, e.g. HC1; pooled rank still uses all blocks')
    args=parser.parse_args()
    home=Path(__file__).resolve().parent
    cfg=json.loads((home/'config.clean_bp.json').read_text())
    base=home/'outputs'/args.subject
    target=home/'validation'/args.subject;target.mkdir(parents=True,exist_ok=True)
    mne.set_log_level('ERROR')
    paths=sorted((base/'01_block_level_eeg/montage_aligned').glob('*.fif'))
    raws=[];block_ranks={}
    for path in paths:
        raw=mne.io.read_raw_fif(path,preload=True,verbose='ERROR')
        raw.pick('eeg');raw.set_eeg_reference('average',projection=True,verbose='ERROR');raw.apply_proj(verbose='ERROR')
        rank,spectrum=sampled_rank(raw)
        block_ranks[path.name]={'rank':rank,'relative_singular_values':spectrum}
        raws.append(raw)
    # The common inverse uses the rank of the pooled participant signals, not
    # the minimum retained-component count of independently cleaned HC blocks.
    pooled=np.concatenate([r.get_data()[:,::max(1,r.n_times//3000)] for r in raws],axis=1)
    pooled-=pooled.mean(1,keepdims=True)
    sv=np.linalg.svd(pooled,compute_uv=False)
    rank=int(np.sum(sv>sv[0]*1e-6))
    old=mne.minimum_norm.read_inverse_operator(base/'02_source_model'/f'{args.subject}_common_inverse_operator.fif',verbose='ERROR')
    fwd=mne.read_forward_solution(base/'02_source_model'/f'{args.subject}_forwardsolution_fsaverage.fif',verbose='ERROR')
    print(f'{args.subject}: pooled rank={rank}; building diagnostic inverse',flush=True)
    fixed=mne.minimum_norm.make_inverse_operator(raws[0].info,fwd,old['noise_cov'],loose=.2,depth=.8,rank={'eeg':rank},verbose='ERROR')
    spec=importlib.util.spec_from_file_location('roi_extraction',ROOT/'auto_fc_pipeline_v2/scripts/03_extract_14roi_timeseries.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    rois=mod.build_network_rois(mne,Path(cfg['paths']['subjects_dir']),cfg['parcel_extraction']['parc'])
    comparisons=[]
    for raw,path in zip(raws,paths):
        if args.sample_block and f'_{args.sample_block}_' not in path.name: continue
        per={}
        sample=raw.copy().crop(tmax=(min(3000,raw.n_times)-1)/raw.info['sfreq'])
        data=raw.get_data()[:,::max(1,raw.n_times//6000)]
        data-=data.mean(1,keepdims=True)
        u,s,_=np.linalg.svd(data,full_matrices=False)
        k=int((s>s[0]*1e-6).sum());basis=u[:,:k]
        projected=sample.copy()
        projected._data=basis@(basis.T@sample.get_data())
        per['diagnostic_projection_relative_change']=float(np.linalg.norm(projected._data-sample._data)/np.linalg.norm(sample._data))
        for name,inverse,current in [('original',old,sample),('rank_aware',fixed,sample),('rank_aware_projected',fixed,projected)]:
            stc=mne.minimum_norm.apply_inverse_raw(current,inverse,lambda2=1/9,method='eLORETA',pick_ori='normal',start=0,stop=current.n_times,verbose='ERROR')
            tc=mne.extract_label_time_course(stc,rois,inverse['src'],mode='mean_flip',verbose='ERROR')
            tc-=tc.mean(1,keepdims=True);s=np.linalg.svd(tc,compute_uv=False)
            per[name]={'source_rms':float(np.sqrt(np.mean(tc**2))),'sampled_roi_rank':int((s>s[0]*1e-6).sum())}
            np.savez_compressed(target/f'{path.stem}_{name}_sample.npz',signed_tc14=tc,sfreq=raw.info['sfreq'])
        per['file']=path.name;comparisons.append(per)
        print(json.dumps(per),flush=True)
    report={'subject':args.subject,'pooled_data_rank':rank,'block_data_ranks':block_ranks,'sample_comparisons':comparisons,'note':'Only diagnostic samples were recomputed. No provided ICA decisions or existing results changed. Rank-aware source samples are not full FC validation.'}
    (target/'rank_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    for raw in raws:raw.close()

if __name__=='__main__':main()
