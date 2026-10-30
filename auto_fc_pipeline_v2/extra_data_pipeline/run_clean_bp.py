"""Run existing v2 on teacher Clean BP without reapplying preprocessing or ICA."""
from pathlib import Path
import argparse,csv,json,os,re,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2]
HOME=Path(__file__).resolve().parent
os.environ.setdefault('_MNE_FAKE_HOME_DIR',str(ROOT/'.mne_fake_home'))
os.environ.setdefault('NUMBA_CACHE_DIR',str(ROOT/'.numba_cache'))
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
import numpy as np
import mne
from scipy.io import loadmat
sys.path.insert(0,str(ROOT/'auto_fc_pipeline_v2/src'))
from fc_pipeline_v2.cohort_policy import is_excluded

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subject',help='Optional ID, e.g. PCD105; default processes all available participants')
    args=parser.parse_args()
    source=ROOT/'data/VRHCT_CleanData-selected/Clean BP'
    inputs=HOME/'inputs'
    inputs.mkdir(parents=True,exist_ok=True)
    logs=HOME/'logs';logs.mkdir(exist_ok=True)
    cfg=json.loads((ROOT/'auto_fc_pipeline_v2/config.hc_corrected.example.json').read_text())
    cfg['paths']['backprojected_dir']=str(inputs)
    cfg['paths']['corrected_output_root']=str(HOME/'outputs')
    for key in ('montage_path','subjects_dir'): cfg['paths'][key]=str((ROOT/cfg['paths'][key]).resolve())
    cfg['inputs']={'backprojected_format':'mne_raw_fif','backprojected_glob':'PCD*_HC[1-4]_backproject_raw.fif'}
    cfg['naming']['subject_regex']=r'^(PCD\d{3})(?=_HC[1-4])'
    cfg['groups']={'YAC':[f'PCD{i}' for i in range(101,121)],'OAC':[f'PCD{i}' for i in range(201,221)],'TCOA':[]}
    config=HOME/'config.clean_bp.json';config.write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    grouped={};selection=[]
    for p in sorted(source.glob('*.set')):
        match=re.fullmatch(r'(\d{3})_time_(HC[1-4])(_2)?_backproject',p.stem)
        if not match: raise ValueError(f'Unrecognized input: {p}')
        sid,block,variant=match.groups();participant='PCD'+sid
        reason='teacher_confirmed_exclude' if is_excluded(participant) else 'ambiguous_duplicate_HC4' if sid=='208' and block=='HC4' else ''
        selection.append(dict(participant=participant,block=block,path=str(p),status='hold' if reason else 'selected',reason=reason))
        if not reason: grouped.setdefault(participant,[]).append((block,p))
    with (HOME/'input_manifest.csv').open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=selection[0]);writer.writeheader();writer.writerows(selection)
    if args.subject:
        if args.subject not in grouped: raise ValueError('No selected Clean BP files for requested participant')
        grouped={args.subject:grouped[args.subject]}
    status_path=HOME/'run_status.json'
    statuses=json.loads(status_path.read_text()) if status_path.exists() else {}
    for participant,records in sorted(grouped.items()):
        if statuses.get(participant,{}).get('status')=='completed':
            print(f'{participant}: already completed; skipping',flush=True);continue
        started=time.time();entry={'status':'running','blocks':[b for b,p in records],'source':'teacher_clean_bp','started_unix':started}
        statuses[participant]=entry;status_path.write_text(json.dumps(statuses,indent=2),encoding='utf-8')
        print(f'{participant}: preparing {len(records)} Clean BP blocks',flush=True)
        try:
            ranks=[]
            for block,p in records:
                meta=loadmat(p,simplify_cells=True)['EEG']
                rank=int(np.asarray(meta['icaweights']).shape[0]);ranks.append(rank)
                target=inputs/f'{participant}_{block}_backproject_raw.fif'
                if not target.exists() or mne.io.read_raw_fif(target,preload=False,verbose='ERROR').info.get('description') != 'Teacher Clean BP; lab positional labels; no additional filtering or ICA.':
                    raw=mne.io.read_raw_eeglab(p,preload=True,verbose='ERROR')
                    assert raw.n_times==meta['pnts'] and len(raw.ch_names)==meta['nbchan']
                    assert np.isfinite(raw._data).all()
                    lab=json.loads((ROOT/'auto_fc_pipeline_v1/config.local.json').read_text())
                    labels=list(lab['channels']['rename_map'].values())
                    assert len(raw.ch_names)==len(labels)==63
                    # Companion MATLAB analysis code defines the loaded 63-channel order.
                    raw.rename_channels(dict(zip(raw.ch_names,labels)))
                    raw.set_channel_types({k:v for k,v in lab['channels']['channel_types'].items() if k in raw.ch_names},verbose='ERROR')
                    raw.info['description']='Teacher Clean BP; lab positional labels; no additional filtering or ICA.'
                    raw.save(target,overwrite=True,verbose='ERROR');raw.close()
            entry['retained_ica_components']=dict(zip(entry['blocks'],ranks))
            # Fewer than 14 retained components cannot support full-rank 14-ROI correction.
            route='both' if min(ranks)>=14 else '100'
            entry['requested_route']=route
            entry['fc14_status']='pending' if route=='both' else 'skipped_insufficient_component_rank'
            status_path.write_text(json.dumps(statuses,indent=2),encoding='utf-8')
            log=logs/f'{participant}.log'
            command=[sys.executable,str(ROOT/'auto_fc_pipeline_v2/scripts/run_participant.py'),participant,'--config',str(config),'--start-at','1','--route',route]
            print(f'{participant}: running v2 route={route}; log={log.name}',flush=True)
            old_log=log.read_text(errors='replace') if log.exists() else ''
            if f'Completed participant {participant}' in old_log:
                result=subprocess.CompletedProcess(command,0)
            else:
                with log.open('w',encoding='utf-8') as handle:
                    result=subprocess.run(command,cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT)
            if result.returncode:
                # A 14-ROI numerical rank failure must not suppress the independent 100-parcel route.
                if route=='both' and 'symmetric correction invalid' in log.read_text(errors='replace'):
                    entry['fc14_status']='failed_signal_rank_check'
                    with log.open('a',encoding='utf-8') as handle:
                        result=subprocess.run([sys.executable,str(ROOT/'auto_fc_pipeline_v2/scripts/04_whole_recording_fc.py'),'--config',str(config),'--subject',participant],cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT)
                if result.returncode: raise RuntimeError(f'v2 returned {result.returncode}; see {log}')
            static=HOME/'outputs'/participant/'04_static_fc'
            matrices=list(static.rglob('*.npz'))
            expected=len(records)*3*(2 if route=='both' and entry['fc14_status']=='pending' else 1)
            if len(matrices)<expected: raise RuntimeError(f'Only {len(matrices)} matrix files; expected at least {expected}')
            for matrix in matrices:
                with np.load(matrix) as data:
                    # Secondary files deliberately contain NaN fc14 placeholders
                    # when symmetric correction fails its rank check.
                    key='fc100_signed' if 'fc100_signed' in data.files else 'fc14_signed'
                    value=data[key]
                    assert np.isfinite(value).all(),str(matrix)
                    assert np.allclose(value,value.T,atol=1e-6),str(matrix)
                    assert np.allclose(np.diag(value),1,atol=1e-6),str(matrix)
            entry.update(status='completed',matrix_npz_count=len(matrices),elapsed_minutes=round((time.time()-started)/60,2))
            if entry['fc14_status']=='pending':entry['fc14_status']='completed'
            print(f'{participant}: completed, {len(matrices)} matrix files',flush=True)
        except Exception as exc:
            entry.update(status='failed',error=str(exc),elapsed_minutes=round((time.time()-started)/60,2))
            print(f'{participant}: FAILED: {exc}',flush=True)
        status_path.write_text(json.dumps(statuses,indent=2),encoding='utf-8')

if __name__=='__main__':main()
