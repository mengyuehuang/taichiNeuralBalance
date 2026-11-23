"""Compare interval screens after an additional channel mask; never fit ICA."""
import argparse
import copy
import json
from pathlib import Path

import run_five_block_pilot as pilot
import numpy as np
from fc_pipeline.preica import annotate_noisy_fixed_chunks


def screen(raw, config, bads):
    raw = raw.copy()
    raw.info['bads'] = list(bads)
    qc = copy.deepcopy(config['preica_qc'])
    selected = qc.get('reject_channel_names')
    if not selected:
        selected = [raw.ch_names[i-1] for i in qc['reject_channel_indices_1based_after_loading']]
    qc['reject_channel_names'] = [n for n in selected if n not in bads]
    result = annotate_noisy_fixed_chunks(raw, qc)
    raw.set_annotations(raw.annotations + result.annotations)
    names = [raw.ch_names[i] for i in pilot.mne.pick_types(raw.info, eeg=True, exclude='bads')]
    x = raw.get_data(picks=names) * 1e6
    sf = int(raw.info['sfreq'])
    mask = pilot.annotation_mask(raw)
    peaks = []
    for a in range(0, raw.n_times, sf):
        ptp = np.ptp(x[:, a:a+sf], axis=1)
        peaks.append(ptp)
        if ptp.max() > 1000 or (ptp > 500).sum() >= 6 or (ptp < 1e-5).sum() >= len(ptp)/2:
            mask[max(0,a-sf//2):min(raw.n_times,a+3*sf//2)] = True
    rows = []
    for excluded in (True, False):
        for a,b in pilot.spans(mask == excluded, sf):
            vals = np.max(peaks[int(a):max(int(a)+1,int(np.ceil(b)))], axis=0)
            top = np.argsort(-vals)[:2]
            decision = 'exclude' if excluded else 'include'
            rows.append(dict(start=a,end=b,decision=decision,assistant_decision=decision,
                my_decision='',reviewer='',flags=['screen_flag' if excluded else 'provisional_include'],
                note='Screening only. Largest 1-s PTP in overlapping bins: '+', '.join(f'{names[i]} {vals[i]:.0f} uV' for i in top)))
    return raw, names, mask, sorted(rows,key=lambda r:r['start'])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source',type=Path)
    ap.add_argument('destination',type=Path)
    ap.add_argument('--add-bad-channel',required=True)
    args=ap.parse_args()
    src=args.source.resolve(); dest=args.destination.resolve()
    cfg=json.loads((src/'config.local.json').read_text())
    old=json.loads((src/'Manual_Review/review_decisions.json').read_text())
    filtered=next((src/'Filtered').glob('*.fif'))
    raw=pilot.mne.io.read_raw_fif(filtered,preload=True,verbose=False)
    assert not any(a['description']=='BAD_preICA_auto' for a in raw.annotations)
    before,names,oldmask,oldrows=screen(raw,cfg,old['bad_channels'])
    expected=np.zeros(raw.n_times,bool); sf=int(raw.info['sfreq'])
    for r in old['intervals']:
        if r['decision']=='exclude': expected[round(r['start']*sf):round(r['end']*sf)]=True
    assert np.array_equal(oldmask,expected), 'Baseline does not reproduce existing viewer; stop.'
    assert args.add_bad_channel in names
    bads=sorted(set(old['bad_channels'])|{args.add_bad_channel})
    after,names,newmask,rows=screen(raw,cfg,bads)
    dest.mkdir(parents=True,exist_ok=False)
    header=Path(cfg['paths']['raw_data_dir'])/cfg['raw']['file_glob']
    original=pilot.mne.io.read_raw_brainvision(header,verbose=False)
    pilot.export_viewer(dest/'Manual_Review',header.stem,original,after,names,rows,
        {str(filtered):pilot.sha(filtered),str(header):pilot.sha(header)},bads)
    f=dest/'Manual_Review/review_decisions.json'; j=json.loads(f.read_text())
    j.update(decisions_applied_to_isolated_pilot=False,comparison_only=True)
    f.write_text(json.dumps(j,indent=2))
    f=dest/'Manual_Review/review.html';html=f.read_text(encoding='utf-8')
    html=html.replace('the displayed proposed intervals were applied ONLY to this isolated pilot.',
        'comparison only; these proposed intervals have NOT been applied to an ICA fit.')
    html=html.replace('Bad channels excluded from reference and ICA:', 'Channels omitted from this proposed screen:')
    f.write_text(html,encoding='utf-8')
    report=dict(source=str(src),filtered_sha256=pilot.sha(filtered),baseline_matches_existing_viewer=True,
        before_bad_channels=old['bad_channels'],after_bad_channels=bads,
        before_excluded_seconds=oldmask.sum()/sf,after_excluded_seconds=newmask.sum()/sf,
        before_retained_seconds=(~oldmask).sum()/sf,after_retained_seconds=(~newmask).sum()/sf,
        before_excluded_intervals=pilot.spans(oldmask,sf),after_excluded_intervals=pilot.spans(newmask,sf),
        newly_proposed_include=pilot.spans(oldmask & ~newmask,sf),newly_proposed_exclude=pilot.spans(newmask & ~oldmask,sf),
        method='Same saved filtered samples; recompute z-score QC and amplitude/flat screen in both cases. Only additional channel mask changes. No ICA, reference, or approved decisions changed.')
    (dest/'comparison.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
