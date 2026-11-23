"""Prepare filtered EEG and neighbor-PTP evidence only; no epoch screen or ICA."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import run_five_block_pilot as pilot
import numpy as np
import matplotlib.pyplot as plt


def selected_recordings(workspace, participant):
    """Resolve explicit multi-run decisions; never silently drop a second run."""
    records = []
    for hc in ('HC1', 'HC2', 'HC3', 'HC4'):
        block = workspace/'outputs/pcd_aligned/raw'/participant/hc
        available = sorted(p for p in block.glob('run*') if p.is_dir())
        selection = block/'run_selection.json'
        if selection.exists():
            decision = json.loads(selection.read_text(encoding='utf-8'))
            if decision.get('status') != 'approved' or decision.get('action') != 'combine':
                raise ValueError(f'Unapproved or unsupported run selection: {selection}')
            if decision.get('participant') != participant or decision.get('block') != hc:
                raise ValueError(f'Run-selection identity mismatch: {selection}')
            runs = decision['run_order']
            if len(runs) < 2 or len(set(runs)) != len(runs) or set(runs) != {p.name for p in available}:
                raise ValueError(f'Run list does not match available acquisitions: {selection}')
        else:
            if len(available) != 1:
                raise ValueError(f'Expected one run or an approved multi-run selection: {block}')
            runs = [available[0].name]
        for run in runs:
            header = block/run/f'{participant}_{hc}.vhdr'
            if not header.is_file():
                raise FileNotFoundError(header)
            key = hc if len(runs) == 1 else f'{hc}_{run}'
            records.append((hc, run, key, header))
    return records


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('participant')
    ap.add_argument('--resume', action='store_true', help='Reuse existing channel-only filtered files after checking the saved config.')
    args = ap.parse_args()
    if not args.participant.startswith('PCD') or not args.participant[3:].isdigit():
        raise ValueError('Expected a PCD participant ID')
    workspace = pilot.V1.parent
    root = pilot.V1/'outputs/PCD_output/outputs'/f'{args.participant.lower()}_review'
    summary = {}
    for hc, run, key, header in selected_recordings(workspace, args.participant):
        dest = root/key
        dest.mkdir(parents=True, exist_ok=args.resume)
        original = pilot.mne.io.read_raw_brainvision(header, verbose=False)
        cfg = json.loads((pilot.V1/'config.local.json').read_text())
        mapping = cfg['channels']['rename_map']
        indices = [original.ch_names.index(n)+1 for n in mapping]
        assert len(set(indices)) == len(mapping) == 63
        cfg['raw'].update(file_glob=header.name, load_channel_indices_1based=indices)
        cfg['paths'].update(raw_data_dir=str(header.parent.resolve()), output_dir=str(dest.resolve()))
        cfg['preica_qc']['enabled'] = False
        cfg['ica']['figure_subject'] = header.stem
        cfg['naming']['subject_regex'] = r'^(PCD\d+)_(HC[1-4])(?:_|$)'
        existing = list((dest/'PreICA').glob('*.fif'))
        if args.resume and existing:
            assert json.loads((dest/'config.local.json').read_text()) == cfg
        else:
            (dest/'config.local.json').write_text(json.dumps(cfg, indent=2))
            with (dest/'preprocess.log').open('w') as log:
                subprocess.run([sys.executable, str(pilot.V1/'scripts/01_preprocess_filter.py'), '--config', str(dest/'config.local.json')], stdout=log, stderr=subprocess.STDOUT, check=True)
        prefile = next((dest/'PreICA').glob('*.fif'))
        raw = pilot.mne.io.read_raw_fif(prefile, preload=True, verbose=False)
        picks = pilot.mne.pick_types(raw.info, eeg=True, exclude=[])
        assert len(picks) == 57 and not raw.info['bads']
        names = [raw.ch_names[i] for i in picks]
        sf = int(raw.info['sfreq']); assert sf == raw.info['sfreq']
        n = int(raw.n_times//sf)
        x = raw.get_data(picks=picks)*1e6
        ptp = np.ptp(x[:, :n*sf].reshape(57, n, sf), axis=2)
        pos = np.array([raw.info['chs'][i]['loc'][:3] for i in picks])
        assert np.isfinite(pos).all()
        dist = np.linalg.norm(pos[:, None]-pos[None, :], axis=2)
        np.fill_diagonal(dist, np.inf)
        neighbors = np.argsort(dist, axis=1)[:, :4]
        med = np.median(ptp[neighbors], axis=1)
        ratios = ptp/np.maximum(med, 1e-12)
        records = []
        for i, name in enumerate(names):
            records.append(dict(channel=name, neighbors=[names[j] for j in neighbors[i]], complete_seconds=n,
                seconds_above_fivefold=int((ratios[i]>5).sum()), seconds_below_one_fifth=int((ratios[i]<.2).sum()),
                flat_seconds=int((ptp[i]<1e-5).sum()), median_ratio=float(np.median(ratios[i])),
                median_uv=float(np.median(ptp[i])), neighbor_median_uv=float(np.median(med[i])),
                above_seconds=np.flatnonzero(ratios[i]>5).tolist(), below_seconds=np.flatnonzero(ratios[i]<.2).tolist()))
        view = dest/'Manual_Review'; view.mkdir(exist_ok=args.resume)
        (view/'channel_screen.json').write_text(json.dumps(records, indent=2))
        flagged = [i for i, r in enumerate(records) if r['seconds_above_fivefold'] or r['seconds_below_one_fifth'] or r['flat_seconds']]
        show = flagged or [int(np.argmax(ratios.max(axis=1)))]
        fig, axes = plt.subplots(len(show), 2, figsize=(16, 3.4*len(show)), squeeze=False)
        for row, i in enumerate(show):
            a,b = axes[row]; a.semilogy(np.arange(n), ratios[i]); a.axhline(5,color='r',ls=':');a.axhline(.2,color='r',ls=':');a.set(title=f'{names[i]} / median of neighbors',xlabel='Time (s)',ylabel='PTP ratio')
            sec = int(np.argmin(ratios[i]) if records[i]['seconds_below_one_fifth']>records[i]['seconds_above_fivefold'] else np.argmax(ratios[i]))
            start=max(0,sec-1);end=min(raw.n_times/sf,sec+2)
            tt=np.arange(round(start*sf),round(end*sf))/sf
            for j in list(neighbors[i])+[i]: b.plot(tt,x[j,round(start*sf):round(end*sf)],lw=1.3 if j==i else .7,label=names[j])
            b.set(title=f'{names[i]} vs neighbors around extreme PTP ratio',xlabel='Time (s)',ylabel='uV');b.legend(fontsize=8,ncol=5)
        fig.suptitle(f'{args.participant} {key}: channel screening, before average reference');fig.tight_layout();fig.savefig(view/'channel_screen.png',dpi=120);plt.close(fig)
        summary[key]=dict(block=hc,run=run,duration_seconds=raw.n_times/sf,source_header=str(header.resolve()),preica_sha256=hashlib.sha256(prefile.read_bytes()).hexdigest(),flagged=[records[i] for i in flagged])
        print(key,json.dumps(summary[key]['flagged']),flush=True)
    (root/'channel_screen_summary.json').write_text(json.dumps(dict(subject=args.participant,human_approval=False,method='1-second PTP relative to median of four nearest EEG neighbors; >5 or <0.2 prompts manual review, not automatic blocking.',blocks=summary),indent=2))


if __name__ == '__main__':
    main()
