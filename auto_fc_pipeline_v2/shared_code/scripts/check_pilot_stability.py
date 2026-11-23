"""Check saved common-inverse pilot FC against chronological retained halves."""
import argparse
import csv
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'shared_code/src'))
os.environ.setdefault('_MNE_FAKE_HOME_DIR',str(ROOT.parent/'.mne_fake_home'))
os.environ['MNE_USE_NUMBA']='false'
import mne
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import welch
from fc_pipeline_v2.corrected import prepare_segments, symmetric_fc
from fc_pipeline_v2.qc_validation import split_parts, edge_correlation, prepare_qc_segments, pairwise_split_fc


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    parser.add_argument('participant')
    args=parser.parse_args()
    config_path=args.run/'config.local.json'
    config=json.loads(config_path.read_text(encoding='utf-8-sig')) if config_path.exists() else {}
    source_config=config.get('source_localization',{})
    d=args.run/'outputs'/args.participant
    out=args.run/'quality_review'
    out.mkdir(exist_ok=True)
    roi_files=sorted((d/'03_roi_timeseries').glob('*signed_rois14.npz'))
    fig,axes=plt.subplots(len(roi_files),2,figsize=(12,3*len(roi_files)),squeeze=False,constrained_layout=True)
    rows=[]
    for ax,file in zip(axes,roi_files):
        hc=file.name.split('_')[1]
        with np.load(file) as a:
            x=a['signed_tc14'];starts=a['segment_starts'];stops=a['segment_stops'];sf=float(a['sfreq'])
        with np.load(next(file.parent.glob(f'*_{hc}_*signed_parcels.npz'))) as a:
            parcels=a['signed_tc100']
            np.testing.assert_array_equal(starts,a['segment_starts']);np.testing.assert_array_equal(stops,a['segment_stops'])
        input_dir = args.run/'inputs'
        if not input_dir.is_dir():
            input_dir = Path(config['paths']['backprojected_dir'])
        raw_file, = input_dir.glob(f'{args.participant}_{hc}_*fif')
        raw=mne.io.read_raw_fif(raw_file,preload=True,verbose=False)
        raw.drop_channels([ch for ch in source_config.get('exclude_channels',[]) if ch in raw.ch_names])
        # String picks include channels marked bad; match the source-model inputs.
        raw.pick(mne.pick_types(raw.info, eeg=True, exclude='bads'))
        if source_config.get('set_average_reference_projection',False):
            raw.set_eeg_reference('average',projection=True,verbose=False)
            raw.apply_proj(verbose=False)
        sig=raw.get_data()*1e6
        segments=[sig[:,a:b] for a,b in zip(starts,stops)]
        keep=np.concatenate(segments,axis=1)
        spectra=[]; weights=[]
        window=int(2*sf)
        for part in segments:
            if part.shape[1]>=window:
                fq,power=welch(part,fs=sf,nperseg=window,axis=1)
                spectra.append(power);weights.append(1+(part.shape[1]-window)//(window//2))
        mean=np.average(spectra,axis=0,weights=weights)
        med=np.median(mean,axis=0)
        def area(lo,hi):
            mask=(fq>=lo)&(fq<=hi)
            return np.trapz(med[mask],fq[mask])
        ptp=np.ptp(keep,axis=1);idx=ptp.argmax()
        dur=(stops-starts);j=dur.argmax();part=segments[j];length=min(part.shape[1],int(4*sf));offset=(part.shape[1]-length)//2
        trace=part[idx,offset:offset+length];ax[0].plot((starts[j]+offset+np.arange(length))/sf,trace,lw=.55)
        ax[0].set_title(f'{hc} | {raw.ch_names[idx]} | excerpt in longest retained segment');ax[0].set(xlabel='Recording time (s)',ylabel='uV')
        ax[1].semilogy(fq,med);ax[1].set(xlim=(1,65),xlabel='Hz',ylabel='Median channel PSD (uV²/Hz)',title=f'{hc} | retained segments')
        for band,limits in [('broadband',None),('alpha',[8,12]),('beta',[13,30])]:
            for route in (14,100):
                sub='matrices' if route==14 else 'pairwise_100parcels'
                f=next((d/'04_static_fc'/sub).glob(f'*_{hc}_*_{band}_*.npz'))
                with np.load(f) as a:
                    native=a[f'fc{route}_signed']
                    if route==14: hz=float(a['envelope_hz_target'])
                if route==14:
                    parts=prepare_segments(x,starts,stops,sf,limits,2 if limits else 0,4)
                    parts=[p for p in parts if p.shape[1]>=round(sf/hz)]
                    full=symmetric_fc(parts,sfreq=sf,envelope_hz=hz)[0]
                    halves=[[p for p in h if p.shape[1]>=round(sf/hz)] for h in split_parts(parts)]
                    first,last=[symmetric_fc(h,sfreq=sf,envelope_hz=hz)[0] for h in halves]
                    half_s=min(sum(p.shape[1] for p in h)/sf for h in halves)
                else:
                    for rate in (256,512,sf):
                        parts,fs,block=prepare_qc_segments(parcels,starts,stops,sf,limits,rate)
                        (full,first,last),counts=pairwise_split_fc(parts,block)
                        if edge_correlation(full,native)>=.98 or fs==sf:break
                    half_s=min(counts)*block/fs
                rows.append(dict(hc=hc,band=band,roi_count=route,half_min_seconds=half_s,
                    split_centered_r=edge_correlation(first,last,True),split_raw_r=edge_correlation(first,last),
                    full_vs_saved_r=edge_correlation(full,native),bp_retained_seconds=keep.shape[1]/sf,
                    peak_channel=raw.ch_names[idx],peak_to_peak_uv=float(ptp[idx]),high_frequency_fraction=area(35,55)/area(1,55),
                    line60_fraction=area(59,61)/area(1,55)))
        print(hc,'complete',flush=True)
    fig.savefig(out/'retained_waveforms_psd.png',dpi=150);plt.close(fig)
    with (out/'split_stability.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)


if __name__=='__main__':
    main()
