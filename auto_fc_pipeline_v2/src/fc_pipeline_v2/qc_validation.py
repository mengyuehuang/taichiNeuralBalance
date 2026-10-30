"""Independent QC helpers; operational screens are not biological acceptance rules."""
import numpy as np
from scipy.signal import hilbert
from .corrected import smooth_segments, standardize, pairwise_fc, prepare_segments
from scipy.signal import resample_poly
from fractions import Fraction


def prepare_qc_segments(x, starts, stops, sfreq, band=None, minimum_sfreq=256):
    """Match native filtering, segment eligibility and actual envelope interval."""
    native_block=max(1,round(sfreq/8))
    parts=prepare_segments(x,starts,stops,sfreq,band,0 if band is None else 2,4)
    parts=[p for p in parts if p.shape[1]>=native_block]
    block=min(native_block,max(1,int(np.ceil(minimum_sfreq/(sfreq/native_block)))))
    ratio=Fraction(block,native_block)
    rate=sfreq*float(ratio)
    return [resample_poly(p,ratio.numerator,ratio.denominator,axis=1) if ratio!=1 else p for p in parts],rate,block


def fisher(matrix):
    return np.arctanh(np.clip(matrix,-.999999,.999999))


def double_center(matrix):
    z=np.array(matrix,dtype=float,copy=True)
    np.fill_diagonal(z,np.nan)
    row=np.nanmean(z,axis=1)
    out=z-row[:,None]-row[None,:]+np.nanmean(z)
    np.fill_diagonal(out,np.nan)
    return out


def edge_correlation(a,b,center=False):
    if center:a,b=double_center(fisher(a)),double_center(fisher(b))
    ix=np.triu_indices(len(a),1)
    x,y=a[ix],b[ix]
    if not np.isfinite(x).all() or not np.isfinite(y).all() or x.std()==0 or y.std()==0:return float('nan')
    return float(np.corrcoef(x,y)[0,1])


def split_parts(parts):
    """Chronological split at half of retained sample count, preserving boundaries."""
    midpoint=sum(p.shape[1] for p in parts)//2
    halves=[[],[]];offset=0
    for p in parts:
        cut=max(0,min(p.shape[1],midpoint-offset))
        if cut:halves[0].append(p[:,:cut])
        if cut<p.shape[1]:halves[1].append(p[:,cut:])
        offset+=p.shape[1]
    return halves


def pairwise_split_fc(parts,block=16):
    """Exact pairwise math on QC-rate data, with independent half Hilbert transforms.

    Return independently computed unsplit full FC and two half matrices.
    Never use envelopes transformed separately in halves as full-recording FC.
    """
    halves=split_parts(parts);z=[];counts=[]
    for half in halves:
        half=[p for p in half if p.shape[1]>=block]
        if not half:raise ValueError('Insufficient samples in one half')
        mean=sum(p.sum(1,keepdims=True) for p in half)/sum(p.shape[1] for p in half)
        analytic=[hilbert(p-mean,axis=1) for p in half]
        z.extend(analytic)
        counts.append(sum(p.shape[1]//block for p in analytic))
    envelope=smooth_segments([np.abs(p) for p in z],block)
    sections=[slice(None),slice(0,counts[0]),slice(counts[0],sum(counts))]
    seeds=[standardize(envelope[:,section]) for section in sections]
    n=envelope.shape[0];matrices=[np.zeros((n,n)) for _ in sections]
    for i in range(n):
        others=np.arange(n)!=i
        orth=[]
        for part in z:
            amp=np.abs(part[i])
            if np.any(amp==0):raise ValueError('Zero seed amplitude')
            orth.append(np.abs(np.imag(part[others]*(part[i].conj()/amp))))
        target=smooth_segments(orth,block)
        for out,seed,section in zip(matrices,seeds,sections):
            out[i,others]=standardize(target[:,section])@seed[i]/seed.shape[1]
    for out in matrices:
        out[:]=(out+out.T)/2
        np.fill_diagonal(out,1)
    matrices[0]=pairwise_fc(parts,block)[0]
    return matrices,counts


def screen(metrics):
    """Conservative prereported operational flags, independent of group patterns."""
    reasons=[]
    if not metrics.get('finite',False):return 'unusable',['nonfinite_input']
    if metrics.get('matrix_error'):return 'unusable',['matrix_or_processing_failure']
    if metrics['clean_seconds']<120:reasons.append('clean_duration_lt120s')
    if metrics['half_seconds_min']<60:reasons.append('half_duration_lt60s')
    if metrics['sensor_rank']<6:reasons.append('very_low_rank_lt6')
    if metrics['flat_channels']:reasons.append('flat_channel')
    if metrics['peak_to_peak_uv']>500:reasons.append('large_peak_to_peak_gt500uV')
    if metrics['high_frequency_fraction']>.5:reasons.append('high_35to55Hz_fraction')
    if metrics.get('line60_fraction',0)>.1:reasons.append('residual_60Hz_power_gt10pct_of_1to55Hz')
    if not metrics['threshold_stable']:reasons.append('rank_threshold_sensitive')
    if not np.isfinite(metrics['native_agreement_r']) or metrics['native_agreement_r']<.98:reasons.append('QC_vs_native_FC_agreement_lt0.98')
    if not np.isfinite(metrics['split_half_centered_r']) or metrics['split_half_centered_r']<.5:reasons.append('temporal_split_centered_r_lt0.5')
    return ('review_required' if reasons else 'technical_candidate'),reasons
