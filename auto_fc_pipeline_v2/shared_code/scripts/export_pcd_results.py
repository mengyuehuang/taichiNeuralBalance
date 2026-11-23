"""Package reviewed PCD matrices and QC for sharing; original files are unchanged."""
from pathlib import Path
import argparse, hashlib, json, re, shutil, zipfile
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/"auto_fc_pipeline_v2/output/PCD_output"

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name",required=True,help="New delivery folder name (letters, numbers, underscores)")
    args=parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_]+",args.name):raise ValueError("Invalid delivery name")
    dest=ROOT/"deliverables"/args.name
    if dest.exists() or dest.with_suffix(".zip").exists():raise FileExistsError("Delivery already exists; use a new name")
    cohort=json.loads((BASE/"group_fc_display/provenance.json").read_text())["participants"]
    assert len(cohort)==33 and len(set(cohort))==33
    dest.mkdir(parents=True);manifest=[]
    def copy(src,relative):
        target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
        sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        digest=sha(src);assert sha(target)==digest
        manifest.append(dict(file=target.relative_to(dest).as_posix(),source=str(src),bytes=target.stat().st_size,sha256=digest))
    matrix_count=0
    for sid in cohort:
        candidates=[p for p in (BASE/"outputs").glob(sid+"_epoch_union_*") if re.fullmatch(sid+r"_epoch_union_\d{8}",p.name)]
        assert len(candidates)==1,(sid,candidates)
        run=candidates[0];participant=run/"outputs"/sid
        matrices=list((participant/"04_static_fc").rglob("*.npz"));assert len(matrices)==24,(sid,len(matrices));matrix_count+=len(matrices)
        for sub in [participant/"04_static_fc",run/"quality_review"]:
            assert sub.is_dir(),sub
            for f in sub.rglob("*"):
                if f.is_file():copy(f,Path("participants")/sid/sub.name/f.relative_to(sub))
        for f in run.iterdir():
            if f.is_file() and f.suffix in [".json",".md"]:copy(f,Path("participants")/sid/"run_metadata"/f.name)
        for f in (participant/"02_source_model").glob("*.json"):
            copy(f,Path("participants")/sid/"source_model_audit"/f.name)
    for f in (BASE/"group_fc_display").rglob("*"):
        if f.is_file():copy(f,Path("group_fc_display")/f.relative_to(BASE/"group_fc_display"))
    for name in ["README.md","participant_policy.json","raw_review_fc_diagnostics.md"]:copy(BASE/name,Path("documentation")/name)
    readme=f"""# Reviewed PCD results delivery

33 participants; 132 HC blocks; {matrix_count} individual FC matrix NPZ files (396 per route).

- `participants/PCDxxx/04_static_fc`: complete individual FC exports, CSVs and summary figures; broadband, alpha and beta; HC1-HC4.
- `participants/PCDxxx/quality_review`: temporal split-half metrics and retained-waveform/PSD figures.
- `participants/PCDxxx/run_metadata` and `source_model_audit`: available run configs, provenance, validation and rank records.
- `group_fc_display`: reviewed alpha/beta group figures, numeric matrices, old/new matched comparison, and 262 small historical input matrices used to reproduce the comparison.
- `documentation`: cohort policy, processing history and rank/stability register. Historical local links/paths in copied metadata are provenance and may not resolve on another computer.

Primary route: symmetric 14-ROI FC. Schaefer-100 pairwise FC and group plots are descriptive visualization/QC. Group plots use Fisher z per HC, equal four-HC mean per participant, reference double-centering, then equal participant mean. PCD211 is excluded because it has only HC1. PCD103/104/107/202/210 are excluded by documented policy; PCD108 is unavailable in the local raw manifest.

Two recordings were combined for PCD101 HC4, PCD102 HC1 and PCD208 HC4. These approved combinations are complete: acquisitions were processed separately, recording boundaries preserved and gaps excluded from observations. PCD101 run01 has an incomplete TTL time code, limiting timing-continuity verification, not processing completion. PCD109 HC4 uses only HC4_2. Each participant counts once.

This is a results-sharing package, not a complete processing backup: raw EEG, cleaned time series, ICA fits/review workbooks and large source-model files remain in the main workspace and are not included. Do not delete production inputs based on this package alone. Scripts are shared separately through Git.

`file_manifest.json` contains copied-file SHA-256 hashes and original paths. The ZIP is CRC-tested after creation, and its SHA-256 is written alongside it. No Drive upload is performed by this script.
"""
    (dest/"README.md").write_text(readme,encoding="utf-8")
    (dest/"file_manifest.json").write_text(json.dumps(dict(participants=cohort,individual_matrix_count=matrix_count,files=manifest),indent=2),encoding="utf-8")
    archive=dest.with_suffix(".zip")
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
        for f in dest.rglob("*"):
            if f.is_file():z.write(f,arcname=(Path(dest.name)/f.relative_to(dest)).as_posix())
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".zip.sha256").write_text(digest+"  "+archive.name+"\n")
    print(json.dumps(dict(folder=str(dest),zip=str(archive),zip_bytes=archive.stat().st_size,copied_files=len(manifest),individual_matrix_count=matrix_count,sha256=digest,crc_test="passed"),indent=2))

if __name__=="__main__":main()
