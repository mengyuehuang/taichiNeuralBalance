"""Prepare one named-channel PCD raw recording for pre-ICA interval review."""
import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

import run_five_block_pilot as pilot
import numpy as np
from hc_epoch_statistics import epoch_statistics


def screen_epochs(pre, mapping, blocked, dest):
    ordered = list(mapping.values())
    channels = [name for name in ordered if name not in blocked]
    local = [i for i, name in enumerate(channels) if name in ordered[:61]]
    sf = int(pre.info['sfreq'])
    if sf != pre.info['sfreq']:
        raise ValueError('Whole-second epoching requires an integer sampling rate.')
    report = dest/'PreICA_QC'/'eeglab_epoch_flags.csv'
    jp, kurt, global_jp, global_kurt = epoch_statistics(
        pre.get_data(picks=channels)*1e6, sf, local)
    flags = []
    for second in range(len(global_jp)):
        jp_names = [channels[local[i]] for i in np.flatnonzero(abs(jp[:,second]) > 6)]
        kurt_names = [channels[local[i]] for i in np.flatnonzero(abs(kurt[:,second]) > 6)]
        flags.append(dict(epoch_start_s=second,
                          joint_probability=int(bool(jp_names) or abs(global_jp[second]) > 6),
                          kurtosis_flag=int(bool(kurt_names) or abs(global_kurt[second]) > 6),
                          local_jp_channels=' '.join(jp_names), local_kurt_channels=' '.join(kurt_names),
                          global_jp_z=global_jp[second], global_kurt_z=global_kurt[second]))
    with report.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=flags[0])
        writer.writeheader()
        writer.writerows(flags)
    rows = []
    for start in range(0, pre.n_times, sf):
        second = start//sf
        if second == len(flags):
            reasons = ['partial_epoch_manual_review']
        else:
            reasons = [key for key in ('joint_probability', 'kurtosis_flag') if int(flags[second][key])]
        decision = ('uncertain' if second == len(flags) else 'exclude') if reasons else 'include'
        end = min(start+sf, pre.n_times)/sf
        if rows and rows[-1]['flags'] == reasons:
            rows[-1]['end'] = end
        else:
            rows.append(dict(start=second, end=end, decision=decision, assistant_decision=decision,
                             my_decision='', flags=reasons, reviewer='',
                             note=('Incomplete final second: review manually.' if decision == 'uncertain' else
                                   'Automatic exclusion under the epoch-union policy.' if reasons else
                                   'Inspect for additional manual exclusions.')))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('header', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--bad-channel', action='append', default=[], help='Recording-specific EEG channel excluded from QC, average reference and ICA.')
    args = parser.parse_args()
    header = args.header.resolve()
    dest = args.destination.resolve()
    dest.mkdir(parents=True, exist_ok=False)
    subject = header.stem
    raw = pilot.mne.io.read_raw_brainvision(header, verbose=False)
    cfg = json.loads((pilot.V1/'config.local.json').read_text())
    cfg['ica']['figure_subject'] = subject
    mapping = cfg['channels']['rename_map']
    cfg['preica_qc']['enabled'] = False  # The EEGLAB screen supersedes the historical z-score annotations.
    if args.bad_channel:
        if not set(args.bad_channel) <= set(mapping.values()):
            raise ValueError('Unknown bad channel')
        qc = cfg['preica_qc']
        selected = qc.get('reject_channel_names') or [list(mapping.values())[i-1] for i in qc['reject_channel_indices_1based_after_loading']]
        qc['reject_channel_names'] = [n for n in selected if n not in args.bad_channel]
        cfg['ica']['exclude_channels'] = sorted(set(cfg['ica']['exclude_channels']) | set(args.bad_channel))
    indices = [raw.ch_names.index(name)+1 for name in mapping]
    assert len(set(indices)) == len(mapping) == 63
    cfg['paths'].update(raw_data_dir=str(header.parent), output_dir=str(dest))
    cfg['raw'].update(file_glob=header.name, load_channel_indices_1based=indices)
    cfg['naming']['subject_regex'] = r'^(PCD\d+)_(HC[1-4])(?:_|$)'
    config = dest/'config.local.json'
    config.write_text(json.dumps(cfg, indent=2))
    with (dest/'preprocess.log').open('w') as log:
        subprocess.run([sys.executable, str(pilot.V1/'scripts/01_preprocess_filter.py'), '--config', str(config)], stdout=log, stderr=subprocess.STDOUT, check=True)
    prefile = next((dest/'PreICA').glob('*.fif'))
    pre = pilot.mne.io.read_raw_fif(prefile, preload=True, verbose=False)
    if args.bad_channel:
        eeg_names = [pre.ch_names[i] for i in pilot.mne.pick_types(pre.info, eeg=True)]
        if not set(args.bad_channel) <= set(eeg_names):
            raise ValueError('Specified channel is not an available EEG channel')
        pre.info['bads'] = sorted(set(pre.info['bads']) | set(args.bad_channel))
        pre.save(prefile, overwrite=True, verbose=False)
    picks = pilot.mne.pick_types(pre.info, eeg=True)
    names = [pre.ch_names[i] for i in picks]
    assert len(names)==57-len(set(args.bad_channel)) and all(n in mapping.values() for n in names)
    sf = int(pre.info['sfreq'])
    rows = screen_epochs(pre, mapping, args.bad_channel, dest)
    view=dest/'Manual_Review'
    pilot.export_viewer(view,subject,raw,pre,names,sorted(rows,key=lambda r:r['start']),{str(prefile):pilot.sha(prefile),str(header):pilot.sha(header)},args.bad_channel, epoch_union=True)
    p=view/'review_decisions.json';j=json.loads(p.read_text());j['decisions_applied_to_isolated_pilot']=False;j['interval_policy']='epoch_union';p.write_text(json.dumps(j,indent=2))
    h=view/'review.html';html=h.read_text(encoding='utf-8').replace('were applied ONLY to this isolated pilot','are pending manual review before ICA');h.write_text(html,encoding='utf-8')
    assert len(list((view/'waveform_data').glob('*.js')))==int(np.ceil(pre.n_times/(10*sf)))
    print(subject, 'total seconds', pre.n_times/sf, 'flagged intervals',
          [(r['start'],r['end']) for r in rows if r['decision']=='exclude'], flush=True)


if __name__=='__main__':
    main()
