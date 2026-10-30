"""Audit provided Clean BP/FC and build explicitly descriptive HC group figures."""
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[2]
HOME=Path(__file__).resolve().parent
OUT=HOME/'rank_corrected/qc_validation'
for key,value in {'_MNE_FAKE_HOME_DIR':str(ROOT/'.mne_fake_home'),'NUMBA_CACHE_DIR':str(ROOT/'.numba_cache'),'OPENBLAS_NUM_THREADS':'2','OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','MPLBACKEND':'Agg'}.items():os.environ.setdefault(key,value)
import argparse,csv,json,sys,time,traceback
from concurrent.futures import ProcessPoolExecutor,as_completed
from fractions import Fraction
sys.path.insert(0,str(ROOT/'auto_fc_pipeline_v2/src'))
import numpy as np
from scipy.signal import welch,resample_poly
from scipy.stats import spearmanr
import mne
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from fc_pipeline_v2.corrected import prepare_segments,NETWORK_ORDER
from fc_pipeline_v2.signal_rank import signal_basis
from fc_pipeline_v2.qc_validation import pairwise_split_fc,prepare_qc_segments,edge_correlation,double_center,fisher,screen

POLICY={
 'version':3,'scope':'HC task; not EC/EO; operational screening, not final biological or statistical approval',
 'qc_minimum_sfreq':256,'qc_fallback_sfreq':[512,'native'],'envelope_sfreq':'matched to native sfreq/round(sfreq/8)','bands':{'broadband':None,'alpha':[8,12],'beta':[13,30]},
 'rank_thresholds':[1e-5,1e-6,1e-7],
 'screens':{'minimum_clean_seconds':120,'minimum_half_seconds':60,'minimum_centered_split_r':.5,'minimum_native_agreement_r':.98,'very_low_rank_review_below':6,'peak_to_peak_review_uV':500,'high_frequency_fraction_review_above':.5,'line60_fraction_review_above':.1},
 'policy_change':'Version 3 separates unsplit full FC from half FC, matches native filtering and segment eligibility, and validates adaptive sampling against native FC. Screening cutoffs unchanged.',
 'split':'Equal retained sample count in chronological order; independent Hilbert transforms in each half; original boundaries retained',
 'sensitivity':'Rank unchanged across thresholds implies identical numerical projection and pooled inverse inputs under this implementation. Changed ranks require full inverse sensitivity recomputation before statistical inclusion.',
 'group_plot':'Participant equal weighting; Fisher-z per block, average matched HC blocks, double-center per participant as reference notebook; never mix symmetric14 and pairwise100 estimators',
 'reference_limit':'Reference Step0b notebook uses EC/EO and labels 100-parcel route visualization/QC only. HC figures are descriptive adaptations, not replication or confirmatory statistical results.'}


def save_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)),encoding='utf-8')


def write_csv(path,rows):
    if not rows:return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)


def safe_metrics(row):
    return {k:(None if isinstance(v,(float,np.floating)) and not np.isfinite(v) else v) for k,v in row.items()}


def participants():
    result=[]
    for directory in sorted((HOME/'rank_corrected/outputs').glob('PCD*')):
        files=sorted((directory/'01_block_level_eeg/montage_aligned').glob('*.fif'))
        if files:result.append(('PCD',directory.name,files,directory))
    for directory in sorted((ROOT/'auto_fc_pipeline_v2/outputs/corrected').iterdir()):
        if not directory.is_dir():continue
        files=sorted((ROOT/'auto_fc_pipeline_v1/outputs/v1_preica_test/Backprojected').glob(f'{directory.name}_HC[1-4]_backproject_raw.fif'))
        if files and any((directory/'04_static_fc/pairwise_100parcels').glob('*.npz')):
            result.append(('TCP','TCP'+directory.name,files,directory))
    return result


def make_kernel(raw,inverse,labels):
    # mean_flip and fixed-normal eLORETA are linear. Evaluating on an identity
    # basis gives the exact sensor->parcel operator without huge full STCs.
    unit=mne.io.RawArray(np.eye(len(raw.ch_names)),raw.info.copy(),verbose='ERROR')
    stc=mne.minimum_norm.apply_inverse_raw(unit,inverse,lambda2=1/9,method='eLORETA',pick_ori='normal',verbose='ERROR')
    kernel=mne.extract_label_time_course(stc,labels,inverse['src'],mode='mean_flip',verbose='ERROR')
    # Direct MNE check on independent observed samples validates linear shortcut.
    sample=raw.copy().crop(tmax=min(1.,(raw.n_times-1)/raw.info['sfreq']))
    direct=mne.minimum_norm.apply_inverse_raw(sample,inverse,lambda2=1/9,method='eLORETA',pick_ori='normal',verbose='ERROR')
    expected=mne.extract_label_time_course(direct,labels,inverse['src'],mode='mean_flip',verbose='ERROR')
    actual=kernel@sample.get_data()
    relative=float(np.linalg.norm(actual-expected)/max(np.linalg.norm(expected),np.finfo(float).tiny))
    if relative>1e-5:raise ValueError(f'Linear kernel disagrees with MNE: {relative}')
    return kernel,relative


def run_subject(task):
    study,participant,files,directory=task
    dest=OUT/participant;dest.mkdir(parents=True,exist_ok=True)
    checkpoint=dest/'qc_results.json'
    if checkpoint.exists():
        report=json.loads(checkpoint.read_text())
        if report.get('qc_policy_version')!=3:
            from refresh_qc_validation import refresh
            refresh(checkpoint);report=json.loads(checkpoint.read_text())
        return report
    mne.set_log_level('ERROR')
    original_id=participant[3:] if study=='TCP' else participant
    group=('YAC' if int(participant[3:])<200 else 'OAC') if study=='PCD' else ('YAC' if int(participant[3:])<200 else 'OAC' if int(participant[3:])<400 else 'TCOA')
    cfg=json.loads((HOME/'rank_corrected/config.rank_corrected.json').read_text())
    inverse=mne.minimum_norm.read_inverse_operator(directory/'02_source_model'/f'{original_id}_common_inverse_operator.fif',verbose='ERROR')
    labels=[l for l in mne.read_labels_from_annot('fsaverage',parc=cfg['parcel_extraction']['parc'],subjects_dir=cfg['paths']['subjects_dir'],verbose='ERROR') if not l.name.startswith('Background') and 'unknown' not in l.name.lower()]
    labels.sort(key=lambda l:(l.name.split('_')[1],NETWORK_ORDER.index(l.name.split('_')[2]),l.name))
    results=[];plots=[];kernel=None;kernel_error=None;rank_inputs=[]
    for path in files:
        hc=__import__('re').search(r'HC[1-4]',path.name)[0]
        state=dest/f'{hc}_progress.json';save_json(state,{'status':'running','stage':'waveform_psd_rank'})
        raw=mne.io.read_raw_fif(path,preload=True,verbose='ERROR')
        raw.pick('eeg');raw.set_eeg_reference('average',projection=True,verbose='ERROR');raw.apply_proj(verbose='ERROR')
        names=list(raw.ch_names)
        if names!=inverse['info']['ch_names']:raise ValueError(f'{participant}: inverse channel order mismatch')
        x=raw.get_data();finite=bool(np.isfinite(x).all())
        basis,spectrum=signal_basis(x,1e-6)
        ranks=[int((spectrum>tol).sum()) for tol in POLICY['rank_thresholds']]
        sf=float(raw.info['sfreq']);valid=np.isfinite(raw.get_data(reject_by_annotation='NaN')).all(0)
        f,psd=welch(x,fs=sf,nperseg=min(round(4*sf),x.shape[1]),axis=1)
        med=np.median(psd,axis=0);total=float(np.trapz(med[(f>=1)&(f<=55)],f[(f>=1)&(f<=55)]))
        high=float(np.trapz(med[(f>=35)&(f<=55)],f[(f>=35)&(f<=55)])/max(total,1e-40))
        line=float(np.trapz(med[(f>=59)&(f<=61)],f[(f>=59)&(f<=61)])/max(total,1e-40))
        peak=float(np.max(np.ptp(x,axis=1))*1e6)
        flat=[names[i] for i in np.where(np.std(x,axis=1)<1e-12)[0]]
        # The original, saved PCD rank-corrected extraction uses this projection.
        # TCP is measured without changing old processing; it remains separately flagged.
        projection_delta=0.
        if study=='PCD':
            y=basis@(basis.T@x)
            projection_delta=float(np.linalg.norm(x-y)/np.linalg.norm(x));raw._data=y;x=raw._data
        rank_inputs.append((path.name,x[:,::max(1,x.shape[1]//3000)].copy()))
        if kernel is None:kernel,kernel_error=make_kernel(raw,inverse,labels)
        elif names!=inverse['info']['ch_names']:raise ValueError('Channel mismatch across blocks')
        ratio=Fraction(128/sf).limit_denominator(10000)
        source_parts=[]
        # Start a new segment at BAD gaps and explicit boundaries.
        boundaries=np.zeros(raw.n_times,dtype=bool);boundaries[0]=True
        for onset,desc in zip(raw.annotations.onset,raw.annotations.description):
            if 'boundary' in str(desc).lower() or str(desc).lower().startswith('edge'):
                index=int(round((onset-raw.first_time)*sf))
                if 0<=index<raw.n_times:boundaries[index]=True
        from fc_pipeline_v2.corrected import continuous_segments
        starts,stops=continuous_segments(valid,boundaries)
        source_native=kernel@x
        block_metrics=[]
        for band,limits in POLICY['bands'].items():
            save_json(state,{'status':'running','stage':'split_half_FC','band':band})
            native_paths=list((directory/'04_static_fc/pairwise_100parcels').glob(f'{original_id}_{hc}_*_{band}_fc.npz'))
            if len(native_paths)!=1:raise ValueError(f'Missing native FC for {hc}/{band}')
            with np.load(native_paths[0]) as d:
                native=d['fc100_signed'];parcel_names=d['parcel_names']
            for target_rate in [256,512,sf]:
                prepared,qc_rate,qc_block=prepare_qc_segments(source_native,starts,stops,sf,limits,target_rate)
                matrices,counts=pairwise_split_fc(prepared,qc_block)
                full,first,last=matrices
                if edge_correlation(native,full)>=.98 or qc_rate==sf:break
            if list(parcel_names)!=[l.name for l in labels]:raise ValueError('Parcel order mismatch')
            row=dict(study=study,participant=participant,group=group,hc=hc,band=band,finite=finite,matrix_error=False,clean_seconds=sum(p.shape[1] for p in prepared)/128,half_seconds_min=min(counts)/8,sensor_rank=ranks[1],rank_tol_1e5=ranks[0],rank_tol_1e6=ranks[1],rank_tol_1e7=ranks[2],threshold_stable=len(set(ranks))==1,flat_channels=';'.join(flat),peak_to_peak_uv=peak,high_frequency_fraction=high,line60_fraction=line,native_agreement_r=edge_correlation(native,full),native_agreement_centered_r=edge_correlation(native,full,True),native_fisher_z_mae=float(np.mean(np.abs(fisher(native)[np.triu_indices(100,1)]-fisher(full)[np.triu_indices(100,1)]))),split_half_r=edge_correlation(first,last),split_half_centered_r=edge_correlation(first,last,True),split_half_spearman=float(spearmanr(first[np.triu_indices(100,1)],last[np.triu_indices(100,1)]).statistic),kernel_relative_error=kernel_error,projection_relative_change=projection_delta)
            row.update(clean_seconds=sum(p.shape[1] for p in prepared)/qc_rate,half_seconds_min=min(counts)/(qc_rate/qc_block),qc_sfreq=qc_rate,qc_envelope_hz=qc_rate/qc_block,qc_policy_version=3)
            status,reasons=screen(row)
            if study=='TCP':reasons.append('legacy_source_rank_policy_not_harmonized');status='review_required'
            row.update(status=status,reasons=';'.join(reasons),low_rank_lt14=ranks[1]<14)
            results.append(safe_metrics(row));block_metrics.append(row)
            row.update(clean_seconds=sum(p.shape[1] for p in prepared)/qc_rate,half_seconds_min=min(counts)/(qc_rate/qc_block),qc_sfreq=qc_rate,qc_envelope_hz=qc_rate/qc_block,qc_policy_version=3)
            np.savez_compressed(dest/f'{hc}_{band}_split_fc.npz',qc_full=full,first_half=first,second_half=last,parcel_names=parcel_names,half_envelope_samples=counts,qc_sfreq=qc_rate,qc_policy_version=3)
        offset=max(0,int(x.shape[1]/2-5*sf));stride=max(1,int(sf/200))
        plots.append(dict(hc=hc,wave=x[:8,offset:offset+int(10*sf):stride]*1e6,time=np.arange(x[:8,offset:offset+int(10*sf):stride].shape[1])*stride/sf,names=names[:8],f=f,median=med,low=np.percentile(psd,10,axis=0),high=np.percentile(psd,90,axis=0),spectrum=spectrum,stability=[r['split_half_centered_r'] for r in block_metrics]))
        save_json(state,{'status':'completed'})
        raw.close()
    pooled=np.concatenate([v for k,v in rank_inputs],axis=1)
    _,pooled_spectrum=signal_basis(pooled,1e-6,max_samples=pooled.shape[1])
    pooled_ranks=[int((pooled_spectrum>tol).sum()) for tol in POLICY['rank_thresholds']]
    for row in results:
        row['pooled_rank_tol_1e5'],row['pooled_rank_tol_1e6'],row['pooled_rank_tol_1e7']=pooled_ranks
        if len(set(pooled_ranks))>1:
            row['status']='review_required';row['reasons']+=';pooled_rank_threshold_sensitive'
    fig,axes=plt.subplots(len(plots),4,figsize=(20,max(4,3.3*len(plots))),squeeze=False)
    for i,p in enumerate(plots):
        ax=axes[i,0];scale=max(20,float(np.percentile(np.std(p['wave'],axis=1),90))*5)
        for j,w in enumerate(p['wave']):ax.plot(p['time'],w+j*scale,lw=.5)
        ax.set_yticks(np.arange(len(p['names']))*scale,p['names'],fontsize=7);ax.set_title(p['hc']+' EEG middle 10 s');ax.set_xlabel('Seconds; traces offset')
        ax=axes[i,1];mask=(p['f']>=.5)&(p['f']<=70)
        ax.semilogy(p['f'][mask],p['median'][mask]*1e12);ax.fill_between(p['f'][mask],p['low'][mask]*1e12,p['high'][mask]*1e12,alpha=.2)
        ax.set_title('Welch PSD: median, channel P10-P90');ax.set_xlabel('Hz');ax.set_ylabel('uV squared / Hz')
        ax=axes[i,2];ax.semilogy(np.arange(1,len(p['spectrum'])+1),p['spectrum'],'o-',ms=2)
        for tol in POLICY['rank_thresholds']:ax.axhline(tol,lw=.6,ls='--')
        ax.set_title('Relative singular values');ax.set_xlabel('Direction index')
        ax=axes[i,3];ax.bar(['Broadband','Alpha','Beta'],p['stability']);ax.axhline(.5,color='r',ls='--',lw=.8);ax.set_ylim(-1,1);ax.set_title('Centered FC chronological split r')
    fig.suptitle(f'{participant}: waveform, spectrum, rank and temporal stability; screening only')
    fig.tight_layout();fig.savefig(dest/'waveform_psd_rank_stability.png',dpi=130);plt.close(fig)
    result={'participant':participant,'study':study,'group':group,'rows':results,'source_directory':str(directory),'legacy_policy_review':study=='TCP','qc_policy_version':3}
    save_json(checkpoint,result);write_csv(dest/'qc_metrics.csv',results)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--subject');parser.add_argument('--workers',type=int,default=2);args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);save_json(OUT/'qc_policy.json',POLICY)
    tasks=participants()
    if args.subject:tasks=[t for t in tasks if t[1]==args.subject]
    statuses={};results=[]
    print(f'QC subjects: {len(tasks)}; workers={args.workers}',flush=True)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(run_subject,t):t[1] for t in tasks}
        for future in as_completed(futures):
            name=futures[future]
            try:
                result=future.result();results.append(result);statuses[name]={'status':'completed','blocks':len(result['rows'])//3}
                print(f'{name}: QC completed',flush=True)
            except Exception as exc:
                statuses[name]={'status':'failed','error':str(exc)}
                (OUT/f'{name}_error.txt').write_text(traceback.format_exc(),encoding='utf-8')
                print(f'{name}: QC FAILED: {exc}',flush=True)
            save_json(OUT/'run_status.json',statuses)
    all_rows=[row for p in sorted(OUT.glob('*/qc_results.json')) for row in json.loads(p.read_text())['rows']]
    write_csv(OUT/'all_recording_qc.csv',all_rows)
    import subprocess
    subprocess.run([sys.executable,str(HOME/'threshold_sensitivity.py')],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(HOME/'summarize_qc.py')],cwd=ROOT,check=True)


if __name__=='__main__':main()
