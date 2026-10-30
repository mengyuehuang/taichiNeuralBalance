"""Isolated experimental pre-ICA review and ICA refit; never promotes to main v1."""
import os
os.environ['MNE_USE_NUMBA']='false'
os.environ['MPLBACKEND']='Agg'
from pathlib import Path
import sys,json,hashlib,importlib.util,importlib,inspect,gzip,base64,csv
from datetime import datetime
V1=Path(__file__).resolve().parents[2]
EXTRA=V1/'extra_review'
os.environ['_MNE_FAKE_HOME_DIR']=str(V1.parent/'.mne_fake_home')
sys.path.insert(0,str(V1/'src'))
import mne
import numpy as np
import matplotlib.pyplot as plt
from mne_icalabel import label_components

CASES=['105_HC3','409_HC4','411_HC3','102_HC1','406_HC3']

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def spans(mask,sf):
    changes=np.diff(np.r_[False,mask,False].astype(int))
    return [(int(a)/sf,int(b)/sf) for a,b in zip(np.where(changes==1)[0],np.where(changes==-1)[0])]

def annotation_mask(raw):
    mask=np.zeros(raw.n_times,bool);sf=raw.info['sfreq']
    for a in raw.annotations:
        if a['description'].lower().startswith('bad'):
            lo=max(0,round((a['onset']-raw.first_time)*sf));hi=min(raw.n_times,round((a['onset']-raw.first_time+a['duration'])*sf))
            mask[lo:hi]=True
    return mask

def export_viewer(dest,subject,raw,pre,names,decisions,hashes,bads):
    dest.mkdir(parents=True,exist_ok=True)
    config=json.loads((V1/'config.local.json').read_text())
    reverse={v:k for k,v in config['channels']['rename_map'].items()}
    x=raw.get_data(picks=[reverse[n] for n in names])*1e6
    y=pre.get_data(picks=names)*1e6
    assert x.shape==y.shape and np.isfinite(x).all() and np.isfinite(y).all()
    sf=pre.info['sfreq'];chunk=int(10*sf)
    folder=dest/'waveform_data';folder.mkdir()
    for i,a in enumerate(range(0,x.shape[1],chunk)):
        block=np.stack([x[:,a:a+chunk],y[:,a:a+chunk]])
        enc=base64.b64encode(gzip.compress(block.astype('<f8').tobytes(),compresslevel=1)).decode()
        (folder/f'chunk_{i:03d}.js').write_text(f'window.registerWaveformChunk({i},{json.dumps(enc)});')
    number,block=subject.split('_')
    summary={'subject':'TCP'+number,'block':block,'duration_seconds':pre.n_times/sf,'channels':names,'samples':int(pre.n_times),'sfreq':sf,'original_bad_intervals':[{'start':a,'end':b} for a,b in spans(annotation_mask(pre),sf)],'source_sha256':hashes,'bad_channels':bads}
    payload={'summary':summary,'candidates':decisions,'chunk_samples':chunk,'chunk_count':int(np.ceil(pre.n_times/chunk)),'format':'gzip_float64_le'}
    template=(EXTRA/'manual_preica_review_404/src/viewer_template.html').read_text(encoding='utf-8')
    template=template.replace('TCP404','TCP'+number).replace('HC4',block)
    template=template.replace('Review only. No data removed, no ICA refitted, no component labels changed. Flags are suggestions, not decisions.', 'Experimental review: the displayed proposed intervals were applied ONLY to this isolated pilot. My decision remains for your independent review. Main v1 is unchanged. Bad channels excluded from reference and ICA: '+(', '.join(bads) or 'none')+'.')
    template=template.replace("$('summary').textContent=`Duration:","$('summary').textContent=`Duration:")
    start=template.index("$('summary').textContent=")
    stop=template.index('\n',start)
    template=template[:start]+"$('summary').textContent=`Duration: ${D.summary.duration_seconds} s. Displayed channels: ${D.summary.channels.length}. Bad channels excluded in pilot: ${D.summary.bad_channels.join(', ')||'none'}. Raw and original PreICA are shown; colored strip marks proposed interval decisions.`;"+template[stop:]
    (dest/'review.html').write_text(template.replace('/*PAYLOAD*/',json.dumps(payload,separators=(',',':'))),encoding='utf-8')
    (dest/'review_decisions.json').write_text(json.dumps({'subject':summary['subject'],'block':block,'source_sha256':hashes,'human_approval':False,'decisions_applied_to_isolated_pilot':True,'bad_channels':bads,'intervals':decisions},indent=2))

def install_audit(callback):
    mod=importlib.import_module('mne.preprocessing.infomax_');ica_mod=importlib.import_module('mne.preprocessing.ica')
    source=inspect.getsource(inspect.unwrap(mod.infomax)).replace('@verbose\n','')
    patches={
      '            # anneal learning rate':"            audit('iteration', step=int(step), change=float(change), angle=float(angledelta), learning_rate=float(l_rate))\n            # anneal learning rate",
      '                        max_iter = step':"                        audit('stop_small_angle', step=int(step))\n                        max_iter = step",
      '                step = max_iter':"                audit('stop_weight_change', step=int(step), change=float(change), threshold=float(w_change))\n                step = max_iter",
      '    # prepare return values':"    audit('return', reported_step=int(step))\n    # prepare return values"}
    for a,b in patches.items():assert source.count(a)==1;source=source.replace(a,b)
    namespace=dict(mod.__dict__);namespace['audit']=callback;exec(compile(source,'pilot_infomax_audit','exec'),namespace)
    original=ica_mod.infomax;ica_mod.infomax=namespace['infomax']
    return ica_mod,original

def main():
    out=EXTRA/'outputs'/('five_block_pilot_'+datetime.now().strftime('%Y%m%d_%H%M%S'));out.mkdir()
    print('OUTPUT '+str(out),flush=True)
    config=json.loads((V1/'config.local.json').read_text())
    spec=importlib.util.spec_from_file_location('v1_ica',V1/'scripts/04_run_ica.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    policy={'scope':'Experimental assistant-proposed screening, not completed human review. No main-v1 changes.','persistent_bad_channel':'Among fully retained 1-second windows: >50% channel PTP >1000 uV AND median channel PTP >10x median of channel medians. Exclude from reference and ICA; no interpolation.','time_intervals':'After removing persistent bad channels: 1-second PTP >1000 uV in any remaining channel OR >=6 remaining channels PTP >500 uV OR >=half channels effectively constant (<1e-5 uV PTP). Add 0.5 s each side; preserve old BAD annotations. Thresholds exploratory, not lab-approved.','ica':'Same extended Infomax/PCA variance policy as v1, seed 97, decim 3. No old IC decisions reused.','automatic_ic_decisions':'Strict prob>0.9: brain include; eye blink, muscle artifact, heart beat, line noise, channel noise exclude; other unresolved. All remaining labels unresolved. Labels computed only on fully retained 2-second epochs; no gap concatenation. 1-55 Hz differs from ICLabel training bandwidth.','not_done':'No final BP, no v2, no main-output promotion. Topographies show the fitted ICA, not a post-rejection refit.'}
    (out/'policy.json').write_text(json.dumps(policy,indent=2))
    results=[]
    for subject in CASES:
        print('PREPARING '+subject,flush=True)
        base=V1/'outputs/v1_preica_test';src=base/f'PreICA/{subject}_preica_raw.fif';oldpath=base/f'ICA/{subject}-ica.fif'
        rawpath=next((V1.parent/'data/TCP_EEG_sync-selected/EEG').rglob(f'TCOA_{subject}.vhdr'))
        hashes={str(p):sha(p) for p in [src,oldpath,rawpath,rawpath.with_suffix('.eeg'),rawpath.with_suffix('.vmrk')]}
        pre=mne.io.read_raw_fif(src,preload=True,verbose=False);old=mne.preprocessing.read_ica(oldpath,verbose=False)
        names=old.ch_names;x=pre.get_data(picks=names)*1e6;sf=int(pre.info['sfreq']);n=pre.n_times;nw=n//sf
        oldmask=annotation_mask(pre);valid=~oldmask[:nw*sf].reshape(nw,sf).any(axis=1)
        ptp=np.ptp(x[:,:nw*sf].reshape(len(names),nw,sf),axis=2);med=np.median(ptp[:,valid],axis=1)
        persistent=(np.mean(ptp[:,valid]>1000,axis=1)>.5)&(med>10*np.median(med))
        bads=[names[k] for k in np.where(persistent)[0]];good=ptp[~persistent]
        flagged=(good.max(axis=0)>1000)|((good>500).sum(axis=0)>=6)|((good<1e-5).sum(axis=0)>=len(good)/2)
        proposed=np.zeros(n,bool)
        for j in np.where(flagged)[0]:proposed[max(0,int((j-.5)*sf)):min(n,int((j+1.5)*sf))]=True
        if nw*sf<n:
            tail=np.ptp(x[~persistent,nw*sf:],axis=1)
            if tail.max()>1000 or (tail>500).sum()>=6:proposed[max(0,int((nw-.5)*sf)):]=True
        finalmask=oldmask|proposed
        decisions=[]
        for excluded in [False,True]:
            for a,b in spans(finalmask==excluded,sf):decisions.append({'start':a,'end':b,'flags':['pilot_proposed_exclude' if excluded else 'pilot_provisional_include'],'assistant_decision':'exclude' if excluded else 'include','decision':'exclude' if excluded else 'include','my_decision':'','reviewer':'Assistant experimental screening','note':'Threshold proposal with 0.5 s padding; original BAD preserved. Review before production use.' if excluded else 'No selected gross-amplitude/flat flag on remaining channels; not a clean-data guarantee.'})
        decisions.sort(key=lambda r:r['start'])
        view=out/'Manual_Review'/subject
        raw=mne.io.read_raw_brainvision(rawpath,verbose=False)
        export_viewer(view,subject,raw,pre,names,decisions,hashes,bads)
        # Screening overview is independent of later ICA results.
        fig,axes=plt.subplots(2,1,figsize=(13,6),sharex=True,constrained_layout=True)
        axes[0].plot(np.arange(nw),ptp.max(axis=0),label='All channels');axes[0].plot(np.arange(nw),good.max(axis=0),label='Without persistent bad channels');axes[0].set_yscale('symlog');axes[0].set_ylabel('1 s max PTP (uV)');axes[0].legend()
        axes[1].plot(np.arange(nw),np.median(good,axis=0));axes[1].set_ylabel('Median channel PTP (uV)');axes[1].set_xlabel('Seconds')
        for a,b in spans(finalmask,sf):
            for ax in axes:ax.axvspan(a,b,color='red',alpha=.12)
        fig.suptitle(subject+' proposed pre-ICA review; bad channels: '+(', '.join(bads) or 'none'));fig.savefig(view/'screening_overview.png',dpi=140);plt.close(fig)
        revised=pre.copy();revised.info['bads']=sorted(set(revised.info['bads'])|set(bads))
        for a,b in spans(proposed,sf):revised.annotations.append(revised.first_time+a,b-a,'BAD_extra_review_pilot')
        target=out/'PreICA'/f'{subject}_preica_raw.fif';target.parent.mkdir(exist_ok=True);revised.save(target,overwrite=False)
        revised.set_eeg_reference('average',projection=False)
        picks=[k for k in mne.pick_types(revised.info,eeg=True,exclude='bads') if revised.ch_names[k] not in config['ica']['exclude_channels']]
        assert len(picks)==len(names)-len(bads)
        logdir=out/'logs';logdir.mkdir(exist_ok=True);events=[]
        with (logdir/f'{subject}_iterations.jsonl').open('w') as log:
            def audit(event,**kw):
                row={'event':event,**kw};events.append(row);log.write(json.dumps(row)+'\n');log.flush()
            module,original=install_audit(audit)
            try:ica=runner.fit_ica_with_retry(revised,picks,config['ica'])
            finally:module.infomax=original
        models=out/'ICA';models.mkdir(exist_ok=True);ica.save(models/f'{subject}-ica.fif',overwrite=False)
        runner.save_ica_figures(revised,ica,out/'ICA_Figures',subject)
        # Export the saved old model using identical plotting defaults, for comparison.
        oldfig=out/'Before_ICA_Figures'/subject;oldfig.mkdir(parents=True)
        figs=old.plot_components(show=False)
        for j,f in enumerate(figs if isinstance(figs,list) else [figs],1):f.savefig(oldfig/f'ica_components_{j}.png',dpi=150);plt.close(f)
        epochs=mne.make_fixed_length_epochs(revised,duration=2,preload=True,reject_by_annotation=True,verbose=False)
        assert len(epochs)>0
        labels=label_components(epochs,ica,method='iclabel')
        review=runner.build_review_table(list(labels['labels']),list(labels['y_pred_proba']),config['ica'])
        def decision(row):
            if row['iclabel_probability']<=.9 or row['iclabel']=='other':return 'review'
            if row['iclabel']=='brain':return 'include'
            return 'exclude' if row['iclabel'].lower() in config['ica']['auto_artifact_labels'] else 'review'
        review['pilot_decision']=review.apply(decision,axis=1)
        review['pilot_reason']=review.apply(lambda r:'User-authorized prob >0.9 rule; '+r['iclabel'] if r['pilot_decision']!='review' else 'Other category or probability <=0.9: unresolved; human review required',axis=1)
        # Only authorized high-confidence decisions populate reviewer2; human reviewer1 stays blank.
        review['review_exclude2']=review['pilot_decision'].map({'include':False,'exclude':True,'review':''})
        review['reviewer2']=review['pilot_decision'].map({'include':'Automatic >0.9, user-authorized','exclude':'Automatic >0.9, user-authorized','review':''})
        review['reviewer2_note']=review['pilot_reason']
        rp=out/'ICA_Review'/subject.split('_')[0];rp.mkdir(parents=True,exist_ok=True);review.to_csv(rp/f'{subject}_ica_review.csv',index=False)
        last_return=[i for i,e in enumerate(events) if e['event']=='return'];start=last_return[-2]+1 if len(last_return)>1 else 0;ev=events[start:]
        stops=[e for e in ev if e['event'].startswith('stop_')]
        reason='weight_change_threshold' if any(e['event']=='stop_weight_change' for e in stops) else ('small_angle_rule' if stops else 'iteration_limit')
        result={'recording':subject,'bad_channels':bads,'source_sha256':hashes,'retained_before_seconds':float((~oldmask).sum()/sf),'retained_after_seconds':float((~finalmask).sum()/sf),'newly_excluded_seconds':float((finalmask&~oldmask).sum()/sf),'old_components':int(old.n_components_),'new_components':int(ica.n_components_),'old_first_pca_fraction':float(old.pca_explained_variance_[0]/old.pca_explained_variance_.sum()),'new_first_pca_fraction':float(ica.pca_explained_variance_[0]/ica.pca_explained_variance_.sum()),'actual_final_fit_updates':sum(e['event']=='iteration' for e in ev),'stop_reason':reason,'stop_events':stops,'automatic_decisions':review['pilot_decision'].value_counts().to_dict(),'label_epochs':len(epochs),'fit_attempts':len(last_return),'status':'pilot_outputs_ready_not_final_BP'}
        assert all(sha(Path(p))==h for p,h in hashes.items()),'Main input changed during pilot'
        (rp/f'{subject}_pilot_summary.json').write_text(json.dumps(result,indent=2));results.append(result)
        (out/'run_status.json').write_text(json.dumps({'complete':False,'results':results},indent=2))
        print('DONE '+json.dumps({k:v for k,v in result.items() if k!='source_sha256'}),flush=True)
    (out/'run_status.json').write_text(json.dumps({'complete':True,'results':results},indent=2))
    links=[]
    for r in results:
        sub=r['recording'];person,block=sub.split('_')
        before=sorted((out/'Before_ICA_Figures'/sub).glob('*.png'));after=sorted((out/'ICA_Figures'/person/block).glob('ica_components*.png'))
        links.append(f'<h2>{sub}</h2><p>Retained {r["retained_after_seconds"]} s; bad channels: {r["bad_channels"]}; old/new ICs: {r["old_components"]}/{r["new_components"]}. IC numbers are NOT matched across fits.</p><a href="Manual_Review/{sub}/review.html">Interval viewer</a> | <a href="ICA_Review/{person}/{sub}_ica_review.csv">IC decisions</a><div class="pair"><section><h3>Before</h3>'+''.join(f'<img src="{p.relative_to(out).as_posix()}">' for p in before)+'</section><section><h3>After</h3>'+''.join(f'<img src="{p.relative_to(out).as_posix()}">' for p in after)+'</section></div>')
    (out/'comparison.html').write_text('<!doctype html><meta charset="utf-8"><title>Extra review pilot</title><style>body{font:16px system-ui;margin:24px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}img{width:100%}h2{border-top:2px solid #aaa;padding-top:16px}</style><h1>Five-block extra review pilot</h1><p>Experimental channel/time decisions; old production files unchanged. Topography appearance alone is not a quality verdict. No final BP or v2. See policy.json.</p>'+''.join(links),encoding='utf-8')
    print('COMPLETE '+str(out),flush=True)

if __name__=='__main__':main()
