from pathlib import Path
import json,ast,csv
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
inventory=json.loads((HERE/'move_inventory.json').read_text())
edits=json.loads((HERE/'edits.json').read_text())
known={x['new'].replace('\\','/').lower() for x in inventory}
for x in inventory:
    for parent in Path(x['new']).parents:
        if parent==PROJECT:break
        known.add(str(parent).replace('\\','/').lower())
seen=set();errors=[];code=0;configs=0
def walk(v):
    if isinstance(v,dict):
        for k,x in v.items():walk(k);walk(x)
    elif isinstance(v,list):
        for x in v:walk(x)
    elif isinstance(v,str) and v.replace('\\','/').lower() in known:
        seen.add(v)
        if not Path(v).exists():errors.append(v)
for x in edits:
    p=Path(x['new'])
    if p.suffix=='.json':walk(json.loads(p.read_text(encoding='utf-8-sig')));configs+=1
    if p.suffix=='.csv':
        with p.open(encoding='utf-8-sig',newline='') as handle:
            for row in csv.reader(handle):walk(row)
    if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8-sig'));code+=1
for old in ['auto_fc_pipeline_v2/extra_data_pipeline','auto_fc_pipeline_v2/outputs','auto_fc_pipeline_v1/extra_review','auto_fc_pipeline_v1/outputs/v1_preica_test']:
    assert not (PROJECT/old).exists(),old
assert not errors,errors
result=dict(moved_files=len(inventory),text_updates=len(edits),referenced_moved_files_checked=len(seen),missing=errors,python_files_parsed=code,json_files_parsed=configs,old_directories_absent=True)
(HERE/'validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
