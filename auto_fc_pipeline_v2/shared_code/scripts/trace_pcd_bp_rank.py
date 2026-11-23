"""Trace PCD Clean BP rank before source reconstruction using the saved SET/FDT."""
from pathlib import Path
import csv
import json
import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[2]
EXTRA = ROOT/'output/PCD_output'
ARCHIVE = ROOT.parent/'data/VRHCT_CleanData-selected'
OUT = ROOT/'output/TCP_output/study_fc_display'


def rank(x):
    s = np.linalg.svd(x-x.mean(axis=1,keepdims=True),compute_uv=False)
    return int(sum(s>s[0]*1e-6))


def main():
    policy = json.loads((EXTRA/'participant_policy.json').read_text())['participants']
    states = json.loads((EXTRA/'rank_corrected/run_status.json').read_text())
    rows=[]
    with (EXTRA/'input_manifest.csv').open(encoding='utf-8-sig') as handle:
        for row in csv.DictReader(handle):
            sid,hc=row['participant'],row['block']
            if row['status']!='selected' or policy.get(sid,{}).get('action')=='exclude':
                continue
            file=Path(row['path'])
            e=loadmat(file,simplify_cells=True)['EEG']
            x=np.memmap(file.parent/e['data'],dtype='<f4',mode='r').reshape(-1,int(e['nbchan'])).T
            assert x.shape[1]==int(e['pnts'])
            sample=x[:,::max(1,x.shape[1]//6000)].astype(float)
            fitted=sample[np.asarray(e['icachansind'],int)-1]
            fitted-=fitted.mean(axis=1,keepdims=True)
            mix=np.asarray(e['icawinv']).reshape(len(fitted),-1)
            residual=fitted-mix@(np.linalg.pinv(mix)@fitted)
            rows.append(dict(participant=sid,block=hc,good_count=np.size(e.get('good',[])),mix_columns=mix.shape[1],
                bp_ica_channels_rank=rank(fitted),bp_all_channels_rank=rank(sample),
                relative_outside_saved_maps=np.linalg.norm(residual)/np.linalg.norm(fitted),
                **states[sid]['block_rank_checks'][hc]))
    assert len(rows)==131
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'pcd_bp_rank_trace.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    low=[r for r in rows if r['source_roi_rank']<14]
    print('low ROI blocks:',len(low),'already low before v2:',sum(r['bp_all_channels_rank']<14 for r in low),
          'ICA channels equal stored IC count:',sum(r['bp_ica_channels_rank']==r['mix_columns'] for r in low),
          'largest relative residual:',max(r['relative_outside_saved_maps'] for r in low))


if __name__=='__main__':
    main()
