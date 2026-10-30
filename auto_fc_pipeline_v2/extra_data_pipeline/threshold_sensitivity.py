"""Rebuild alternative inverse/FC only where rank thresholds change the model."""
from pathlib import Path
import json,sys
import run_qc_validation as qc
import numpy as np
from fractions import Fraction
from scipy.signal import resample_poly
import mne
from fc_pipeline_v2.signal_rank import project_numerical_residue,signal_basis
from fc_pipeline_v2.corrected import continuous_segments,prepare_segments,pairwise_fc
from fc_pipeline_v2.qc_validation import prepare_qc_segments,edge_correlation,fisher


def main():
    mne.set_log_level('ERROR');home=qc.HOME;out=qc.OUT/'threshold_sensitivity';out.mkdir(exist_ok=True)
    cfg=json.loads((home/'rank_corrected/config.rank_corrected.json').read_text())
    rows=[];unchanged=[]
    for task in qc.participants():
        study,sid,paths,directory=task
        if study!='PCD':continue
        audit=json.loads((directory/'02_source_model/signal_rank_audit.json').read_text())
        sensitive=any(len({int((np.array(v['relative_singular_values'])>tol).sum()) for tol in [1e-5,1e-6,1e-7]})>1 for v in audit.values() if isinstance(v,dict))
        if not sensitive:
            unchanged.append(sid);continue
        report=out/f'{sid}_sensitivity.json'
        if report.exists() and json.loads(report.read_text()).get('qc_policy_version')==3:
            rows.extend(json.loads(report.read_text())['rows']);continue
        print(f'{sid}: rebuilding 1e-7 sensitivity inverse',flush=True)
        try:
            raws=[];rank_audit={}
            for p in paths:
                raw=mne.io.read_raw_fif(p,preload=True,verbose='ERROR');raw.pick('eeg');raw.set_eeg_reference('average',projection=True,verbose='ERROR');raw.apply_proj(verbose='ERROR')
                rank_audit[p.name]=project_numerical_residue(raw,1e-7);raws.append(raw)
            sample=np.concatenate([r.get_data()[:,::max(1,r.n_times//3000)] for r in raws],axis=1)
            basis,_=signal_basis(sample,1e-7,max_samples=sample.shape[1]);rank={'eeg':basis.shape[1]}
            combined=mne.concatenate_raws([r.copy() for r in raws],verbose='ERROR')
            cov=mne.compute_raw_covariance(combined,method=cfg['source_localization']['covariance_method'],rank=rank,verbose='ERROR')
            del combined
            fwd=mne.read_forward_solution(directory/'02_source_model'/f'{sid}_forwardsolution_fsaverage.fif',verbose='ERROR')
            inv=mne.minimum_norm.make_inverse_operator(raws[0].info,fwd,cov,loose=.2,depth=.8,rank=rank,verbose='ERROR')
            labels=[l for l in mne.read_labels_from_annot('fsaverage',parc=cfg['parcel_extraction']['parc'],subjects_dir=cfg['paths']['subjects_dir'],verbose='ERROR') if not l.name.startswith('Background') and 'unknown' not in l.name.lower()]
            labels.sort(key=lambda l:(l.name.split('_')[1],qc.NETWORK_ORDER.index(l.name.split('_')[2]),l.name))
            kernel,error=qc.make_kernel(raws[0],inv,labels)
            subject_rows=[]
            for raw,p in zip(raws,paths):
                hc=__import__('re').search(r'HC[1-4]',p.name)[0];sf=raw.info['sfreq'];x=raw.get_data()
                valid=np.isfinite(raw.get_data(reject_by_annotation='NaN')).all(0);boundary=np.zeros(raw.n_times,dtype=bool);boundary[0]=True
                for onset,desc in zip(raw.annotations.onset,raw.annotations.description):
                    if 'boundary' in str(desc).lower() or str(desc).lower().startswith('edge'):
                        index=round((onset-raw.first_time)*sf)
                        if 0<=index<raw.n_times:boundary[index]=True
                starts,stops=continuous_segments(valid,boundary)
                source=kernel@x
                for band,limits in qc.POLICY['bands'].items():
                    baseline=qc.OUT/sid/f'{hc}_{band}_split_fc.npz'
                    with np.load(baseline) as d:
                        if int(d['qc_policy_version'])!=3:raise ValueError('Complete QC v3 refresh first')
                        nominal=d['qc_full'];nominal_rate=float(d['qc_sfreq'])
                    prepared,rate,block=prepare_qc_segments(source,starts,stops,sf,limits,nominal_rate-1e-6)
                    alt=pairwise_fc(prepared,block)[0]
                    iu=np.triu_indices(100,1)
                    row=dict(participant=sid,hc=hc,band=band,nominal_tolerance=1e-6,alternative_tolerance=1e-7,alternative_pooled_rank=rank['eeg'],alternative_block_rank=rank_audit[p.name]['rank'],fc_edge_r=edge_correlation(nominal,alt),fc_centered_edge_r=edge_correlation(nominal,alt,True),fisher_z_mae=float(np.abs(fisher(nominal)[iu]-fisher(alt)[iu]).mean()),kernel_relative_error=error)
                    subject_rows.append(qc.safe_metrics(row))
                    np.savez_compressed(out/f'{sid}_{hc}_{band}_tol1e7_fc.npz',alternative_qc_full=alt,nominal_qc_full=nominal)
                raw.close()
            qc.save_json(report,{'status':'completed','rows':subject_rows,'rank_audit':rank_audit,'qc_policy_version':3});rows.extend(subject_rows)
        except Exception as exc:
            qc.save_json(out/f'{sid}_error.json',{'status':'failed','error':str(exc)})
            print(f'{sid}: sensitivity failed: {exc}',flush=True)
    qc.write_csv(qc.OUT/'threshold_FC_sensitivity.csv',rows)
    qc.save_json(out/'summary.json',{'qc_policy_version':3,'unchanged_block_rank_participants':unchanged,'full_alternative_inverse_rows':len(rows),'alternative_model_errors':[p.name for p in out.glob('*_error.json')],'note':'Matched QC v3 sampling, native filtering and native segment eligibility for both models. 1e-5 and 1e-6 block bases agree in supplied PCD rank audits. Unchanged block bases require pooled rank checks too.'})


if __name__=='__main__':main()
