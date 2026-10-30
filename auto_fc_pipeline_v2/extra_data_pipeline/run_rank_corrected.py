"""Recompute provided Clean BP source/FC with explicit rank and residual checks."""
from pathlib import Path
import csv,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2]
HOME=Path(__file__).resolve().parent
RUN=HOME/'rank_corrected'
os.environ.setdefault('_MNE_FAKE_HOME_DIR',str(ROOT/'.mne_fake_home'))
os.environ.setdefault('NUMBA_CACHE_DIR',str(ROOT/'.numba_cache'))
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
import numpy as np


def main():
    RUN.mkdir(exist_ok=True);(RUN/'logs').mkdir(exist_ok=True)
    cfg=json.loads((HOME/'config.clean_bp.json').read_text())
    cfg['paths']['corrected_output_root']=str(RUN/'outputs')
    cfg['source_localization'].update(rank_policy='data_relative',rank_relative_tolerance=1e-6,forward_reuse_root=str(HOME/'outputs'))
    config=RUN/'config.rank_corrected.json';config.write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    with (HOME/'input_manifest.csv').open() as handle:manifest=list(csv.DictReader(handle))
    sys.path.insert(0,str(ROOT/'auto_fc_pipeline_v2/src'))
    from fc_pipeline_v2.cohort_policy import is_excluded
    participants=sorted({r['participant'] for r in manifest if r['status']=='selected' and not is_excluded(r['participant'])})
    state_file=RUN/'run_status.json'
    states=json.loads(state_file.read_text()) if state_file.exists() else {}
    for participant in participants:
        if states.get(participant,{}).get('status')=='completed':continue
        started=time.time();entry={'status':'running','provided_ica_unchanged':True}
        states[participant]=entry;state_file.write_text(json.dumps(states,indent=2),encoding='utf-8')
        print(f'{participant}: rank-corrected source/FC',flush=True)
        try:
            log=RUN/'logs'/f'{participant}.log'
            with log.open('w',encoding='utf-8') as handle:
                result=subprocess.run([sys.executable,str(ROOT/'auto_fc_pipeline_v2/scripts/run_participant.py'),participant,'--config',str(config),'--start-at','1','--route','100'],cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT)
            if result.returncode:raise RuntimeError(f'v2 failed; see {log}')
            output=RUN/'outputs'/participant
            audit=json.loads((output/'02_source_model/signal_rank_audit.json').read_text())
            ranks={}
            for p in (output/'03_roi_timeseries').glob('*signed_rois14.npz'):
                hc=p.name.split('_')[1]
                input_rank=next(v['rank'] for k,v in audit.items() if isinstance(v,dict) and f'_{hc}_' in k)
                with np.load(p) as d:
                    x=d['signed_tc14'][:,::max(1,d['signed_tc14'].shape[1]//6000)].astype(float)
                    x-=x.mean(1,keepdims=True);s=np.linalg.svd(x,compute_uv=False)
                    rank=int((s>s[0]*1e-6).sum())
                if rank>input_rank:raise RuntimeError(f'{hc}: source rank {rank} exceeds input rank {input_rank}')
                ranks[hc]={'input_rank':input_rank,'source_roi_rank':rank}
            matrices=list((output/'04_static_fc/pairwise_100parcels').glob('*.npz'))
            if len(matrices)!=len(ranks)*3:raise RuntimeError('Missing FC matrices')
            for p in matrices:
                with np.load(p) as d:
                    a=d['fc100_signed']
                    if not np.isfinite(a).all() or not np.allclose(a,a.T,atol=1e-6) or not np.allclose(np.diag(a),1,atol=1e-6):raise RuntimeError(f'Invalid matrix: {p}')
            # The primary route runs only if every available block supports it.
            entry['fc14_status']='skipped_insufficient_signal_rank'
            if all(v['source_roi_rank']>=14 for v in ranks.values()):
                with log.open('a',encoding='utf-8') as handle:
                    result=subprocess.run([sys.executable,str(ROOT/'auto_fc_pipeline_v2/scripts/04_whole_recording_fc14.py'),'--config',str(config),'--subject',participant],cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT)
                entry['fc14_status']='completed' if result.returncode==0 else 'failed_band_specific_rank_or_qc'
            entry.update(status='completed',block_rank_checks=ranks,pairwise_matrix_count=len(matrices),elapsed_minutes=round((time.time()-started)/60,2))
            print(f'{participant}: completed and rank checks passed',flush=True)
        except Exception as error:
            entry.update(status='failed',error=str(error))
            print(f'{participant}: FAILED: {error}',flush=True)
        state_file.write_text(json.dumps(states,indent=2),encoding='utf-8')
        if entry['status']!='completed':
            raise SystemExit('Participant did not pass; remaining participants were not started')


if __name__=='__main__':main()
