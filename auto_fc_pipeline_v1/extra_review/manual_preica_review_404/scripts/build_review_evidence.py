"""Export whole-recording evidence for provisional and manual interval review; no fitting."""
from pathlib import Path
import os
import json
os.environ.setdefault('MNE_USE_NUMBA', 'false')
os.environ.setdefault('MNE_LOGGING_LEVEL', 'ERROR')
ROOT = Path(__file__).resolve().parents[4]
os.environ.setdefault('_MNE_FAKE_HOME_DIR', str(ROOT / '.mne_fake_home'))
import numpy as np
import mne
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    out = Path(__file__).resolve().parents[1] / 'outputs/Manual_Review/review_evidence'
    out.mkdir(exist_ok=True)
    base = ROOT / 'auto_fc_pipeline_v1/outputs/v1_preica_test'
    ica = mne.preprocessing.read_ica(base / 'ICA/404_HC4-ica.fif')
    pre = mne.io.read_raw_fif(base / 'PreICA/404_HC4_preica_raw.fif')
    x = pre.get_data(picks=ica.ch_names) * 1e6
    sf = pre.info['sfreq']
    windows = []
    for start in range(0, int(np.ceil(x.shape[1]/sf)), 2):
        end = min(start+2, x.shape[1]/sf)
        a,b = round(start*sf),round(end*sf)
        seg=x[:,a:b];ptp=np.ptp(seg,axis=1)
        windows.append(dict(start=start,end=end,median_channel_ptp_uV=float(np.median(ptp)),
                            maximum_channel_ptp_uV=float(max(ptp)),
                            channels_over_500uV=[ica.ch_names[k] for k in np.where(ptp>500)[0]],
                            top_channels=[dict(channel=ica.ch_names[k],ptp_uV=float(ptp[k])) for k in np.argsort(ptp)[-4:]]))
    (out/'two_second_metrics.json').write_text(json.dumps(windows,indent=2),encoding='utf-8')
    # Full-resolution overview for every nonconstant part of the recording.
    for page in range(0,210,30):
        fig,axes=plt.subplots(1,3,figsize=(24,26),sharey=True,constrained_layout=True)
        for col,ax in enumerate(axes):
            start=page+col*10;end=start+10;a,b=round(start*sf),round(end*sf)
            t=np.arange(a,b)/sf
            for k,name in enumerate(ica.ch_names):
                sig=x[k,a:b];med=np.median(sig)
                # Clip only this overview at +/- 100 uV; mark each exceeded row.
                vals=np.clip(sig-med,-100,100)
                ax.plot(t,vals-k*250,lw=.4,color='#214f79')
                if np.max(abs(sig-med))>100: ax.text(start+.02,-k*250+105,'OVER +/-100',fontsize=5,color='#b52c20')
            ax.set_xlim(start,end);ax.set_xticks(np.arange(start,end+1,2));ax.grid(alpha=.2);ax.set_title(f'{start}-{end} s');ax.set_xlabel('Seconds')
        axes[0].set_yticks(-np.arange(57)*250);axes[0].set_yticklabels(ica.ch_names,fontsize=8)
        fig.suptitle('TCP404 HC4 / saved PreICA / actual samples / per-window median removed / +/-100 uV clipped overview; red labels require detail review')
        fig.savefig(out/f'overview_{page:03d}_{page+30:03d}.png',dpi=110);plt.close(fig)
    # Detailed un-clipped grids for channels with largest excursions, in all-channel flagged windows.
    for start,end in [(0,4),(116,126),(130,140),(140,150),(156,164),(170,184),(184,196)]:
        a,b=round(start*sf),round(end*sf);seg=x[:,a:b];rank=np.argsort(np.ptp(seg,axis=1))[-8:][::-1]
        fig,axes=plt.subplots(8,1,figsize=(16,16),sharex=True,constrained_layout=True)
        for ax,k in zip(axes,rank):
            ax.plot(np.arange(a,b)/sf,seg[k],lw=.5);ax.set_ylabel(ica.ch_names[k]+' uV');ax.grid(alpha=.2)
        axes[-1].set_xlabel('Seconds');fig.suptitle('TCP404 HC4 / actual PreICA samples / independent axes / top 8 channels by peak-to-peak')
        fig.savefig(out/f'detail_{start:03d}_{end:03d}.png',dpi=110);plt.close(fig)
    # Verify every raw cap-channel sample in tail; do not infer constancy from plots.
    path=ROOT/'data/TCP_EEG_sync-selected/EEG/TCOA 404/TCOA_404_HC4.eeg'
    raw=np.memmap(path,dtype='<f4',mode='r').reshape(-1,72)
    last_change=np.flatnonzero(np.any(raw[1:,:64]!=raw[:-1,:64],axis=1))[-1]+1
    assert np.all(raw[last_change:,:64]==raw[-1,:64])
    result=dict(raw_first64_constant_from_seconds=float(last_change/sf),end_seconds=float(len(raw)/sf),
                exact_constant_tail_verified=True,checked_tail_samples_per_channel=int(len(raw)-last_change))
    (out/'tail_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))

if __name__=='__main__':
    main()
