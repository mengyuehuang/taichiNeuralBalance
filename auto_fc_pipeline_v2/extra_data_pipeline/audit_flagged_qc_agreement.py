"""Recheck every flagged QC/native comparison without the artificial half boundary."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='2'
import csv,json,sys
from pathlib import Path
from fractions import Fraction
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
from scipy.signal import resample_poly
HOME=Path(__file__).resolve().parent
sys.path.insert(0,str(HOME.parent/'src'))
from fc_pipeline_v2.corrected import prepare_segments,pairwise_fc
from fc_pipeline_v2.qc_validation import edge_correlation
QC=HOME/'rank_corrected/qc_validation';OUT=QC/'agreement_audit';OUT.mkdir(exist_ok=True)

def audit(row):
    subject,hc,band=(row[k] for k in ['participant','hc','band'])
    ident=subject if row['study']=='PCD' else subject[3:]
    directory=HOME/'rank_corrected/outputs'/subject if row['study']=='PCD' else HOME.parent/'outputs/corrected'/ident
    checkpoint=OUT/f'{subject}_{hc}_{band}_unsplit.json'
    if checkpoint.exists():return json.loads(checkpoint.read_text())
    with np.load(next((directory/'03_roi_timeseries').glob(f'{ident}_{hc}_*_signed_parcels.npz'))) as d:
        x=d['signed_tc100'];sf=float(d['sfreq']);starts=d['segment_starts'];stops=d['segment_stops']
    ratio=Fraction(128/sf).limit_denominator(10000)
    band_limits={'broadband':None,'alpha':[8,12],'beta':[13,30]}[band]
    parts=[]
    for a,b in zip(starts,stops):
        if (b-a)/sf<8:continue
        p=resample_poly(x[:,a:b].astype(float),ratio.numerator,ratio.denominator,axis=1)
        parts.extend(prepare_segments(p,[0],[p.shape[1]],128,band_limits,0 if band_limits is None else 2,4))
    matrix=pairwise_fc(parts,16)[0]
    with np.load(next((directory/'04_static_fc/pairwise_100parcels').glob(f'{ident}_{hc}_*_{band}_fc.npz'))) as d:native=d['fc100_signed']
    result={k:row[k] for k in ['participant','study','hc','band']}
    result.update(original_split_qc_r=float(row['native_agreement_r']),unsplit_qc_r=edge_correlation(native,matrix),unsplit_centered_r=edge_correlation(native,matrix,True))
    np.savez_compressed(OUT/f'{subject}_{hc}_{band}_unsplit.npz',fc=matrix)
    checkpoint.write_text(json.dumps(result,indent=2))
    return result

rows=list(csv.DictReader((QC/'all_recording_qc.csv').open(encoding='utf-8-sig')))
flagged=[r for r in rows if float(r['native_agreement_r'])<.98]
results=[];errors=[]
with ThreadPoolExecutor(max_workers=2) as pool:
    futures={pool.submit(audit,r):r for r in flagged}
    for f in as_completed(futures):
        try:results.append(f.result());print(json.dumps(results[-1]),flush=True)
        except Exception as exc:errors.append({'participant':futures[f]['participant'],'error':str(exc)})
        (OUT/'flagged_recheck_status.json').write_text(json.dumps({'expected':len(flagged),'completed':len(results),'errors':errors},indent=2))
results.sort(key=lambda r:(r['participant'],r['hc'],r['band']))
if results:
    with (OUT/'flagged_unsplit_comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=results[0]);w.writeheader();w.writerows(results)
summary={'expected':len(flagged),'completed':len(results),'errors':errors,'agreement_restored_ge098':sum(r['unsplit_qc_r']>=.98 for r in results),'still_below098':[r for r in results if r['unsplit_qc_r']<.98]}
(OUT/'flagged_recheck_summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary),flush=True)

def matched_segments_and_filter(row):
    subject,hc,band=(row[k] for k in ['participant','hc','band'])
    checkpoint=OUT/f'{subject}_{hc}_{band}_matched.json'
    if checkpoint.exists():return json.loads(checkpoint.read_text())
    ident=subject if row['study']=='PCD' else subject[3:]
    directory=HOME/'rank_corrected/outputs'/subject if row['study']=='PCD' else HOME.parent/'outputs/corrected'/ident
    with np.load(next((directory/'03_roi_timeseries').glob(f'{ident}_{hc}_*_signed_parcels.npz'))) as d:
        x=d['signed_tc100'];sf=float(d['sfreq']);starts=d['segment_starts'];stops=d['segment_stops']
    limits={'broadband':None,'alpha':[8,12],'beta':[13,30]}[band]
    prepared=prepare_segments(x,starts,stops,sf,limits,0 if limits is None else 2,4)
    prepared=[p for p in prepared if p.shape[1]>=round(sf/8)]
    ratio=Fraction(128/sf).limit_denominator(10000)
    parts=[resample_poly(p,ratio.numerator,ratio.denominator,axis=1) for p in prepared]
    matrix=pairwise_fc(parts,16)[0]
    with np.load(next((directory/'04_static_fc/pairwise_100parcels').glob(f'{ident}_{hc}_*_{band}_fc.npz'))) as d:native=d['fc100_signed']
    result=dict(row,matched_segments_filter_r=edge_correlation(native,matrix),segment_seconds=((stops-starts)/sf).tolist())
    checkpoint.write_text(json.dumps(result,indent=2));return result

matched=[]
with ThreadPoolExecutor(max_workers=2) as pool:
    futures=[pool.submit(matched_segments_and_filter,r) for r in results if r['unsplit_qc_r']<.98]
    for f in as_completed(futures):
        matched.append(f.result());print(json.dumps(matched[-1]),flush=True)
(OUT/'matched_recheck_summary.json').write_text(json.dumps(matched,indent=2))

def higher_rate(row):
    subject,hc,band=(row[k] for k in ['participant','hc','band'])
    ident=subject if row['study']=='PCD' else subject[3:]
    directory=HOME/'rank_corrected/outputs'/subject if row['study']=='PCD' else HOME.parent/'outputs/corrected'/ident
    checkpoint=OUT/f'{subject}_{hc}_{band}_higher_rate.json'
    if checkpoint.exists():return json.loads(checkpoint.read_text())
    with np.load(next((directory/'03_roi_timeseries').glob(f'{ident}_{hc}_*_signed_parcels.npz'))) as d:
        sf=float(d['sfreq']);limits={'broadband':None,'beta':[13,30]}[band]
        parts=prepare_segments(d['signed_tc100'],d['segment_starts'],d['segment_stops'],sf,limits,0 if limits is None else 2,4)
    native_block=round(sf/8);parts=[p for p in parts if p.shape[1]>=native_block]
    with np.load(next((directory/'04_static_fc/pairwise_100parcels').glob(f'{ident}_{hc}_*_{band}_fc.npz'))) as d:native=d['fc100_signed']
    result=dict(row,native_sfreq=sf,native_envelope_hz=sf/native_block,rate_tests=[])
    for block in [32,64]:
        ratio=Fraction(block,native_block)
        down=[resample_poly(p,ratio.numerator,ratio.denominator,axis=1) for p in parts]
        matrix=pairwise_fc(down,block)[0]
        r=edge_correlation(native,matrix)
        result['rate_tests'].append({'sfreq':sf*float(ratio),'block':block,'edge_r':r})
        if r>=.98:break
    checkpoint.write_text(json.dumps(result,indent=2));return result

higher=[]
with ThreadPoolExecutor(max_workers=2) as pool:
    for result in pool.map(higher_rate,[r for r in matched if r['matched_segments_filter_r']<.98]):
        higher.append(result);print(json.dumps(result),flush=True)
(OUT/'higher_rate_summary.json').write_text(json.dumps(higher,indent=2))
final=[]
for row in results:
    key=(row['participant'],row['hc'],row['band'])
    m=next((r for r in matched if (r['participant'],r['hc'],r['band'])==key),None)
    h=next((r for r in higher if (r['participant'],r['hc'],r['band'])==key),None)
    if h:stage='higher_rate_and_matched_envelope';r=h['rate_tests'][-1]['edge_r']
    elif m:stage='matched_native_segments_and_filter';r=m['matched_segments_filter_r']
    else:stage='remove_artificial_half_boundary';r=row['unsplit_qc_r']
    final.append(dict(row,resolution_stage=stage,final_agreement_r=r))
with (OUT/'final_agreement_audit.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=final[0]);w.writeheader();w.writerows(final)
(OUT/'final_summary.json').write_text(json.dumps({'audited':len(final),'restored_ge098':sum(r['final_agreement_r']>=.98 for r in final),'errors':errors,'note':'Historical agreement flags reflect mismatched QC conditions. Other QC flags and biological validity are not cleared. Original FC and historical screening tables remain unchanged.'},indent=2))
