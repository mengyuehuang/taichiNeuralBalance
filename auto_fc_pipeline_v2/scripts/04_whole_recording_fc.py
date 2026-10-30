"""Whole HC recording FC, Step0b QC, and Step2b network features without HMM."""
import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fc_pipeline_v2.config import load_config, resolve_path
from fc_pipeline_v2.io import infer_subject_id, infer_hc_label, infer_block_name
from fc_pipeline_v2.corrected import prepare_segments, pairwise_fc, symmetric_fc, network_features, NETWORK_ORDER
from fc_pipeline_v2.connectivity import fisher_r_to_z
from fc_pipeline_v2.output_paths import ensure_participant_output_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--subject', required=True, help='Participant id')
    parser.add_argument('--plots-only', action='store_true', help='Rebuild the summary from saved matrices without recomputing FC')
    args = parser.parse_args()
    cfg = load_config(args.config)
    paths = ensure_participant_output_paths(cfg, args.subject)
    source = paths['roi_timeseries']
    out = paths['static_fc'] / 'pairwise_100parcels'
    out.mkdir(parents=True, exist_ok=True)
    if args.plots_only:
        records = []
        for file in sorted(out.glob(f'{args.subject}_HC*_fc.npz')):
            band = next((b for b in ['broadband', *cfg.get('frequency_bands', {})]
                         if file.stem.endswith(f'_{b}_fc')), None)
            if band is None:
                raise ValueError(f'Unknown frequency band: {file.name}')
            ident = dict(subject=args.subject, hc=infer_hc_label(file), band=band,
                         group=next((g for g, ids in cfg.get('groups', {}).items()
                                     if args.subject in ids), 'unknown'))
            with np.load(file) as data:
                records.append((ident, data['fc100_signed'], data['fc100_uncorrected'],
                                data['parcel_network']))
        if not records:
            raise FileNotFoundError(f'No saved pairwise matrices in {out}')
        plot_participant_summary(records, out)
        return
    files = sorted(source.glob('*_signed_parcels.npz'))
    if not files:
        raise FileNotFoundError(f'No corrected signed parcel NPZ inputs in {source}; run step 03')
    settings = cfg.get('corrected_fc', {})
    # Compute broadband QC without changing the preprocessing 1–55 Hz
    # upstream filtering. Existing alpha/beta bands remain explicit analyses.
    bands = {'broadband': None, **cfg.get('frequency_bands', {})}
    smoothing_hz = float(settings.get('pairwise_envelope_hz', 8))
    rows, qc, records = [], [], []
    for file in files:
        with np.load(file) as data:
            if str(data['pick_ori']) != 'normal':
                raise ValueError(f'Unsigned source input: {file}')
            sfreq = float(data['sfreq'])
            names, networks = data['parcel_names'], data['parcel_network']
            subject = infer_subject_id(file, cfg['naming']['subject_regex'])
            hc = infer_hc_label(file)
            condition = infer_block_name(file, cfg['naming']['block_patterns'])
            group = next((g for g, ids in cfg.get('groups', {}).items() if subject in ids), 'unknown')
            for band_name, limits in bands.items():
                trim = 0 if limits is None else float(cfg['filtering']['edge_trim_seconds'])
                parts = prepare_segments(data['signed_tc100'], data['segment_starts'], data['segment_stops'],
                                         sfreq, limits, trim, int(cfg['filtering']['order']))
                block = max(1, int(round(sfreq / smoothing_hz)))
                parts = [p for p in parts if p.shape[1] >= block]
                if not parts:
                    raise ValueError(f'No usable segments: {file.name} {band_name}')
                fc100, unc = pairwise_fc(parts, block)
                parts14 = prepare_segments(data['signed_tc14'], data['segment_starts'], data['segment_stops'],
                                           sfreq, limits, trim, int(cfg['filtering']['order']))
                # Low-rank recordings cannot support symmetric 14-ROI FC.
                # Keep valid pairwise-100 results and explicitly flag 14-ROI failure.
                orth_status = 'ok'
                try:
                    hz14 = float(settings.get('symmetric_envelope_hz', 10))
                    parts14 = [p for p in parts14 if p.shape[1] >= round(sfreq / hz14)]
                    fc14, residual = symmetric_fc(parts14, sfreq=sfreq, envelope_hz=hz14)
                except ValueError as error:
                    fc14 = np.full((14, 14), np.nan)
                    residual = np.nan
                    orth_status = str(error)
                for matrix in [fc100, unc] + ([fc14] if orth_status == 'ok' else []):
                    if (not np.isfinite(matrix).all() or np.abs(matrix).max() > 1 + 1e-6
                            or not np.allclose(matrix, matrix.T, atol=1e-6)
                            or not np.allclose(np.diag(matrix), 1, atol=1e-6)):
                        raise ValueError(f'{file.name}: invalid FC matrix')
                # Step0b agreement: collapse 100-parcel pairwise FC to the
                # 14 hemisphere/network blocks and compare off-diagonal edges.
                hemi = np.array([n.split('_')[1] for n in names])
                members = [np.flatnonzero((hemi == h) & (networks == n))
                           for h in ['LH', 'RH'] for n in NETWORK_ORDER]
                collapsed = np.array([[fc100[np.ix_(a, b)].mean() for b in members] for a in members])
                iu14 = np.triu_indices(14, 1)
                agreement = np.corrcoef(collapsed[iu14], fc14[iu14])[0, 1] if orth_status == 'ok' else np.nan
                ident = dict(subject=subject, group=group, hc=hc, condition=condition, band=band_name)
                stem = f'{subject}_{hc}_{condition}_{band_name}'
                z100 = fisher_r_to_z(fc100)
                z100_unc = fisher_r_to_z(unc)
                z14 = fisher_r_to_z(fc14) if orth_status == 'ok' else np.full((14, 14), np.nan)
                np.savez_compressed(out / f'{stem}_fc.npz', fc100_signed=fc100, fc100_uncorrected=unc,
                                    fc14_signed=fc14, fc100_fisher_z=z100,
                                    fc100_uncorrected_fisher_z=z100_unc, fc14_fisher_z=z14,
                                    parcel_names=names, parcel_network=networks,
                                    roi_names=data['roi_names'], sfreq=sfreq,
                                    envelope_hz_actual=sfreq / block, n_segments=len(parts),
                                    envelope_method='block_mean_per_segment',
                                    input_timeseries_file=str(file),
                                    symmetric_envelope_hz_target=hz14,
                                    symmetric_envelope_method='mne_fft_resample_per_segment',
                                    samples_used=sum(p.shape[1] for p in parts))
                for suffix, matrix in [('r', fc100), ('fisher_z', z100)]:
                    pd.DataFrame(matrix, index=names, columns=names).to_csv(
                        out / f'{stem}_fc100_{suffix}.csv')
                for resolution, matrix, net in [('100', fc100, networks),
                                                ('14', fc14, np.array(NETWORK_ORDER * 2))]:
                    rows.append({**ident, 'resolution': resolution, **network_features(matrix, net)})
                upper = np.triu_indices(100, 1)
                within = ((networks[upper[0]] == networks[upper[1]])
                          & (hemi[upper[0]] == hemi[upper[1]]))
                qc.append({**ident, 'n_segments': len(parts),
                           'within_definition': 'same_network_and_same_hemisphere',
                           'envelope_hz_actual': sfreq / block,
                           'envelope_method': 'block_mean_per_segment',
                           'clean_seconds_used': sum(p.shape[1] for p in parts) / sfreq,
                           'max_abs_r_after_orth14': residual, 'orth14_status': orth_status,
                           'agreement_fc100_collapsed_vs_fc14': agreement,
                           'mean_within100': fc100[upper][within].mean(),
                           'mean_between100': fc100[upper][~within].mean()})
                records.append((ident, fc100, unc, networks))
                print(f'{stem}: pairwise100 saved; symmetric14: {orth_status}')
    pd.DataFrame(rows).to_csv(out / 'recording_network_features_fisher_z.csv', index=False)
    pd.DataFrame(qc).to_csv(out / 'recording_qc.csv', index=False)
    plot_participant_summary(records, out)
    print(f'Saved whole-recording results and QC: {out}')


def plot_participant_summary(records, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for subject in sorted({r[0]['subject'] for r in records}):
        selected = [r for r in records if r[0]['subject'] == subject]
        lookup = {(r[0]['hc'], r[0]['band']): r for r in selected}
        if len(lookup) != len(selected):
            raise ValueError(f'Duplicate HC/band matrices for {subject}')
        available = {r[0]['band'] for r in selected}
        bands = [b for b in ['broadband', 'alpha', 'beta'] if b in available]
        bands += sorted(available - set(bands))
        hcs = sorted({r[0]['hc'] for r in selected}, key=lambda h: int(h[2:]))
        fig, axes = plt.subplots(len(hcs), 2 * len(bands),
                                 figsize=(7 * len(bands), 3.6 * len(hcs)),
                                 squeeze=False, constrained_layout=True)
        for row, hc in enumerate(hcs):
            for col, band in enumerate(bands):
                record = lookup.get((hc, band))
                for offset, (index, title) in enumerate([(2, 'Uncorrected'), (1, 'Pairwise corrected')]):
                    ax = axes[row, 2 * col + offset]
                    if row == 0:
                        ax.set_title(f'{band.capitalize()}\n{title}', fontsize=11)
                    if col == 0 and offset == 0:
                        ax.set_ylabel(hc, fontsize=12, fontweight='bold')
                    if record is None:
                        ax.text(.5, .5, 'Not available', ha='center', va='center', transform=ax.transAxes)
                        ax.set_xticks([])
                        ax.set_yticks([])
                        continue
                    matrix = record[index].copy()
                    np.fill_diagonal(matrix, np.nan)
                    im = ax.imshow(matrix, cmap='RdBu_r', vmin=-1, vmax=1, interpolation='nearest')
                    networks = record[3]
                    for boundary in np.flatnonzero(networks[1:] != networks[:-1]) + 1:
                        ax.axhline(boundary - .5, color='k', lw=.3)
                        ax.axvline(boundary - .5, color='k', lw=.3)
                    ax.axhline(49.5, color='k', lw=.9)
                    ax.axvline(49.5, color='k', lw=.9)
                    ax.set_xticks([24.5, 74.5], ['LH', 'RH'] if row == len(hcs) - 1 else ['', ''])
                    ax.set_yticks([24.5, 74.5], ['LH', 'RH'] if offset == 0 else ['', ''])
        fig.colorbar(im, ax=axes, shrink=.7, pad=.015, label='Envelope correlation (r)')
        fig.suptitle(f'Participant {subject}: 100-parcel pairwise connectivity QC', fontsize=18)
        target = out / f'{subject}_fc100_summary.png'
        fig.savefig(target, dpi=200, bbox_inches='tight')
        plt.close(fig)
        # Remove only the superseded plots represented in this successful summary.
        for ident, *_ in selected:
            legacy = out / f"qc_{ident['group']}_{ident['hc']}_{ident['band']}.png"
            if legacy.is_file():
                legacy.unlink()
        print(f'Saved {target}')


if __name__ == '__main__':
    main()
