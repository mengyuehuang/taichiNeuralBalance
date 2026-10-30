"""Export all 30 topographies from the selected, converged 158-second ICA."""
import os
os.environ['MNE_USE_NUMBA'] = 'false'
os.environ['MPLBACKEND'] = 'Agg'
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parents[1]
os.environ['_MNE_FAKE_HOME_DIR'] = str(HERE.parents[2] / '.mne_fake_home')

def main():
    import mne
    import matplotlib.pyplot as plt
    source = HERE / 'outputs/Comparisons/termination_comparison_20261029_223545/human_158s'
    model = source / '404_HC4-ica.fif'
    status = json.loads((source / 'termination.json').read_text())
    assert status['weight_change_converged'] and status['retained_seconds'] == 158
    out = HERE / 'outputs/Selected_158s/ICA_Figures/404/HC4'
    out.mkdir(parents=True, exist_ok=True)
    ica = mne.preprocessing.read_ica(model)
    paths = []
    figures = ica.plot_components(show=False)
    if not isinstance(figures, list):
        figures = [figures]
    for index, fig in enumerate(figures, 1):
        path = out / f'ica_components_{index}.png'
        fig.savefig(path, dpi=150)
        plt.close(fig)
        paths.append(path.name)
    metadata = {'selected_scheme': 'human_158s', 'selection_basis': 'Original interval decisions selected',
                'model': str(model), 'model_sha256': hashlib.sha256(model.read_bytes()).hexdigest(),
                'termination': status, 'mne_version': mne.__version__, 'files': paths,
                'component_numbering': 'zero-based, IC00 through IC29',
                'note': 'Independent map color scales; ICA sign/scale is arbitrary. No refitting or component rejection.'}
    (out / 'provenance.json').write_text(json.dumps(metadata, indent=2))
    print(f'Exported {len(paths)} images to {out}')

if __name__ == '__main__':
    main()
