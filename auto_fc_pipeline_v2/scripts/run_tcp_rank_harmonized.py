"""Reuse the corrected PCD v2 implementation for TCP, then process reviewed 404.

Writes only outputs/tcp_rank_harmonized. Does not refit ICA or replace legacy FC.
Default is preparation/rank preflight; --run continues to numerical processing.
"""
import os
for key in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[key] = '2'
from pathlib import Path
import argparse, hashlib, importlib.util, json, subprocess, sys, time
ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
RUN = ROOT / 'outputs/tcp_rank_harmonized'
os.environ['_MNE_FAKE_HOME_DIR'] = str(PROJECT / '.mne_fake_home')
os.environ['MNE_USE_NUMBA'] = 'false'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
from fc_pipeline_v2.signal_rank import project_numerical_residue, signal_basis


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temp.replace(path)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def command(script, subject, log, *extra):
    subprocess.run([sys.executable, '-u', str(ROOT/'scripts'/script),
                    '--config', str(RUN/'config.tcp.json'), '--subject', subject, *extra],
                   cwd=PROJECT, stdout=log, stderr=subprocess.STDOUT, check=True)


def preflight(subject, cfg, log):
    command('01_prepare_blocks.py', subject, log)
    command('02_check_montage_and_channels.py', subject, log)
    spec = importlib.util.spec_from_file_location('source_step', ROOT/'scripts/02_source_localization_hc_blocks.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    files = sorted((RUN/'outputs'/subject/'01_block_level_eeg/montage_aligned').glob('*.fif'))
    if len(files) != 4: raise ValueError(f'{subject}: expected four HC blocks, found {len(files)}')
    audits = {}; samples = []; signature = None
    for path in files:
        raw = mod.read_raw_block(path, cfg['source_localization']['exclude_channels'], True)
        current = (raw.ch_names, raw.info['sfreq'], raw.info['bads'])
        if signature is not None and current != signature: raise ValueError('HC channel/reference compatibility mismatch')
        signature = current
        original = raw.get_data()[:, ::max(1,raw.n_times//6000)].copy()
        audit = project_numerical_residue(raw, 1e-6)
        audit['rank_tolerance_sensitivity'] = {str(t): signal_basis(original,t)[0].shape[1] for t in [1e-5,1e-6,1e-7]}
        audit['sfreq'] = raw.info['sfreq']; audit['n_channels'] = len(raw.ch_names)
        audits[path.name] = audit
        samples.append(raw.get_data()[:, ::max(1,raw.n_times//3000)].copy())
    pooled = np.concatenate(samples,axis=1)
    audits['pooled_rank'] = signal_basis(pooled,1e-6,max_samples=pooled.shape[1])[0].shape[1]
    save(RUN/'logs'/f'{subject}_preflight.json',audits)
    return audits


def verify(subject):
    folder = RUN/'outputs'/subject
    audit = json.loads((folder/'02_source_model/signal_rank_audit.json').read_text())
    ranks = {}
    for path in sorted((folder/'03_roi_timeseries').glob('*signed_rois14.npz')):
        hc = path.name.split('_')[1]
        incoming = next(v['rank'] for k,v in audit.items() if isinstance(v,dict) and f'_{hc}_' in k)
        with np.load(path) as d:
            measured = signal_basis(d['signed_tc14'])[0].shape[1]
        if measured > incoming: raise ValueError(f'{subject}/{hc}: source rank exceeds input rank')
        ranks[hc] = {'input_rank':incoming,'source_roi_rank':measured}
    if set(ranks) != {'HC1','HC2','HC3','HC4'}: raise ValueError('Missing signed ROI blocks')
    paths = sorted((folder/'04_static_fc/pairwise_100parcels').glob('*.npz'))
    if len(paths) != 12: raise ValueError('Expected twelve pairwise matrices')
    for path in paths:
        with np.load(path) as d:
            a=d['fc100_signed']
            if a.shape!=(100,100) or not np.isfinite(a).all() or not np.allclose(a,a.T,atol=1e-6) or not np.allclose(np.diag(a),1,atol=1e-6) or np.max(abs(a))>1+1e-6:
                raise ValueError(f'Invalid matrix: {path}')
    return ranks


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');args=parser.parse_args()
    RUN.mkdir(parents=True,exist_ok=True);(RUN/'logs').mkdir(exist_ok=True)
    lock=RUN/'runner.lock'
    try: fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError: raise SystemExit('Runner lock exists; check active process before resuming')
    os.write(fd,str(os.getpid()).encode());os.close(fd)
    state={'status':'preflight','pid':os.getpid(),'participants':{},'order':[]}
    status_path=RUN/'run_status.json'
    if status_path.exists(): state=json.loads(status_path.read_text());state['pid']=os.getpid()
    state.pop('error',None)
    try:
        tracked = [ROOT/'src/fc_pipeline_v2/signal_rank.py', ROOT/'scripts/02_source_localization_hc_blocks.py', ROOT/'scripts/03_extract_14roi_timeseries.py', ROOT/'scripts/04_whole_recording_fc.py', ROOT/'scripts/04_whole_recording_fc14.py', ROOT/'src/fc_pipeline_v2/corrected.py']
        fingerprints = {str(p.relative_to(ROOT)): digest(p) for p in tracked}
        if state.get('code_sha256') not in [None, fingerprints]:
            raise ValueError('Numerical code changed; inspect before resuming this output version')
        state['code_sha256'] = fingerprints
        state['projection_policy'] = 'centered_preserve_mean_v2'
        pcd=json.loads((ROOT/'extra_data_pipeline/rank_corrected/config.rank_corrected.json').read_text())
        tcp=json.loads((ROOT/'config.hc_corrected.example.json').read_text())
        cfg=json.loads(json.dumps(pcd))
        cfg['paths']['backprojected_dir']=str(PROJECT/'auto_fc_pipeline_v1/outputs/v1_preica_test/Backprojected')
        cfg['paths']['corrected_output_root']=str(RUN/'outputs')
        cfg['inputs']=tcp['inputs'];cfg['naming']=tcp['naming'];cfg['groups']=tcp['groups']
        cfg['source_localization']['forward_reuse_root']=str(ROOT/'outputs/corrected')
        target=RUN/'config.tcp.json'
        if target.exists() and json.loads(target.read_text())!=cfg: raise ValueError('Configuration changed; use a new output version')
        save(target,cfg)
        subjects=sorted(p.name for p in (ROOT/'outputs/corrected').iterdir() if p.is_dir() and list((p/'04_static_fc/pairwise_100parcels').glob('*.npz')))
        if len(subjects)!=17 or '404' in subjects: raise ValueError('Unexpected legacy cohort; inspect before continuing')
        state['order']=subjects+['404'];save(status_path,state)
        for subject in subjects:
            entry=state['participants'].setdefault(subject,{})
            sources=sorted(Path(cfg['paths']['backprojected_dir']).glob(f'{subject}_HC[1-4]_backproject_raw.fif'))
            if len(sources)!=4: raise ValueError(f'{subject}: missing BP')
            hashes={str(p):digest(p) for p in sources}
            if entry.get('input_sha256') not in [None,hashes]: raise ValueError(f'{subject}: BP changed; new output version required')
            entry['input_sha256']=hashes
            if entry.get('status') in ['preflight_passed','completed']:continue
            state.update(status='preflight',current_subject=subject);entry['status']='preflight';save(status_path,state)
            with (RUN/'logs'/f'{subject}_preflight.log').open('w',encoding='utf-8') as log:
                audit=preflight(subject,cfg,log)
            entry.update(status='preflight_passed',pooled_rank=audit['pooled_rank']);save(status_path,state)
            print(subject,'preflight passed; pooled rank',audit['pooled_rank'],flush=True)
        state['status']='preflight_completed';save(status_path,state)
        if not args.run:return
        for subject in subjects+['404']:
            entry=state['participants'].setdefault(subject,{})
            if entry.get('status')=='completed':continue
            if subject=='404':
                if not all(state['participants'][s].get('status')=='completed' for s in subjects):raise ValueError('404 requires all 17 harmonized TCP subjects to pass')
                state.update(status='preflight_404',current_subject=subject);save(status_path,state)
                with (RUN/'logs'/'404_preflight.log').open('w',encoding='utf-8') as log:preflight(subject,cfg,log)
                entry['input_sha256']={str(p):digest(p) for p in Path(cfg['paths']['backprojected_dir']).glob('404_HC[1-4]_backproject_raw.fif')}
            state.update(status='running',current_subject=subject);entry['status']='running';save(status_path,state)
            started=time.time()
            with (RUN/'logs'/f'{subject}.log').open('a',encoding='utf-8') as log:
                subprocess.run([sys.executable,'-u',str(ROOT/'scripts/run_participant.py'),subject,'--config',str(target),'--start-at','3','--route','100'],cwd=PROJECT,stdout=log,stderr=subprocess.STDOUT,check=True)
                ranks=verify(subject)
                entry['fc14_status']='skipped_insufficient_signal_rank'
                if all(v['source_roi_rank']>=14 for v in ranks.values()):
                    command('04_whole_recording_fc14.py',subject,log)
                    files=list((RUN/'outputs'/subject/'04_static_fc/matrices').glob('*.npz'))
                    if len(files)!=12:raise ValueError('Missing 14-ROI matrices')
                    for path in files:
                        with np.load(path) as d:
                            a=d['fc14_signed']
                            if a.shape!=(14,14) or not np.isfinite(a).all() or not np.allclose(a,a.T,atol=1e-6):raise ValueError('Invalid 14-ROI matrix')
                    entry['fc14_status']='completed'
            if any(digest(Path(p))!=h for p,h in entry['input_sha256'].items()):raise ValueError('Input changed during run')
            entry.update(status='completed',block_rank_checks=ranks,elapsed_minutes=(time.time()-started)/60)
            save(status_path,state);print(subject,'completed and verified',flush=True)
        state['status']='completed';state.pop('current_subject',None);save(status_path,state)
    except Exception as exc:
        state.update(status='failed',error=str(exc))
        if state.get('current_subject') in state['participants']:state['participants'][state['current_subject']]['status']='failed'
        save(status_path,state);raise
    finally:
        lock.unlink()


if __name__=='__main__':main()
