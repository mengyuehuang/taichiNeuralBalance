"""Export un-clipped sample traces for the TCP preICA screening shortlist."""
import os
os.environ['MNE_USE_NUMBA']='false'
os.environ['MPLBACKEND']='Agg'
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.environ['_MNE_FAKE_HOME_DIR']=str(ROOT.parent/'.mne_fake_home')
import mne,numpy as np,json
import matplotlib.pyplot as plt

def main():
    out=ROOT/'extra_review/outputs/tcp_preica_screen_20261030_003851'
    config=json.loads((ROOT/'config.local.json').read_text())
    names={v:k for k,v in config['channels']['rename_map'].items()}
    cases=[('105_HC3',105,110,['AF7','Fp1','O2']),('409_HC4',68,73,['AF7','Fp1','O2']),('411_HC3',273,278,['AF7','Fp1','O2']),('102_HC1',211,216,['O2','O1','Fp1']),('406_HC3',261,266,['P8','Fp1','O2'])]
    checks=[]
    for subject,start,end,channels in cases:
        pre=mne.io.read_raw_fif(ROOT/f'outputs/v1_preica_test/PreICA/{subject}_preica_raw.fif',verbose=False)
        source=next((ROOT.parent/'data/TCP_EEG_sync-selected/EEG').rglob(f'TCOA_{subject}.vhdr'))
        raw=mne.io.read_raw_brainvision(source,verbose=False)
        sf=pre.info['sfreq'];a,b=int(start*sf),int(end*sf)
        xp=pre.get_data(picks=channels,start=a,stop=b)*1e6
        xr=raw.get_data(picks=[names[c] for c in channels],start=a,stop=b)*1e6
        fig,axes=plt.subplots(3,2,figsize=(15,8),sharex=True,constrained_layout=True)
        t=np.arange(a,b)/sf
        for k,ch in enumerate(channels):
            for col,x in enumerate([xr,xp]):
                axes[k,col].plot(t,x[k]-np.median(x[k]),lw=.6)
                axes[k,col].set_ylabel(ch+' (uV)');axes[k,col].grid(alpha=.2)
            checks.append({'recording':subject,'start':start,'end':end,'channel':ch,'raw_ptp_uV':float(np.ptp(xr[k])),'preica_ptp_uV':float(np.ptp(xp[k]))})
        axes[0,0].set_title('Original raw');axes[0,1].set_title('Saved PreICA')
        fig.suptitle(subject+' | actual samples; median removed; independent axes; no clipping')
        fig.savefig(out/f'{subject}_evidence.png',dpi=130);plt.close(fig)
    (out/'raw_spot_checks.json').write_text(json.dumps(checks,indent=2))
    print(json.dumps(checks,indent=2))

if __name__=='__main__':main()
