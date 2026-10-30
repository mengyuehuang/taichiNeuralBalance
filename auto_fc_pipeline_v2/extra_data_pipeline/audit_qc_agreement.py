"""Isolate sampling, filtering, segment selection and split-boundary effects."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[key]='2'
import sys,json
from pathlib import Path
from fractions import Fraction
import numpy as np
from scipy.signal import resample_poly
HOME=Path(__file__).resolve().parent
sys.path.insert(0,str(HOME.parent/'src'))
from fc_pipeline_v2.corrected import prepare_segments,pairwise_fc
from fc_pipeline_v2.qc_validation import split_parts,edge_correlation

def historical_split_pool(parts,block):
    """Reproduce the superseded v2 comparison for this diagnostic only."""
    centered=[]
    for half in split_parts(parts):
        half=[p for p in half if p.shape[1]>=block*2]
        mean=sum(p.sum(1,keepdims=True) for p in half)/sum(p.shape[1] for p in half)
        centered.extend(p-mean for p in half)
    return pairwise_fc(centered,block)[0]

OUT=HOME/'rank_corrected/qc_validation/agreement_audit'
OUT.mkdir(exist_ok=True)
cases=[('PCD119','HC4','beta'),('PCD101','HC4','beta'),('PCD105','HC1','broadband'),('TCP104','HC1','broadband')]
rows=json.loads((OUT/'results.json').read_text()) if (OUT/'results.json').exists() else []
for subject,hc,band in cases:
    if sum(r['subject']==subject and r['hc']==hc and r['band']==band for r in rows)==5:continue
    ident=subject if subject.startswith('PCD') else subject[3:]
    directory=HOME/'rank_corrected/outputs'/subject if subject.startswith('PCD') else HOME.parent/'outputs/corrected'/ident
    file=next((directory/'03_roi_timeseries').glob(f'{ident}_{hc}_*_signed_parcels.npz'))
    native_file=next((directory/'04_static_fc/pairwise_100parcels').glob(f'{ident}_{hc}_*_{band}_fc.npz'))
    with np.load(native_file) as d:native=d['fc100_signed'].copy()
    with np.load(file) as d:
        x=d['signed_tc100'].astype(float);sf=float(d['sfreq']);starts=d['segment_starts'];stops=d['segment_stops']
    limits={'beta':[13,30],'broadband':None}[band];trim=0 if limits is None else 2
    ratio=Fraction(128/sf).limit_denominator(10000)
    def down(p):return resample_poly(p,ratio.numerator,ratio.denominator,axis=1)
    def record(name,matrix):
        row=dict(subject=subject,hc=hc,band=band,variant=name,edge_r=edge_correlation(native,matrix),centered_r=edge_correlation(native,matrix,True),max_abs_difference=float(np.max(np.abs(native-matrix))))
        rows.append(row);print(json.dumps(row),flush=True)
        (OUT/'results.json').write_text(json.dumps(rows,indent=2))
        np.savez_compressed(OUT/f'{subject}_{hc}_{band}_{name}.npz',fc=matrix)
    prepared=prepare_segments(x,starts,stops,sf,limits,trim,4)
    record('native_exact_replay',pairwise_fc(prepared,round(sf/8))[0])
    prepared_down=[down(p) for p in prepared]
    record('filter_native_then_downsample',pairwise_fc(prepared_down,16)[0])
    raw_down=[down(x[:,a:b]) for a,b in zip(starts,stops) if (b-a)/sf>=8]
    qc_parts=[]
    for p in raw_down:qc_parts.extend(prepare_segments(p,[0],[p.shape[1]],128,limits,trim,4))
    record('qc_rate_without_half_split',pairwise_fc(qc_parts,16)[0])
    record('qc_rate_with_half_split',historical_split_pool(qc_parts,16))
    with np.load(HOME/'rank_corrected/qc_validation'/subject/f'{hc}_{band}_split_fc.npz') as d:
        saved=d['qc_full'].copy()
    record('saved_qc_kernel_route',saved)
print('Agreement audit completed',flush=True)
