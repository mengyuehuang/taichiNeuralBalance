"""Update only Excel's saved-directory metadata, never cells/styles/formulas."""
import json,re,zipfile,io,hashlib,base64
from pathlib import Path
from migrate_references import HERE,mapped,sha

records=[]
for old in json.loads((HERE/'office_references.json').read_text()):
    p=mapped(Path(old));before=sha(p)
    with zipfile.ZipFile(p) as z:
        entries=[(info,z.read(info.filename)) for info in z.infolist()]
    original=dict((i.filename,b) for i,b in entries)
    xml=original['xl/workbook.xml'].decode('utf-8')
    new,n=re.subn(r'(<(?:\w+:)?absPath\b[^>]*\burl=")[^"]*(")',lambda m:m[1]+str(p.parent)+'\\'+m[2],xml)
    assert n==1,str(p)
    assert 'extra_review' not in new and 'v1_preica_test' not in new
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as out:
        for info,b in entries:out.writestr(info,new.encode('utf-8') if info.filename=='xl/workbook.xml' else b)
    with zipfile.ZipFile(stream) as test:
        assert test.testzip() is None
        assert test.namelist()==list(original)
        for name,b in original.items():
            if name!='xl/workbook.xml':assert test.read(name)==b,(p,name)
    assert sha(p)==before
    p.write_bytes(stream.getvalue())
    records.append(dict(path=str(p),before_sha256=before,after_sha256=sha(p),old_workbook_xml_b64=base64.b64encode(original['xl/workbook.xml']).decode(),unchanged_parts=len(entries)-1))
(HERE/'excel_metadata_updates.json').write_text(json.dumps(records,indent=2))
print(f'Updated saved-directory metadata in {len(records)} workbooks; every other ZIP entry is byte-identical.')
