"""Refit only TCP404 HC4 using the user's saved interval decisions."""
import os
os.environ['MNE_USE_NUMBA'] = 'false'
os.environ['MPLBACKEND'] = 'Agg'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
from pathlib import Path
import json
import hashlib
import subprocess
import sys

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
os.environ['_MNE_FAKE_HOME_DIR'] = str(ROOT.parent / '.mne_fake_home')
OUT = HERE / 'outputs/Selected_158s'

def main():
    import mne
    import numpy as np
    OUT.mkdir(exist_ok=True)
    status = {'stage': 'preparing', 'subject': 'TCP404', 'block': 'HC4'}
    def save():
        (OUT / 'run_status.json').write_text(json.dumps(status, indent=2))
    save()
    try:
        decisions = json.loads((HERE / 'outputs/Manual_Review/human_review_decisions.json').read_text())
        intervals = decisions['intervals']
        assert intervals[0]['start'] == 0 and intervals[-1]['end'] == 589.7
        assert all(a['end'] == b['start'] for a,b in zip(intervals, intervals[1:]))
        assert all(r['my_decision'] in ('include','exclude') for r in intervals)
        source = ROOT / 'outputs/v1_preica_test/PreICA/404_HC4_preica_raw.fif'
        assert hashlib.sha256(source.read_bytes()).hexdigest() == decisions['source_sha256'][str(source)]
        raw = mne.io.read_raw_fif(source, preload=True)
        # Preserve original BAD annotations and absolute timing; omit reviewed
        # exclusions during fitting, rather than concatenate across gaps.
        for r in intervals:
            if r['my_decision'] == 'exclude':
                raw.annotations.append(raw.first_time+r['start'], r['end']-r['start'], 'BAD_human_interval')
        retained = raw.get_data(picks='eeg', reject_by_annotation='omit')
        status['retained_seconds'] = retained.shape[1] / raw.info['sfreq']
        assert abs(status['retained_seconds']-158) < .002
        target = OUT / 'PreICA/404_HC4_preica_raw.fif'
        target.parent.mkdir(exist_ok=True)
        if target.exists():
            raise RuntimeError('Existing reviewed run; will not overwrite or repeat automatically.')
        raw.save(target, overwrite=False)
        config = json.loads((ROOT / 'config.local.json').read_text())
        config['paths']['output_dir'] = str(OUT)
        config['ica']['apply_without_review'] = False
        config_path = OUT / 'config.json'
        config_path.write_text(json.dumps(config, indent=2))
        status['stage'] = 'fitting_ica_and_exporting_review'
        save()
        subprocess.run([sys.executable, str(ROOT/'scripts/04_run_ica.py'), '--config', str(config_path), '--include-regex', '^404_HC4$'], check=True)
        ica = mne.preprocessing.read_ica(OUT/'ICA/404_HC4-ica.fif')
        old = mne.preprocessing.read_ica(ROOT/'outputs/v1_preica_test/ICA/404_HC4-ica.fif')
        status.update(stage='awaiting_new_component_review', n_components=int(ica.n_components_), n_iter=int(ica.n_iter_), old_n_components=int(old.n_components_), old_n_iter=int(old.n_iter_), fit_samples=int(ica.n_samples_), old_fit_samples=int(old.n_samples_), pca_first_fraction=float(ica.pca_explained_variance_[0]/np.sum(ica.pca_explained_variance_)), old_pca_first_fraction=float(old.pca_explained_variance_[0]/np.sum(old.pca_explained_variance_)), backprojection_completed=False)
        save()
    except Exception as error:
        status.update(stage='failed', error=repr(error));save();raise

if __name__ == '__main__':
    main()
