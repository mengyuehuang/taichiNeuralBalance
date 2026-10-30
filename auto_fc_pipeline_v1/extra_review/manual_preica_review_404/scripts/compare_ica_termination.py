"""Read-only source instrumentation: record actual Infomax termination for two reviews."""
import os
os.environ['MNE_USE_NUMBA']='false'
os.environ['MPLBACKEND']='Agg'
from pathlib import Path
import sys, json, inspect, importlib, hashlib
from datetime import datetime
HERE=Path(__file__).resolve().parents[1]
ROOT=HERE.parents[1]
os.environ['_MNE_FAKE_HOME_DIR']=str(ROOT.parent/'.mne_fake_home')
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import mne
from mne_icalabel import label_components

def main():
    out=HERE/'outputs/Comparisons'/('termination_comparison_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    out.mkdir(exist_ok=False)
    print('OUTPUT: '+str(out),flush=True)
    spec=importlib.util.spec_from_file_location('runner',ROOT/'scripts/04_run_ica.py')
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    mod=importlib.import_module('mne.preprocessing.infomax_')
    ica_mod=importlib.import_module('mne.preprocessing.ica')
    original=ica_mod.infomax
    source=inspect.getsource(inspect.unwrap(mod.infomax))
    source=source.replace('@verbose\n','')
    replacements={
        '            # anneal learning rate': "            audit('iteration', step=int(step), change=float(change), learning_rate=float(l_rate), angle=float(angledelta))\n            # anneal learning rate",
        '                        max_iter = step': "                        audit('stop_small_angle', step=int(step), count=int(count_small_angle))\n                        max_iter = step",
        '                step = max_iter': "                audit('stop_weight_change', step=int(step), change=float(change), threshold=float(w_change))\n                step = max_iter",
        '    # prepare return values': "    audit('return', reported_step=int(step), effective_limit=int(max_iter))\n    # prepare return values",
    }
    for old,new in replacements.items():
        assert source.count(old)==1,old
        source=source.replace(old,new)
    (out/'instrumented_infomax.py').write_text(source)
    config=json.loads((ROOT/'config.local.json').read_text())
    (out/'provenance.json').write_text(json.dumps({'mne_version':mne.__version__,'original_infomax_sha256':hashlib.sha256(inspect.getsource(inspect.unwrap(mod.infomax)).encode()).hexdigest(),'config':config,'instrumentation':'Only audit calls inserted; same mathematical updates and stopping rules; installed package unchanged.'},indent=2))
    # Check that observation does not change numerical results on a small fixed input.
    namespace=dict(mod.__dict__);namespace['audit']=lambda *a,**k:None
    exec(compile(source,'instrumented_infomax','exec'),namespace)
    toy=np.random.RandomState(5).normal(size=(300,4))
    kwargs=dict(random_state=97,max_iter=5,return_n_iter=True,verbose=False)
    a=original(toy.copy(),**kwargs);b=namespace['infomax'](toy.copy(),**kwargs)
    assert np.array_equal(a[0],b[0]) and a[1]==b[1]
    results=[]
    models=[]
    try:
        for name,filename in [('human_158s','human_review_decisions.json'),('strict_108s','strict_review_decisions.json')]:
            dest=out/name;dest.mkdir()
            decisions=json.loads((HERE/'outputs/Manual_Review'/filename).read_text())
            (dest/'decisions.json').write_text(json.dumps(decisions,indent=2))
            src=ROOT/'outputs/v1_preica_test/PreICA/404_HC4_preica_raw.fif'
            assert hashlib.sha256(src.read_bytes()).hexdigest()==decisions['source_sha256'][str(src)]
            raw=mne.io.read_raw_fif(src,preload=True,verbose=False)
            for r in decisions['intervals']:
                if r['my_decision']=='exclude':raw.annotations.append(raw.first_time+r['start'],r['end']-r['start'],'BAD_human_interval')
            raw.set_eeg_reference('average',projection=False)
            picks=[p for p in mne.pick_types(raw.info,eeg=True) if raw.ch_names[p] not in config['ica']['exclude_channels']]
            events=[]
            with (dest/'iterations.jsonl').open('w') as log:
                def audit(event,**values):
                    row={'event':event,**values};events.append(row);log.write(json.dumps(row)+'\n');log.flush()
                namespace=dict(mod.__dict__);namespace['audit']=audit
                exec(compile(source,'instrumented_infomax','exec'),namespace)
                ica_mod.infomax=namespace['infomax']
                print('Fitting '+name,flush=True)
                ica=runner.fit_ica_with_retry(raw,picks,config['ica'])
            ica.save(dest/'404_HC4-ica.fif',overwrite=False)
            # Keep each retry identifiable by the preceding return event.
            segments=[];segment=[]
            for event in events:
                segment.append(event)
                if event['event']=='return':segments.append(segment);segment=[]
            final=segments[-1]
            steps=[e for e in final if e['event']=='iteration']
            reasons=[e for e in final if e['event'].startswith('stop_')]
            reason='weight_change_threshold' if any(e['event']=='stop_weight_change' for e in reasons) else ('small_angle_rule' if reasons else 'iteration_limit')
            result={'scheme':name,'retained_seconds':raw.get_data(picks=[picks[0]],reject_by_annotation='omit').shape[1]/raw.info['sfreq'],'components':int(ica.n_components_),'reported_n_iter':int(ica.n_iter_),'actual_final_fit_updates':len(steps),'last_step':steps[-1],'stop_reason':reason,'stop_events':reasons,'weight_change_converged':reason=='weight_change_threshold','fit_attempts':len(segments),'first_pca_fraction':float(ica.pca_explained_variance_[0]/ica.pca_explained_variance_.sum())}
            (dest/'termination.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
            runner.save_ica_figures(raw,ica,dest/'ICA_Figures','404_HC4')
            epochs=mne.make_fixed_length_epochs(raw,duration=2,preload=True,reject_by_annotation=True,verbose=False)
            labels=label_components(epochs,ica,method='iclabel')
            table=runner.build_review_table(list(labels['labels']),list(labels['y_pred_proba']),config['ica'])
            table.to_csv(dest/'ica_review.csv',index=False)
            result['label_epochs']=len(epochs)
            result['automatic_label_counts']=table['iclabel'].value_counts().to_dict()
            results.append(result);models.append(ica)
            (out/'comparison.json').write_text(json.dumps({'results':results,'complete':False},indent=2))
        from scipy.optimize import linear_sum_assignment
        corr=np.corrcoef(models[0].get_components().T,models[1].get_components().T)[:models[0].n_components_,models[0].n_components_:]
        row,col=linear_sum_assignment(-np.abs(corr))
        matches=[{'human_ic':int(i),'strict_ic':int(j),'absolute_spatial_correlation':float(abs(corr[i,j]))} for i,j in zip(row,col)]
        report={'results':results,'complete':True,'matched_topographies':matches,'interpretation':'Spatial matches only, sign-invariant; not proof of brain sources or FC reliability. No IC exclusion/backprojection applied.'}
        (out/'comparison.json').write_text(json.dumps(report,indent=2))
        print('COMPLETE '+str(out),flush=True)
    finally:
        ica_mod.infomax=original

if __name__=='__main__':main()
