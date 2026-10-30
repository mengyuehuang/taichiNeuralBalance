"""Upgrade existing EEG QC to matched filtering, segments and independent full FC."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='2'
from pathlib import Path
import json,sys,traceback
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from scipy.stats import spearmanr
from scipy.signal import welch
import run_qc_validation as base
from fc_pipeline_v2.qc_validation import prepare_qc_segments,pairwise_split_fc,edge_correlation,fisher
from fc_pipeline_v2.signal_rank import signal_basis
OUT=base.OUT

def restore_missing_parcels(directory,ident,hc):
    """Restore a missing intermediate using the saved inverse, never refit ICA."""
    if ident.startswith('PCD'):raise ValueError('PCD recovery requires its numerical-rank projection; use formal step 03')
    import functools
    mne=base.mne
    source=next((directory/'01_block_level_eeg/montage_aligned').glob(f'{ident}_{hc}_*_montage_raw.fif'))
    inverse_file=directory/'02_source_model'/f'{ident}_common_inverse_operator.fif'
    inverse=mne.minimum_norm.read_inverse_operator(inverse_file,verbose='ERROR')
    cfg=json.loads((base.HOME/'rank_corrected/config.rank_corrected.json').read_text())
    labels=[l for l in mne.read_labels_from_annot('fsaverage',parc=cfg['parcel_extraction']['parc'],subjects_dir=cfg['paths']['subjects_dir'],verbose='ERROR') if not l.name.startswith('Background') and 'unknown' not in l.name.lower()]
    labels.sort(key=lambda l:(l.name.split('_')[1],base.NETWORK_ORDER.index(l.name.split('_')[2]),l.name))
    if len(labels)!=100:raise ValueError('Recovery requires exactly 100 parcels')
    rois=[]
    for hemi in ['LH','RH']:
        for network in base.NETWORK_ORDER:
            members=[l for l in labels if l.name.split('_')[1:3]==[hemi,network]]
            roi=functools.reduce(lambda a,b:a+b,members);roi.name=f'{hemi}_{network}';rois.append(roi)
    raw=mne.io.read_raw_fif(source,preload=True,verbose='ERROR')
    raw.pick(inverse['info']['ch_names']);raw.reorder_channels(inverse['info']['ch_names'])
    raw.set_eeg_reference('average',projection=True,verbose='ERROR');raw.apply_proj(verbose='ERROR')
    # Preserve the legacy TCP source model. Do not apply the PCD rank policy.
    kernel,error=base.make_kernel(raw,inverse,labels+rois)
    tc=np.empty((len(labels)+len(rois),raw.n_times),dtype=np.float32)
    for start in range(0,raw.n_times,10000):
        stop=min(start+10000,raw.n_times);tc[:,start:stop]=kernel@raw.get_data(start=start,stop=stop)
    valid=np.isfinite(raw.get_data(reject_by_annotation='NaN')).all(0)
    boundaries=np.zeros(raw.n_times,dtype=bool);boundaries[0]=True
    for onset,desc in zip(raw.annotations.onset,raw.annotations.description):
        if 'boundary' in str(desc).lower() or str(desc).lower().startswith('edge'):
            index=round((onset-raw.first_time)*raw.info['sfreq'])
            if 0<=index<raw.n_times:boundaries[index]=True
    from fc_pipeline_v2.corrected import continuous_segments
    starts,stops=continuous_segments(valid,boundaries)
    target=directory/'03_roi_timeseries'/source.name.replace('_montage_raw.fif','_signed_parcels.npz')
    target.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(target,signed_tc100=tc[:100],signed_tc14=tc[100:],parcel_names=np.array([l.name for l in labels]),parcel_network=np.array([l.name.split('_')[2] for l in labels]),roi_names=np.array([l.name for l in rois]),sfreq=float(raw.info['sfreq']),segment_starts=starts,segment_stops=stops,pick_ori='normal',inverse_file=str(inverse_file.resolve()),source_file=str(source.resolve()))
    base.save_json(target.with_suffix('.recovery.json'),{'method':'saved inverse linear projection; no ICA refit or rank change','direct_MNE_kernel_relative_error':error,'source':str(source.resolve()),'restored_file':str(target.resolve())})
    raw.close();print(f'{ident} {hc}: restored missing parcel time series; MNE relative error={error:.3g}',flush=True)
    return target

def refresh(path):
    report=json.loads(path.read_text());sid=report['participant'];dest=path.parent
    if report.get('qc_policy_version')==3:return sid
    plots=[];new_rows=[]
    for hc in sorted({r['hc'] for r in report['rows']}):
        checkpoint=dest/f'{hc}_qc_v3.json';plotfile=dest/f'{hc}_qc_plot_data.npz'
        if checkpoint.exists() and plotfile.exists():
            new_rows.extend(json.loads(checkpoint.read_text()))
            with np.load(plotfile) as d:plots.append({k:d[k] for k in d.files})
            continue
        rows=[r.copy() for r in report['rows'] if r['hc']==hc]
        directory=Path(report['source_directory']);ident=sid if report['study']=='PCD' else sid[3:]
        file=next((directory/'03_roi_timeseries').glob(f'{ident}_{hc}_*_signed_parcels.npz'),None)
        if file is None:file=restore_missing_parcels(directory,ident,hc)
        with np.load(file) as d:
            x=d['signed_tc100'];sf=float(d['sfreq']);starts=d['segment_starts'];stops=d['segment_stops'];source=str(d['source_file'])
        for row in rows:
            band=row['band'];base.save_json(dest/f'{hc}_progress.json',{'status':'running','stage':'corrected_FC_QC','band':band,'version':3})
            native_file=next((directory/'04_static_fc/pairwise_100parcels').glob(f'{ident}_{hc}_*_{band}_fc.npz'))
            with np.load(native_file) as d:native=d['fc100_signed'];names=d['parcel_names']
            attempts=[]
            for rate_target in [256,512,sf]:
                parts,rate,block=prepare_qc_segments(x,starts,stops,sf,base.POLICY['bands'][band],rate_target)
                matrices,counts=pairwise_split_fc(parts,block)
                full,first,last=matrices;agreement=edge_correlation(native,full)
                attempts.append({'sfreq':rate,'edge_r':agreement})
                if agreement>=.98 or rate==sf:break
            row.update(native_agreement_r=agreement,native_agreement_centered_r=edge_correlation(native,full,True),native_fisher_z_mae=float(np.mean(np.abs(fisher(native)[np.triu_indices(100,1)]-fisher(full)[np.triu_indices(100,1)]))),split_half_r=edge_correlation(first,last),split_half_centered_r=edge_correlation(first,last,True),split_half_spearman=float(spearmanr(first[np.triu_indices(100,1)],last[np.triu_indices(100,1)]).statistic),clean_seconds=sum(p.shape[1] for p in parts)/rate,half_seconds_min=min(counts)/(rate/block),qc_sfreq=rate,qc_envelope_hz=rate/block,qc_policy_version=3,agreement_attempts=json.dumps(attempts),agreement_input='saved_native_signed_parcels')
            np.savez_compressed(dest/f'{hc}_{band}_split_fc.npz',qc_full=full,first_half=first,second_half=last,parcel_names=names,half_envelope_samples=counts,qc_sfreq=rate,envelope_hz_actual=rate/block,qc_policy_version=3)
            print(f'{sid} {hc} {band}: corrected QC r={agreement:.6f}',flush=True)
        # Waveform/spectral metrics remain unchanged; regenerate the combined
        # figure so its stability panel uses the corrected computation too.
        raw=base.mne.io.read_raw_fif(source,preload=True,verbose='ERROR')
        raw.pick('eeg');raw.set_eeg_reference('average',projection=True,verbose='ERROR');raw.apply_proj(verbose='ERROR')
        sensor=raw.get_data();sfraw=float(raw.info['sfreq'])
        f,psd=welch(sensor,fs=sfraw,nperseg=min(round(4*sfraw),sensor.shape[1]),axis=1)
        _,spectrum=signal_basis(sensor,1e-6)
        offset=max(0,int(sensor.shape[1]/2-5*sfraw));stride=max(1,int(sfraw/200))
        wave=sensor[:8,offset:offset+int(10*sfraw):stride]*1e6
        plot=dict(hc=hc,wave=wave,time=np.arange(wave.shape[1])*stride/sfraw,names=np.array(raw.ch_names[:8]),f=f,median=np.median(psd,axis=0),low=np.percentile(psd,10,axis=0),high=np.percentile(psd,90,axis=0),spectrum=spectrum,stability=np.array([next(r['split_half_centered_r'] for r in rows if r['band']==b) for b in ['broadband','alpha','beta']]))
        raw.close();del sensor
        np.savez_compressed(plotfile,**plot);plots.append(plot)
        base.save_json(checkpoint,rows);new_rows.extend(rows)
        base.save_json(dest/f'{hc}_progress.json',{'status':'completed','version':3})
    fig,axes=base.plt.subplots(len(plots),4,figsize=(20,max(4,3.3*len(plots))),squeeze=False)
    for i,p in enumerate(plots):
        ax=axes[i,0];scale=max(20,float(np.percentile(np.std(p['wave'],axis=1),90))*5)
        for j,w in enumerate(p['wave']):ax.plot(p['time'],w+j*scale,lw=.5)
        ax.set_yticks(np.arange(len(p['names']))*scale,p['names'],fontsize=7);ax.set_title(str(p['hc'])+' EEG middle 10 s')
        mask=(p['f']>=.5)&(p['f']<=70);ax=axes[i,1]
        ax.semilogy(p['f'][mask],p['median'][mask]*1e12);ax.fill_between(p['f'][mask],p['low'][mask]*1e12,p['high'][mask]*1e12,alpha=.2);ax.set_title('Welch PSD; median and channel P10-P90');ax.set_xlabel('Hz')
        ax=axes[i,2];ax.semilogy(np.arange(1,len(p['spectrum'])+1),p['spectrum'],'o-',ms=2)
        for tol in base.POLICY['rank_thresholds']:ax.axhline(tol,lw=.6,ls='--')
        ax.set_title('Relative singular values')
        ax=axes[i,3];ax.bar(['Broadband','Alpha','Beta'],p['stability']);ax.axhline(.5,color='r',ls='--');ax.set_ylim(-1,1);ax.set_title('Corrected chronological split r')
    fig.suptitle(f'{sid}: QC version 3; matched native segments and envelope intervals');fig.tight_layout();fig.savefig(dest/'waveform_psd_rank_stability.png',dpi=130);base.plt.close(fig)
    report.update(rows=new_rows,qc_policy_version=3)
    base.save_json(path,report);base.write_csv(dest/'qc_metrics.csv',new_rows)
    error_file=OUT/f'{sid}_qc_refresh_error.txt'
    if error_file.exists():error_file.unlink()
    return sid

def main():
    all_tasks=sorted(OUT.glob('*/qc_results.json'))
    statuses={p.parent.name:'completed' for p in all_tasks if json.loads(p.read_text()).get('qc_policy_version')==3}
    tasks=[p for p in all_tasks if p.parent.name not in statuses]
    expected=len(all_tasks)
    base.save_json(OUT/'qc_refresh_status.json',{'expected':expected,'completed':len(statuses),'failed':[],'status':'running'})
    with ProcessPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(refresh,p):p.parent.name for p in tasks}
        for future in as_completed(futures):
            sid=futures[future]
            try:future.result();statuses[sid]='completed'
            except Exception:
                statuses[sid]='failed';(OUT/f'{sid}_qc_refresh_error.txt').write_text(traceback.format_exc())
            base.save_json(OUT/'qc_refresh_status.json',{'expected':expected,'completed':sum(v=='completed' for v in statuses.values()),'failed':[s for s,v in statuses.items() if v=='failed'],'status':'running' if not any(v=='failed' for v in statuses.values()) else 'failed'})
    if any(v=='failed' for v in statuses.values()):raise RuntimeError('QC refresh failed; summaries not regenerated')
    import subprocess
    try:
        base.save_json(OUT/'qc_refresh_status.json',{'expected':expected,'completed':len(statuses),'failed':[],'status':'running','stage':'sensitivity_and_summary'})
        subprocess.run([sys.executable,str(base.HOME/'summarize_qc.py')],check=True)
    except Exception as exc:
        base.save_json(OUT/'qc_refresh_status.json',{'expected':expected,'completed':len(statuses),'failed':[],'status':'failed','stage':'sensitivity_and_summary','error':str(exc)})
        raise
    base.save_json(OUT/'qc_policy.json',base.POLICY)
    base.save_json(OUT/'qc_refresh_status.json',{'expected':expected,'completed':len(statuses),'failed':[],'status':'completed'})

if __name__=='__main__':main()
