"""Audit existing matrix artifacts without refitting or approving study inclusion."""
from pathlib import Path
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    cohorts = {
        'TCP_legacy': ROOT / 'outputs/corrected',
        'PCD_rank_corrected': ROOT / 'extra_data_pipeline/rank_corrected/outputs',
    }
    report = {'scope': 'File/numerical audit only; not scientific or inclusion approval',
              'cohorts': {}, 'errors': []}
    for cohort, root in cohorts.items():
        routes = {}
        for route, key, size in [('matrices', 'fc14_signed', 14),
                                 ('pairwise_100parcels', 'fc100_signed', 100)]:
            files = sorted(root.glob(f'*/04_static_fc/{route}/*.npz'))
            participants = {}
            for path in files:
                participant = path.parents[2].name
                participants[participant] = participants.get(participant, 0) + 1
                try:
                    with np.load(path) as data:
                        matrix = data[key]
                        assert matrix.shape == (size, size), 'shape'
                        assert np.isfinite(matrix).all(), 'nonfinite'
                        assert np.allclose(matrix, matrix.T, atol=1e-6), 'asymmetric'
                        assert np.allclose(np.diag(matrix), 1, atol=1e-6), 'diagonal'
                        assert np.max(np.abs(matrix)) <= 1 + 1e-6, 'correlation bounds'
                except Exception as error:
                    report['errors'].append({'file': str(path), 'error': str(error)})
            routes[route] = {'matrix_count': len(files), 'participants': participants}
        report['cohorts'][cohort] = routes
    state = json.loads((ROOT / 'extra_data_pipeline/rank_corrected/run_status.json').read_text())
    report['PCD_missing_blocks'] = {
        p: sorted({'HC1', 'HC2', 'HC3', 'HC4'} - set(s['block_rank_checks']))
        for p, s in state.items() if len(s.get('block_rank_checks', {})) < 4
    }
    report['pending'] = [
        'TCP404 reviewed v1 BP has not yet been propagated through v2.',
        'TCP legacy source-rank policy differs from PCD rank-corrected policy.',
        'Five extra-review pilot ICA fits have not produced final BP or replacement FC.',
        'Existing QC group figures predate the documented exclusion clarification; do not present as final cohorts.',
        'Documented matching HC protocols; participant identity overlap remains unresolved.',
        'Planned consistent updated preprocessing; existing Clean BP results are preliminary.',
    ]
    out = ROOT / 'outputs/delivery_audit'
    out.mkdir(exist_ok=True)
    (out / 'matrix_inventory.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'cohorts'}, indent=2))
    for cohort, routes in report['cohorts'].items():
        print(cohort, {r: (v['matrix_count'], len(v['participants'])) for r, v in routes.items()})
    if report['errors']:
        raise SystemExit('Matrix audit failed; inspect matrix_inventory.json')


if __name__ == '__main__':
    main()
