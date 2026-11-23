"""Descriptive old/new PCD group FC comparison; no automatic quality verdict."""
from pathlib import Path
import json, hashlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from refresh_fc_display import ROOT, SUBJECTS, fisher_z, double_center

BASE=ROOT/"output/PCD_output"
DEST=BASE/"group_fc_display/comparison_old_new"
OLD=BASE/"group_fc_display/comparison_old_new/legacy_matrix_inputs"
NEW=BASE/"group_fc_display"

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    provenance=json.loads((NEW/"provenance.json").read_text())
    old_ids=sorted(SUBJECTS+["PCD211"])
    rows={};sources=[];groups={};stats={}
    names=np.load(NEW/"PCD_alpha_pairwise_group_fc.npz")["parcel_names"].astype(str)
    labels=[n.split("_")[1]+" "+n.split("_")[2] for n in names]
    iu=np.triu_indices(100,1)
    same=np.array([labels[i]==labels[j] for i,j in zip(*iu)])
    hemi=np.array([names[i].split("_")[1]==names[j].split("_")[1] for i,j in zip(*iu)])
    def load(p):
        with np.load(p) as d:
            order=[list(d["parcel_names"].astype(str)).index(n) for n in names]
            x=d["fc100_signed"][np.ix_(order,order)]
        assert np.isfinite(x[iu]).all()
        return fisher_z(x)
    def metrics(stack):
        edges=stack[:,iu[0],iu[1]]
        mean=edges.mean(0)
        loo=[float(np.corrcoef(x,(edges.sum(0)-x)/(len(edges)-1))[0,1]) for x in edges]
        rng=np.random.default_rng(20261121);split=[]
        for _ in range(500):
            q=rng.permutation(len(edges));k=len(q)//2
            split.append(float(np.corrcoef(edges[q[:k]].mean(0),edges[q[k:]].mean(0))[0,1]))
        return dict(group_subject_split_r_median=float(np.median(split)),group_subject_split_r_5_95=np.percentile(split,[5,95]).tolist(),leave_one_out_r_median=float(np.median(loo)),within_network_same_hemi_minus_between_network_same_hemi=float(mean[same].mean()-mean[hemi & ~same].mean()),edge_sd=float(mean.std()))
    for band in ["alpha","beta"]:
        old={};new={};matched_old=[];matched_new=[];blocks={}
        for sid in old_ids:
            files=sorted((OLD/sid/"04_static_fc/pairwise_100parcels").glob(f"{sid}_HC*_{band}_fc.npz"))
            assert files
            zs=[];hcs=[]
            for p in files:
                hc=p.name.split("_")[1];hcs.append(hc);zs.append(load(p))
                sources.append(dict(version="old",subject=sid,band=band,block=hc,path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
            old[sid]=double_center(np.mean(zs,axis=0));blocks[sid]=hcs
            if sid in SUBJECTS:
                matched_old.append(old[sid]); nz=[]
                for hc in hcs:
                    selected=[x for x in provenance["sources"] if x["subject"]==sid and x["band"]==band and x["block"]==hc]
                    assert len(selected)==1;nz.append(load(Path(selected[0]["file"])))
                matched_new.append(double_center(np.mean(nz,axis=0)))
        d=np.load(NEW/f"PCD_{band}_pairwise_group_fc.npz")
        np.testing.assert_array_equal(d["participant_ids"],SUBJECTS)
        stacks=dict(old_actual=np.array(list(old.values())),new_actual=d["participant_centered_fisher_z"],old_matched=np.array(matched_old),new_matched=np.array(matched_new))
        groups[band]={k:v.mean(0) for k,v in stacks.items()}
        stats[band]={k:metrics(v) for k,v in stacks.items()}
        for suffix in ["actual","matched"]:
            a,b=groups[band]["old_"+suffix][iu],groups[band]["new_"+suffix][iu]
            stats[band][suffix+"_old_new_edge_r"]=float(np.corrcoef(a,b)[0,1])
            stats[band][suffix+"_rms_difference"]=float(np.sqrt(np.mean((b-a)**2)))
        rows[band]=blocks
        np.savez_compressed(DEST/f"{band}_comparison.npz",**groups[band],parcel_names=names,matched_participant_ids=np.array(SUBJECTS),old_participant_ids=np.array(old_ids))
    starts=[i for i in range(100) if i==0 or labels[i]!=labels[i-1]]
    ticks=(np.array(starts)+np.array(starts[1:]+[100])-1)/2
    limits={}
    for mode in ["actual","matched"]:
        lim=float(np.percentile(np.abs(np.concatenate([groups[b][v+"_"+mode][iu] for b in groups for v in ["old","new"]])),99));limits[mode]=lim
        fig,axes=plt.subplots(2,2,figsize=(13,13))
        for row,v in enumerate(["old","new"]):
            for col,band in enumerate(groups):
                ax=axes[row,col];m=groups[band][v+"_"+mode]
                im=ax.imshow(m,cmap="RdBu_r",vmin=-lim,vmax=lim,interpolation="nearest")
                ax.xaxis.tick_top();ax.set_xticks(ticks,[labels[i] for i in starts],rotation=90,fontsize=7);ax.set_yticks(ticks,[labels[i] for i in starts],fontsize=7);ax.tick_params(length=0)
                ax.axhline(49.5,color="black",lw=.7);ax.axvline(49.5,color="black",lw=.7)
                n=34 if mode=="actual" and v=="old" else 33
                ax.set_xlabel(f"{v.title()} PCD {band} | n={n}",fontsize=12)
        fig.subplots_adjust(left=.09,right=.87,top=.86,bottom=.07,wspace=.30,hspace=.43)
        cax=fig.add_axes([.91,.24,.017,.50]);fig.colorbar(im,cax=cax,extend="both",label="Centered Fisher z | shared scale")
        fig.suptitle("PCD old vs reviewed | pairwise-corrected Schaefer-100",fontsize=15,y=.985)
        subtitle="Historical 34 participants vs reviewed 33 participants" if mode=="actual" else "Matched 33 participants and HC availability; PCD208 uses HC1-HC3 in both"
        fig.text(.5,.95,subtitle,ha="center",fontsize=10)
        fig.text(.5,.025,"Same reference averaging and centering. Shared 99th-percentile color scale; descriptive comparison, not a quality test.",ha="center",fontsize=9)
        fig.savefig(DEST/f"old_new_{mode}.png",dpi=160);fig.savefig(DEST/f"old_new_{mode}.pdf");plt.close(fig)
    result=dict(metrics=stats,color_limits=limits,old_block_availability=rows,old_sources=sources,new_provenance=str(NEW/"provenance.json"),limitations=["Legacy provided Clean BP vs reviewed raw workflow; input/projection policy, channel and interval decisions differ.","Matched comparison controls subject IDs and HC availability, not clean durations or run selection within HC.","Group subject-split stability is different from temporal split-half stability within a recording.","Strong network structure or group reproducibility alone cannot establish artifact-free or more accurate brain connectivity."])
    (DEST/"comparison_metrics.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    text="# PCD old/new group comparison\n\nHistorical group reconstructed from rank_corrected provided-Clean-BP matrices (34 participants, excluding historical PCD107 but including HC1-only PCD211). This reconstructs the documented old plotting inputs; the exact screenshot provenance is not independently established. The reviewed group uses 33 completed epoch-union participants.\n\nBoth versions use reference Fisher z per block, equal available-block average, participant double-centering, and equal participant averaging. `old_new_actual.png` compares actual cohorts; `old_new_matched.png` matches the same 33 people and HC availability (PCD208 HC1-HC3 only). Each figure uses a shared data-derived scale across all four panels. Extreme colors saturate at the 99th percentile; numeric matrices are not clipped.\n\n| Band | Matched old/new edge r | Old / new subject-split median r | Old / new leave-one-out median r | Old / new within-minus-between network z |\n|---|---:|---|---|---|\n"
    for b,s in stats.items():
        a,c=s["old_matched"],s["new_matched"]
        text+=f"| {b} | {s['matched_old_new_edge_r']:.3f} | {a['group_subject_split_r_median']:.3f} / {c['group_subject_split_r_median']:.3f} | {a['leave_one_out_r_median']:.3f} / {c['leave_one_out_r_median']:.3f} | {a['within_network_same_hemi_minus_between_network_same_hemi']:.4f} / {c['within_network_same_hemi_minus_between_network_same_hemi']:.4f} |\n"
    text+="\nSubject-split uses 500 identical seeded random splits of participants, not time halves. Within/between contrasts compare networks within the same hemisphere. These metrics assess descriptive structure and reproducibility, not artifact removal accuracy or statistical improvement. Differences in legacy projection policy, preprocessing and retained acquisitions remain.\n"
    (DEST/"README.md").write_text(text,encoding="utf-8")
    print(json.dumps(stats,indent=2))

if __name__=="__main__":main()
