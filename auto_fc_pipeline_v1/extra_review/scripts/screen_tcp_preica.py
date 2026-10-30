"""Read-only triage of saved TCP PreICA: flags are not exclusion decisions."""
import os
os.environ['MNE_USE_NUMBA']='false'
os.environ['MPLBACKEND']='Agg'
from pathlib import Path
import json
from datetime import datetime
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
os.environ['_MNE_FAKE_HOME_DIR']=str(ROOT.parent/'.mne_fake_home')
import mne

def main():
    base=ROOT/'outputs/v1_preica_test'
    out=ROOT/'extra_review/outputs'/('tcp_preica_screen_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    out.mkdir()
    print(str(out),flush=True)
    results=[]
    for path in sorted((base/'PreICA').glob('*_preica_raw.fif')):
        subject=path.name.removesuffix('_preica_raw.fif')
        try:
            raw=mne.io.read_raw_fif(path,verbose=False)
            ica=mne.preprocessing.read_ica(base/'ICA'/f'{subject}-ica.fif',verbose=False)
            x=raw.get_data(picks=ica.ch_names)*1e6
            sf=int(round(raw.info['sfreq']));n=x.shape[1]
            bad=np.zeros(n,bool)
            for ann in raw.annotations:
                if ann['description'].lower().startswith('bad'):
                    a=max(0,int(round((ann['onset']-raw.first_time)*sf)))
                    b=min(n,int(round((ann['onset']-raw.first_time+ann['duration'])*sf)))
                    bad[a:b]=True
            nw=n//sf;w=x[:,:nw*sf].reshape(len(x),nw,sf)
            ptp=np.ptp(w,axis=2);sd=np.std(w,axis=2)
            valid=~bad[:nw*sf].reshape(nw,sf).any(axis=1)
            med=np.median(ptp,axis=0);peak=np.max(ptp,axis=0);over=(ptp>500).sum(axis=0);flat=(ptp<1e-5).sum(axis=0)
            event=(peak>1000)|(over>=6)|(flat>=len(x)//2)
            flags=[]
            for j in np.where(event & valid)[0]:
                top=np.argsort(ptp[:,j])[-3:][::-1]
                flags.append({'start':int(j),'end':int(j+1),'peak_ptp_uV':float(peak[j]),'median_ptp_uV':float(med[j]),'channels_over_500':int(over[j]),'near_flat_channels':int(flat[j]),'top_channels':[{'channel':ica.ch_names[k],'ptp_uV':float(ptp[k,j])} for k in top]})
            energy=np.sum(sd**2,axis=0);e=energy[valid]
            frac=float(np.sort(e)[-max(1,int(np.ceil(.01*len(e)))):].sum()/e.sum()) if len(e) and e.sum()>0 else None
            maps=ica.get_components();corr=np.abs(np.corrcoef(maps.T));np.fill_diagonal(corr,0)
            rr={'recording':subject,'source':str(path),'duration_seconds':n/sf,'retained_seconds':float((~bad).sum()/sf),'fully_retained_one_second_windows':int(valid.sum()),'skipped_partial_bad_windows':int((~valid).sum()),'flagged_unmarked_seconds':len(flags),'peak_retained_1s_ptp_uV':float(peak[valid].max()) if valid.any() else None,'median_retained_channel_ptp_uV':float(np.median(med[valid])) if valid.any() else None,'unmarked_broad_500uV_seconds':int(((over>=6)&valid).sum()),'unmarked_nearflat_seconds':int(((flat>=len(x)//2)&valid).sum()),'top_1percent_window_energy_fraction':frac,'ica_components':int(ica.n_components_),'first_pca_fraction':float(ica.pca_explained_variance_[0]/ica.pca_explained_variance_.sum()),'max_absolute_ic_map_correlation':float(corr.max()),'unmarked_flags':flags}
            rr['priority_score']=int(((peak>5000)&valid).sum())*10+rr['unmarked_nearflat_seconds']*10+rr['unmarked_broad_500uV_seconds']*2+len(flags)
            results.append(rr)
            print(f'{subject}: unmarked flags={len(flags)}, peak={rr["peak_retained_1s_ptp_uV"]:.0f} uV',flush=True)
        except Exception as exc:
            results.append({'recording':subject,'error':repr(exc)})
        (out/'screening.json').write_text(json.dumps({'complete':False,'results':results},indent=2))
    results.sort(key=lambda r:r.get('priority_score',-1),reverse=True)
    (out/'screening.json').write_text(json.dumps({'complete':True,'scope':'72 saved TCP PreICA blocks, current selected HC4 for 404. Not raw-data or full visual review.','criteria':'Exploratory triage, not validated exclusion thresholds: 1-second channel ptp >1000 uV, >=6 channels ptp >500 uV, or >=half channels ptp <1e-5 uV. Only wholly unmarked 1-second windows counted; partial/end windows need visual review. No n_iter criterion.','results':results},indent=2))
    print('COMPLETE',flush=True)

if __name__=='__main__':main()
