"""PCD reviewed-cohort display, adapted from reference Step0b cell 0b.6.

No source reconstruction or individual FC is recomputed. Four HC matrices are
averaged in Fisher-z space per participant before reference double-centering.
"""
from pathlib import Path
import hashlib
import json
import re
import warnings
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT.parent
RUNS = ROOT / "output/PCD_output/outputs"
DEST = ROOT / "output/PCD_output/group_fc_display"
REFERENCE = PROJECT / "references/Step0b_Connectome_Sanity_Check_100parcels.ipynb"
SUBJECTS = [f"PCD{i}" for i in [101,102,105,106,*range(109,121),201,*range(203,210),*range(212,221)]]
BANDS = ("alpha", "beta")
BLOCKS = ("HC1", "HC2", "HC3", "HC4")
NETWORKS = ("Vis", "SomMot", "DorsAttn", "SalVentAttn", "Limbic", "Cont", "Default")
VERSIONS = {"pairwise": "fc100_signed", "uncorrected": "fc100_uncorrected"}

# Reference implementations: Step0b, group FC figure cell 0b.6.
def fisher_z(matrix):
    z = np.arctanh(np.clip(matrix, -.999999, .999999)).astype(float)
    np.fill_diagonal(z, np.nan)
    return z


def double_center(z):
    off = ~np.eye(len(z), dtype=bool)
    row = np.nanmean(z, axis=1)
    grand = np.nanmean(z[off])
    centered = z - row[:, None] - row[None, :] + grand
    np.fill_diagonal(centered, np.nan)
    return centered


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert len(SUBJECTS) == len(set(SUBJECTS)) == 33
    policy = json.loads((ROOT / "output/PCD_output/participant_policy.json").read_text(encoding="utf-8"))
    assert all(policy["participants"].get(s, {}).get("action") != "exclude" for s in SUBJECTS)
    sources = []
    arrays = {v: {b: [] for b in BANDS} for v in VERSIONS}
    names = None
    order = None
    labels = None
    for sid in SUBJECTS:
        candidates = [p for p in RUNS.glob(sid + "_epoch_union_*") if re.fullmatch(sid + r"_epoch_union_\d{8}", p.name)]
        if len(candidates) != 1:
            raise ValueError(f"Expected one reviewed run for {sid}: {candidates}")
        folder = candidates[0] / "outputs" / sid / "04_static_fc/pairwise_100parcels"
        for band in BANDS:
            per_block = {v: [] for v in VERSIONS}
            for hc in BLOCKS:
                files = list(folder.glob(f"{sid}_{hc}_*_{band}_fc.npz"))
                if len(files) != 1:
                    raise ValueError(f"Missing/ambiguous block: {sid} {hc} {band}")
                path = files[0]
                with np.load(path) as data:
                    current = data["parcel_names"].astype(str)
                    if names is None:
                        names = current.copy()
                        if len(names) != 100 or len(set(names)) != 100:
                            raise ValueError("Expected 100 unique parcels")
                        hemi = [n.split("_")[1] for n in names]
                        network = [n.split("_")[2] for n in names]
                        order = np.array(sorted(range(100), key=lambda i: (("LH", "RH").index(hemi[i]), NETWORKS.index(network[i]), i)))
                        labels = [hemi[i] + " " + network[i] for i in order]
                    np.testing.assert_array_equal(current, names)
                    for version, key in VERSIONS.items():
                        matrix = data[key]
                        off = matrix[~np.eye(100, dtype=bool)]
                        assert matrix.shape == (100,100) and np.isfinite(off).all()
                        assert np.max(np.abs(off)) <= 1.000001
                        assert np.allclose(matrix, matrix.T, atol=1e-7, equal_nan=True)
                        per_block[version].append(fisher_z(matrix[np.ix_(order,order)]))
                sources.append(dict(subject=sid, block=hc, band=band, file=str(path), sha256=sha(path)))
            for version in VERSIONS:
                # Equal HC weight; mean keeps the intentionally masked diagonal NaN.
                arrays[version][band].append(double_center(np.mean(per_block[version], axis=0)))
    DEST.mkdir(parents=True, exist_ok=True)
    iu = np.triu_indices(100,1)
    starts = [i for i in range(100) if i == 0 or labels[i] != labels[i-1]]
    ticks = (np.array(starts) + np.array(starts[1:] + [100]) - 1) / 2
    limits = {}
    checks = {}
    for version in VERSIONS:
        groups = {b: np.mean(arrays[version][b], axis=0) for b in BANDS}
        # Reference 99th-percentile absolute upper-triangle scale, shared across panels.
        lim = float(np.nanpercentile(np.abs(np.concatenate([m[iu] for m in groups.values()])),99))
        assert np.isfinite(lim) and lim > 0
        limits[version] = lim
        fig, axes = plt.subplots(1,2,figsize=(14,7.6))
        for ax, band in zip(axes,BANDS):
            m = groups[band]
            assert np.isfinite(m[iu]).all() and np.allclose(m,m.T,equal_nan=True)
            im = ax.imshow(m,cmap="RdBu_r",vmin=-lim,vmax=lim,interpolation="nearest")
            ax.xaxis.tick_top()
            ax.set_xticks(ticks,[labels[i] for i in starts],rotation=90,fontsize=8)
            ax.set_yticks(ticks,[labels[i] for i in starts],fontsize=8)
            ax.tick_params(length=0)
            ax.axhline(49.5,color="black",lw=.7);ax.axvline(49.5,color="black",lw=.7)
            ax.set_xlabel(f"PCD {band} | {version} | n={len(SUBJECTS)}",fontsize=12,labelpad=12)
            checks[version+"_"+band] = dict(minimum=float(m[iu].min()),maximum=float(m[iu].max()),clipped_edges=int((np.abs(m[iu])>lim).sum()),total_edges=len(m[iu]))
            np.savez_compressed(DEST/f"PCD_{band}_{version}_group_fc.npz",centered_fisher_z=m,participant_centered_fisher_z=np.asarray(arrays[version][band]),participant_ids=np.array(SUBJECTS),parcel_names=names[order],blocks=np.array(BLOCKS),color_limit=lim)
        fig.subplots_adjust(left=.08,right=.89,bottom=.13,top=.76,wspace=.30)
        cax=fig.add_axes([.92,.20,.015,.50])
        fig.colorbar(im,cax=cax,extend="both",label="Centered Fisher z (relative connectivity)")
        fig.suptitle("PCD group-mean FC | Schaefer-100, hemisphere order",fontsize=16,y=.98)
        fig.text(.5,.925,"HC1–HC4 equally averaged per participant; double-centered; 33 participants equally weighted",ha="center",fontsize=10)
        fig.text(.5,.045,"Descriptive visualization / QC. Shared symmetric scale: 99th percentile of absolute off-diagonal values; extremes saturate.",ha="center",fontsize=9)
        stem="FC_group_matrices_leakage_corrected" if version=="pairwise" else "FC_group_matrices_uncorrected"
        fig.savefig(DEST/(stem+".png"),dpi=180)
        fig.savefig(DEST/(stem+".pdf"))
        plt.close(fig)
    audit=dict(reference=str(REFERENCE),reference_sha256=sha(REFERENCE),script_sha256=sha(Path(__file__)),participants=SUBJECTS,n=33,blocks=BLOCKS,bands=BANDS,input_count=len(sources),sources=sources,color_limits=limits,checks=checks,method="Fisher z per HC -> equal four-HC mean per participant -> reference double-centering -> equal participant mean",adaptations="Reference EC/EO replaced by complete HC1-HC4; reference group panels replaced by PCD alpha/beta panels; common reference-style scale across both bands per version",all_checks_passed=True)
    (DEST/"provenance.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
    (DEST/"README.md").write_text("# Reviewed PCD group FC display\n\nGenerated from 33 reviewed raw-workflow participants, using all four HC blocks for each participant. PCD211 is excluded because only HC1 is available. No historical Clean BP matrices are used.\n\nMethod adapted directly from `references/Step0b_Connectome_Sanity_Check_100parcels.ipynb`, group figure cell 0b.6: Fisher z each block, equal mean of HC1-HC4 per participant, double-center per participant (diagonal omitted), equal mean across participants. The reference averages EC/EO and compares demographic groups; this figure averages HC1-HC4 and presents PCD alpha/beta separately. No recording-length weighting or raw-recording concatenation.\n\nBoth pairwise-corrected and uncorrected comparison figures are generated, as in the reference. Each version uses one shared symmetric color limit across alpha/beta, defined by the 99th percentile of absolute upper-triangle group values. Colors are not fixed to -1/+1. Values outside the color limit saturate for display only; saved matrices are unchanged. Limits: "+json.dumps(limits)+".\n\nThe 100-parcel route and double-centering are descriptive visualization/QC, not a statistical significance test. This all-HC display does not estimate a perturbation effect. Existing 14-ROI and individual matrices remain unchanged. NPZ files include the group matrix, all 33 participant matrices, IDs and ordered parcel labels; provenance.json records all 264 input paths and hashes.\n",encoding="utf-8")
    print(json.dumps(dict(destination=str(DEST),participants=len(SUBJECTS),inputs=len(sources),color_limits=limits,checks=checks),indent=2))


if __name__ == "__main__":
    main()
