"""Read-only TCP404 HC4 review export. Never fits ICA or applies decisions."""
from pathlib import Path
import os
import json
import hashlib
import gzip
import base64

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1] / 'outputs/Manual_Review'
os.environ.setdefault('MNE_USE_NUMBA', 'false')
os.environ.setdefault('MNE_LOGGING_LEVEL', 'ERROR')
os.environ.setdefault('_MNE_FAKE_HOME_DIR', str(ROOT / '.mne_fake_home'))
import numpy as np
import mne
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    folder = ROOT / 'data/TCP_EEG_sync-selected/EEG/TCOA 404'
    base = ROOT / 'auto_fc_pipeline_v1/outputs/v1_preica_test'
    paths = [folder / 'TCOA_404_HC4.vhdr', folder / 'TCOA_404_HC4.eeg',
             folder / 'TCOA_404_HC4.vmrk', base / 'PreICA/404_HC4_preica_raw.fif',
             base / 'ICA/404_HC4-ica.fif']
    before = {str(p): sha256(p) for p in paths}
    config = json.loads((ROOT / 'auto_fc_pipeline_v1/config.local.json').read_text())
    reverse = {v: k for k, v in config['channels']['rename_map'].items()}
    raw = mne.io.read_raw_brainvision(paths[0], preload=False)
    pre = mne.io.read_raw_fif(paths[3], preload=False)
    ica = mne.preprocessing.read_ica(paths[4])
    names = ica.ch_names
    sf = float(raw.info['sfreq'])
    assert sf == pre.info['sfreq'] and raw.n_times == pre.n_times
    x = raw.get_data(picks=[reverse[n] for n in names]) * 1e6
    y = pre.get_data(picks=names) * 1e6
    assert np.isfinite(x).all() and np.isfinite(y).all()
    duration = x.shape[1] / sf
    old_bad = [{'start': float(a['onset'] - pre.first_time),
                'end': float(a['onset'] - pre.first_time + a['duration'])}
               for a in pre.annotations if a['description'].lower().startswith('bad')]
    metrics = []
    for start in range(int(np.ceil(duration))):
        end = min(start + 1, duration)
        a, b = int(round(start * sf)), int(round(end * sf))
        rx, py = x[:, a:b], y[:, a:b]
        flat = float(np.mean(np.ptp(rx, axis=1) <= .01))
        raw_max = float(np.max(np.abs(rx)))
        pre_ptp = float(np.max(np.ptp(py, axis=1)))
        reasons = []
        if flat >= .95: reasons.append('raw_flat_at_least_95pct_channels')
        if raw_max >= 100000: reasons.append('raw_absolute_amplitude_ge_100000uV')
        if pre_ptp >= 500: reasons.append('preICA_channel_ptp_ge_500uV')
        metrics.append(dict(start=start, end=end, raw_flat_fraction=flat,
                            raw_max_abs_uV=raw_max, preICA_max_channel_ptp_uV=pre_ptp,
                            flags=reasons))
    candidates = []
    for row in metrics:
        if not row['flags']: continue
        if candidates and candidates[-1]['end'] == row['start'] and candidates[-1]['flags'] == row['flags']:
            candidates[-1]['end'] = row['end']
        else:
            candidates.append(dict(start=row['start'], end=row['end'], flags=row['flags'],
                                   decision='', reviewer='', note=''))
    # Direct file-level check of all 64 recorded EEG/auxiliary cap channels.
    binary = np.memmap(paths[1], dtype='<f4', mode='r').reshape(-1, len(raw.ch_names))
    changing = np.flatnonzero(np.any(binary[1:, :64] != binary[:-1, :64], axis=1))
    tail = float((changing[-1] + 1) / sf) if len(changing) else 0.
    summary = dict(subject='TCP404', block='HC4', duration_seconds=duration,
                   channels=names, samples=x.shape[1], sfreq=sf,
                   all_first64_constant_tail_start=tail,
                   constant_tail_seconds=duration-tail,
                   original_bad_intervals=old_bad,
                   thresholds='Exploratory review flags, not validated exclusion rules. Raw DC amplitude alone does not prove saturation.',
                   status='awaiting_human_review', decisions_applied=False,
                   sample_interval='Half-open [start, end), seconds from file start.',
                   source_sha256=before)
    (OUT / 'review_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    (OUT / 'one_second_metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    (OUT / 'candidate_intervals.json').write_text(json.dumps(candidates, indent=2), encoding='utf-8')

    fig, ax = plt.subplots(3, 1, figsize=(15, 9), sharex=True, constrained_layout=True)
    t = [r['start'] for r in metrics]
    ax[0].plot(t, [r['raw_max_abs_uV'] for r in metrics]); ax[0].set_ylabel('Raw max |amplitude| (uV)')
    ax[1].plot(t, [r['preICA_max_channel_ptp_uV'] for r in metrics]); ax[1].set_yscale('symlog'); ax[1].set_ylabel('PreICA max channel PTP (uV)')
    ax[2].plot(t, [r['raw_flat_fraction'] for r in metrics]); ax[2].set_ylabel('Raw flat channel fraction'); ax[2].set_xlabel('Seconds from recording start')
    for a in ax:
        a.axvspan(tail, duration, color='tomato', alpha=.13, label='Exact constant tail (first 64 channels)')
        for span in old_bad: a.axvspan(span['start'], span['end'], color='black', alpha=.3)
        a.grid(alpha=.2)
    ax[0].legend(loc='upper left'); fig.suptitle('TCP404 HC4 pre-ICA review: raw record and saved filtered input')
    fig.savefig(OUT / 'recording_overview.png', dpi=140); plt.close(fig)

    chosen = ['Fp1', 'O1', 'P8', 'C2', 'AFz', 'C4']
    for lo, hi, label in [(115,155,'early_transients'), (180,205,'constant_tail_transition')]:
        fig, axes = plt.subplots(len(chosen), 2, figsize=(15,12), sharex=True, constrained_layout=True)
        a,b=int(lo*sf),int(hi*sf); times=np.arange(a,b)/sf
        for j,name in enumerate(chosen):
            k=names.index(name)
            for col,arr in enumerate([x,y]):
                axes[j,col].plot(times,arr[k,a:b],lw=.45)
                axes[j,col].set_ylabel(name+' (uV)'); axes[j,col].grid(alpha=.2)
                for span in old_bad: axes[j,col].axvspan(span['start'],span['end'],alpha=.12,color='red')
                axes[j,col].set_xlim(lo,hi)
        axes[0,0].set_title('Original raw (absolute voltage)'); axes[0,1].set_title('Saved filtered PreICA (before average reference)')
        fig.suptitle('TCP404 HC4: '+label.replace('_',' ')+'; independent y scales')
        fig.savefig(OUT / (label+'.png'),dpi=130);plt.close(fig)

    # Lossless float64 samples in independently loaded 10-second chunks.
    chunk_samples = int(10 * sf)
    chunks = OUT / 'waveform_data'
    chunks.mkdir(exist_ok=True)
    for idx, a in enumerate(range(0, x.shape[1], chunk_samples)):
        block = np.stack([x[:, a:a+chunk_samples], y[:, a:a+chunk_samples]])
        encoded = base64.b64encode(gzip.compress(block.astype('<f8').tobytes(), compresslevel=4)).decode('ascii')
        content = 'window.registerWaveformChunk(' + str(idx) + ',' + json.dumps(encoded) + ');'
        (chunks / f'chunk_{idx:03d}.js').write_text(content, encoding='utf-8')
    payload = dict(summary=summary, candidates=candidates, chunk_samples=chunk_samples,
                   chunk_count=int(np.ceil(x.shape[1]/chunk_samples)), format='gzip_float64_le')
    review_path = OUT / 'assistant_review_decisions.json'
    if review_path.exists():
        review = json.loads(review_path.read_text(encoding='utf-8'))
        if review.get('source_sha256') != before:
            raise ValueError('Suggestion provenance differs from current sources')
        payload['assistant_review'] = review
    template=(Path(__file__).resolve().parents[1]/'src/viewer_template.html').read_text(encoding='utf-8')
    (OUT/'review.html').write_text(template.replace('/*PAYLOAD*/',json.dumps(payload,separators=(',',':'))),encoding='utf-8')
    after={str(p):sha256(p) for p in paths}
    assert before==after, 'Source changed during export'
    print(json.dumps({'export':str(OUT),'constant_tail_start':tail,'candidates':len(candidates),'source_hashes_unchanged':True}))


if __name__ == '__main__':
    main()
