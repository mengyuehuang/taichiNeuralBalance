"""Summarize QC and create HC descriptive group matrices with source provenance."""
from pathlib import Path
import os,sys,json,csv
os.environ.setdefault('MPLBACKEND','Agg')
ROOT=Path(__file__).resolve().parents[2];HOME=Path(__file__).resolve().parent
OUT=HOME/'rank_corrected/qc_validation'
sys.path.insert(0,str(ROOT/'auto_fc_pipeline_v2/src'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from fc_pipeline_v2.qc_validation import double_center,fisher,edge_correlation,screen
from fc_pipeline_v2.corrected import NETWORK_ORDER


def csv_write(path,rows):
    if not rows:return
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)


def draw(matrices,counts,names,path,title,footnote):
    network=np.array([n.split('_')[2] for n in names]);hemi=np.array([n.split('_')[1] for n in names])
    starts=np.flatnonzero(np.r_[True,(network[1:]!=network[:-1])|(hemi[1:]!=hemi[:-1])]);ends=np.r_[starts[1:],100]
    mid=(starts+ends-1)/2;labels=[f'{hemi[i]} {network[i]}' for i in starts]
    iu=np.triu_indices(100,1)
    values=np.concatenate([np.abs(m[iu]) for m in matrices.values()]) if matrices else np.array([.05])
    limit=max(float(np.nanpercentile(values,99)),1e-4)
    fig,axes=plt.subplots(1,3,figsize=(17,6))
    titles={'YAC':'Younger Adult Controls','OAC':'Older Adult Controls','TCOA':'Tai Chi Older Adult Practitioners'}
    image=None
    for ax,group in zip(axes,['YAC','OAC','TCOA']):
        if group not in matrices:
            ax.text(.5,.5,'No eligible participants\nunder this QC screen',ha='center',va='center',transform=ax.transAxes);ax.axis('off');continue
        image=ax.imshow(matrices[group],cmap='RdBu_r',vmin=-limit,vmax=limit,interpolation='nearest')
        ax.xaxis.tick_top();ax.set_xticks(mid,labels,rotation=90,fontsize=6);ax.set_yticks(mid,labels,fontsize=6)
        ax.set_xlabel(f'{titles[group]}\nn={counts[group]} participants',fontsize=10)
    if image is not None:
        fig.colorbar(image,ax=list(axes),fraction=.02,pad=.02,label='Fisher z relative to participant brain-wide pattern')
    fig.suptitle(title,fontsize=14)
    fig.text(.05,.015,footnote,fontsize=8)
    fig.subplots_adjust(left=.06,right=.88,top=.73,bottom=.13,wspace=.36)
    fig.savefig(path,dpi=180,bbox_inches='tight');plt.close(fig)


def main():
    global OUT
    # Preserve historical QC checkpoints and summaries. Updated teacher-cohort
    # summaries are a separate view, never a rewrite of the original QC run.
    source_out=OUT
    # Older running QC batches may have been started before the sensitivity
    # stage was added; final aggregation must still wait for that stage.
    if not (OUT/'threshold_sensitivity/summary.json').exists() or json.loads((OUT/'threshold_sensitivity/summary.json').read_text()).get('qc_policy_version')!=3:
        import subprocess
        subprocess.run([sys.executable,str(HOME/'threshold_sensitivity.py')],cwd=ROOT,check=True)
    reports=[json.loads(p.read_text()) for p in sorted(OUT.glob('*/qc_results.json'))]
    if any(r.get('qc_policy_version')!=3 for r in reports):
        raise ValueError('Complete version 3 QC refresh before regenerating summaries')
    from fc_pipeline_v2.cohort_policy import is_excluded, participant_decision, DEFAULT_POLICY
    excluded=[r['participant'] for r in reports if is_excluded(r['participant'])]
    reports=[r for r in reports if not is_excluded(r['participant'])]
    OUT=source_out/'teacher_cohort'
    OUT.mkdir(exist_ok=True)
    (OUT/'cohort_provenance.json').write_text(json.dumps({'policy':json.loads(DEFAULT_POLICY.read_text()),'source_qc':str(source_out),'excluded_existing_reports':excluded,'note':'Retained does not mean QC-approved. Existing legacy TCP rank policy remains unchanged; identity warnings do not resolve independence.'},indent=2),encoding='utf-8')
    for report in reports:
        (OUT/report['participant']).mkdir(exist_ok=True)
        report['teacher_cohort_decision']=participant_decision(report['participant'])
    # Reapply current exploratory policy to all checkpoints, including the pilot
    # and checkpoints made before the residual-line-power flag was introduced.
    for report in reports:
        for row in report['rows']:
            status,reasons=screen({k:(float('nan') if v is None and k in ['native_agreement_r','split_half_centered_r'] else v) for k,v in row.items()})
            if report['study']=='TCP':reasons.append('legacy_source_rank_policy_not_harmonized')
            if len({row.get(k) for k in ['pooled_rank_tol_1e5','pooled_rank_tol_1e6','pooled_rank_tol_1e7']})>1:reasons.append('pooled_rank_threshold_sensitive')
            row['status']='review_required' if reasons and status!='unusable' else status
            row['reasons']=';'.join(reasons)
        report['qc_policy_version']=3
        path=OUT/report['participant']
        (path/'qc_results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        csv_write(path/'qc_metrics.csv',report['rows'])
    rows=[r for report in reports for r in report['rows']]
    csv_write(OUT/'all_recording_qc.csv',rows)
    csv_write(OUT/'technical_candidate_results.csv',[r for r in rows if r['status']=='technical_candidate'])
    eligibility=[]
    for report in reports:
        for band in ['broadband','alpha','beta']:
            available=[r for r in report['rows'] if r['band']==band]
            accepted=[r['hc'] for r in available if r['status']=='technical_candidate']
            held=[r['hc'] for r in available if r['status']!='technical_candidate']
            eligibility.append(dict(participant=report['participant'],study=report['study'],group=report['group'],band=band,technical_candidate_blocks=';'.join(accepted),review_blocks=';'.join(held),missing_blocks=';'.join(hc for hc in ['HC1','HC2','HC3','HC4'] if hc not in {r['hc'] for r in available}),all_HC_candidate=len(accepted)==4,non_perturbation_candidate=all(hc in accepted for hc in ['HC1','HC4']),perturbation_candidate=all(hc in accepted for hc in ['HC2','HC3']),formal_statistics_approved=False))
    csv_write(OUT/'usable_results_by_participant_band.csv',eligibility)
    groups=OUT/'group_figures';groups.mkdir(exist_ok=True)
    # Remove only this summarizer's generated files so empty updated groups
    # cannot leave obsolete candidate figures or arrays behind.
    for pattern in ['all_available_descriptive_*','technical_candidates_*']:
        for old in groups.glob(pattern):
            if old.is_file() and old.suffix in ['.png','.npz','.csv']:old.unlink()
    native={};names=None;participants=[]
    for report in reports:
        sid=report['participant'];study=report['study'];source=Path(report['source_directory'])/'04_static_fc/pairwise_100parcels'
        ident=sid[3:] if study=='TCP' else sid
        selected={};flags=set()
        for row in report['rows']:
            hc,band=row['hc'],row['band']
            files=list(source.glob(f'{ident}_{hc}_*_{band}_fc.npz'))
            if len(files)!=1:continue
            with np.load(files[0]) as d:
                current=d['parcel_names'].astype(str).tolist()
                if names is None:names=current
                if current!=names:raise ValueError('Cross-participant parcel mismatch')
                native[(sid,hc,band)]=d['fc100_signed'].copy()
            selected[(hc,band)]=row
            flags.update(filter(None,row.get('reasons','').split(';')))
        complete=all((hc,band) in selected for hc in ['HC1','HC2','HC3','HC4'] for band in ['broadband','alpha','beta'])
        participants.append({'participant':sid,'study':study,'group':report['group'],'complete_four_HC':complete,'technical_candidate_all_available_bands':all(r['status']=='technical_candidate' for r in selected.values()) and bool(selected),'flags':';'.join(sorted(flags)),'minimum_centered_split_r':min((r['split_half_centered_r'] for r in selected.values() if r['split_half_centered_r'] is not None),default=None),'rank_min':min((r['sensor_rank'] for r in selected.values()),default=None)})
    csv_write(OUT/'participant_qc_decisions.csv',participants)
    sensitivity=[]
    for threshold in [.3,.5,.7]:
        for study in ['PCD','TCP']:
            for band in ['broadband','alpha','beta']:
                candidates=[r for r in rows if r['study']==study and r['band']==band]
                sensitivity.append({'study':study,'band':band,'centered_split_r_cutoff':threshold,'rows_evaluated':len(candidates),'rows_meeting_temporal_cutoff':sum(r['split_half_centered_r'] is not None and r['split_half_centered_r']>=threshold for r in candidates),'note':'Temporal criterion only; other quality gates still apply'})
    csv_write(OUT/'screen_cutoff_sensitivity.csv',sensitivity)
    counts=[];reliability=[];features=[]
    for band in ['broadband','alpha','beta']:
        for condition,blocks in [('all_HC',['HC1','HC2','HC3','HC4']),('non_perturbation',['HC1','HC4']),('perturbation',['HC2','HC3'])]:
            for selection in ['all_available_descriptive','technical_candidates']:
                subjects={};by_group={g:[] for g in ['YAC','OAC','TCOA']}
                for report in reports:
                    sid=report['participant'];group=report['group']
                    block_rows=[next((r for r in report['rows'] if r['hc']==hc and r['band']==band),None) for hc in blocks]
                    if any(r is None for r in block_rows):continue
                    if selection=='technical_candidates' and any(r['status']!='technical_candidate' for r in block_rows):continue
                    z=np.mean([fisher(native[(sid,hc,band)]) for hc in blocks],axis=0)
                    np.fill_diagonal(z,np.nan)
                    centered=double_center(z)
                    subjects[sid]=centered;by_group[group].append((sid,z,centered))
                    iu=np.triu_indices(100,1)
                    features.append({'participant':sid,'study':report['study'],'group':group,'band':band,'condition':condition,'selection':selection,'mean_uncentered_fisher_z':float(np.mean(z[iu])),'minimum_rank':min(r['sensor_rank'] for r in block_rows)})
                matrices={};group_counts={}
                for group,items in by_group.items():
                    if not items:continue
                    matrices[group]=np.mean([x[2] for x in items],axis=0);group_counts[group]=len(items)
                    cohorts={k:sum(next(r for r in reports if r['participant']==x[0])['study']==k for x in items) for k in ['PCD','TCP']}
                    counts.append({'selection':selection,'band':band,'condition':condition,'group':group,'participants':len(items),'PCD':cohorts['PCD'],'TCP':cohorts['TCP']})
                    prefix=f'{selection}_{condition}_{band}_{group}'
                    np.savez_compressed(groups/f'{prefix}.npz',centered_fisher_z=matrices[group],uncentered_fisher_z=np.mean([x[1] for x in items],axis=0),participant_ids=np.array([x[0] for x in items]),parcel_names=np.array(names))
                    np.savetxt(groups/f'{prefix}_centered_z.csv',matrices[group],delimiter=',')
                    if len(items)>=4:
                        iu=np.triu_indices(100,1);v=np.array([x[2][iu] for x in items]);rng=np.random.default_rng(2026)
                        loo=[np.corrcoef(v[i],np.delete(v,i,axis=0).mean(0))[0,1] for i in range(len(v))]
                        split=[]
                        for _ in range(200):
                            order=rng.permutation(len(v));half=len(v)//2
                            split.append(np.corrcoef(v[order[:half]].mean(0),v[order[half:]].mean(0))[0,1])
                        reliability.append({'selection':selection,'band':band,'condition':condition,'group':group,'n':len(items),'group_subject_split_r_median':float(np.median(split)),'group_subject_split_r_p025':float(np.percentile(split,2.5)),'group_subject_split_r_p975':float(np.percentile(split,97.5)),'leave_one_out_r_median':float(np.median(loo))})
                if matrices:
                    draw(matrices,group_counts,names,groups/f'{selection}_{condition}_{band}.png',f'HC functional connectivity | {condition} | {band} | {selection.replace("_"," ")}', 'DESCRIPTIVE ONLY. HC task, not reference EC/EO. Participants equally weighted; matched blocks required. TCP source pipeline remains unharmonized.')
    csv_write(OUT/'group_sample_counts.csv',counts);csv_write(OUT/'group_reliability.csv',reliability)
    csv_write(OUT/'participant_group_features.csv',features)
    associations=[]
    for study in ['PCD','TCP']:
        for band in ['broadband','alpha','beta']:
            f=[x for x in features if x['study']==study and x['band']==band and x['selection']=='all_available_descriptive' and x['condition']=='all_HC']
            if len(f)>=5 and len({x['minimum_rank'] for x in f})>1:
                stat=spearmanr([x['minimum_rank'] for x in f],[x['mean_uncentered_fisher_z'] for x in f])
                associations.append({'study':study,'band':band,'n':len(f),'rank_vs_mean_FC_spearman':float(stat.statistic),'note':'Descriptive dependence check; not a group-effect test'})
    csv_write(OUT/'rank_fc_associations.csv',associations)
    summary={'participants_completed_qc':len(reports),'recording_band_rows':len(rows),'technical_candidate_rows':sum(r['status']=='technical_candidate' for r in rows),'review_required_rows':sum(r['status']=='review_required' for r in rows),'error_files':[p.name for p in OUT.glob('*_error.txt')],'formal_group_statistics_ready':False,'blocking_reasons':['100-parcel method is visualization/QC in supplied reference; confirm intended inferential endpoint','Legacy TCP source rank policy and threshold sensitivity not harmonized with corrected PCD','Cross-study participant overlap and protocol equivalence not confirmed','Screening cutoffs are operational choices, not validated universal acceptance rules','Waveform/PSD plots require human inspection; automated screens cannot establish artifact-free recordings'],'reference':'references/Step0b_Connectome_Sanity_Check_100parcels.ipynb; reference analyzes EC/EO, current outputs are HC','figure_directory':str(groups.resolve())}
    summary['blocking_reasons']=[r.replace('Cross-study participant overlap and protocol equivalence not confirmed','Participant identity overlap unresolved; matching HC protocols confirmed by teacher') for r in summary['blocking_reasons']]
    summary['excluded_existing_reports']=excluded
    summary['teacher_policy_version']=1
    summary['quality_note_participants']=[r['participant'] for r in reports if participant_decision(r['participant']).get('quality_review_required')]
    (OUT/'validation_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    summary.update(qc_policy_version=3,participants_with_any_technical_candidate=sum(any(r['status']=='technical_candidate' for r in report['rows']) for report in reports),participants_all_available_rows_candidate=sum(all(r['status']=='technical_candidate' for r in report['rows']) for report in reports),unusable_rows=sum(r['status']=='unusable' for r in rows),native_agreement_failed_rows=sum(r['native_agreement_r'] is None or r['native_agreement_r']<.98 for r in rows))
    (OUT/'validation_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
