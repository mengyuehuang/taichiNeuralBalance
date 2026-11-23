from pathlib import Path
import os, re, json, hashlib, sys, ast, zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
V1=ROOT/'auto_fc_pipeline_v1'
MOVES=[(V1/'extra_review',V1/'outputs/PCD_output'),(V1/'outputs/v1_preica_test',V1/'outputs/TCP_output')]
TEXT={'.py','.ps1','.json','.jsonl','.ndjson','.csv','.tsv','.txt','.md','.html','.js','.yaml','.yml','.toml','.ini','.cfg','.ipynb','.bat','.cmd','.xml','.log','.m'}
SKIP={'.git','__pycache__','.numba_cache','.mne_fake_home','node_modules','waveform_data'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def mapped(p):
 for a,b in MOVES:
  if p.is_relative_to(a):return b/p.relative_to(a)
 return p
def replace(s):
 for sep in ['\\\\','\\','/']:
  s=s.replace('extra_review'+sep,'outputs'+sep+'PCD_output'+sep)
  s=s.replace('v1_preica_test'+sep,'TCP_output'+sep)
 # Directory strings and documentation labels, not annotation descriptions.
 s=re.sub(r'(?<=[\x27\x22`])extra_review(?=[\x27\x22`])','outputs/PCD_output',s)
 s=re.sub(r'\bv1_preica_test\b','TCP_output',s)
 return s
def transform(p,s):
 # Rebase relative Markdown hyperlinks using their original locations.
 if p.suffix=='.md':
  links={}
  def link(m):
   target=m[1]; plain=target.strip('<>')
   if re.match(r'(?:[A-Za-z]+:|#|/)',plain):return '('+target+')'
   base,mark,anchor=plain.partition('#')
   if not base:return '('+target+')'
   old=(p.parent/base).resolve()
   new=mapped(old)
   if new!=old or mapped(p)!=p:
    dest=os.path.relpath(new,mapped(p).parent).replace('\\','/')+(mark+anchor if mark else '')
    key=f'__MIGRATION_LINK_{len(links)}__';links[key]='('+('<'+dest+'>' if ' ' in dest else dest)+')';return key
   return '('+target+')'
  s=re.sub(r'\]\(([^\n]+?)\)',lambda m:']'+link(m),s)
  s=replace(s)
  for a,b in links.items():s=s.replace(a,b)
 else:s=replace(s)
 if p.parent==MOVES[0][0]/'scripts' and p.name in {'run_five_block_pilot.py','screen_tcp_preica.py','export_tcp_screen_evidence.py'}:
  s=s.replace('Path(__file__).resolve().parents[2]','Path(__file__).resolve().parents[3]')
 if p.parent==MOVES[0][0]/'manual_preica_review_404/scripts':
  s=s.replace('Path(__file__).resolve().parents[4]','Path(__file__).resolve().parents[5]')
  s=s.replace('ROOT=HERE.parents[1]','ROOT=HERE.parents[2]').replace('ROOT = HERE.parents[1]','ROOT = HERE.parents[2]')
  if p.name=='export_selected_topographies.py':s=s.replace('HERE.parents[2]','HERE.parents[3]')
 return s
def prepare():
 edits=[]; office=[]
 count=0
 for folder,dirs,names in os.walk(ROOT):
  d=Path(folder);dirs[:]=[x for x in dirs if x not in SKIP and not (d/x).is_relative_to(HERE)]
  if d.is_relative_to(ROOT/'data'):dirs[:]=[];continue
  for name in names:
   p=d/name
   count+=1
   if count%1000==0:print('Scanning '+str(p),flush=True)
   if p.suffix in {'.xlsx','.docx','.pptx'}:
    try:
     with zipfile.ZipFile(p) as z:
      for n in z.namelist():
       if n.endswith(('.xml','.rels')) and any(t in z.read(n) for t in (b'extra_review',b'v1_preica_test')):office.append(str(p));break
    except (zipfile.BadZipFile,PermissionError):pass
   if p.suffix.lower() not in TEXT and p.name!='.gitignore':continue
   try:raw=p.read_bytes()
   except FileNotFoundError:
    raw=Path('\\\\?\\'+str(p)).read_bytes()
   if not any(token in raw for token in globals().get('NEEDLES',(b'extra_review',b'v1_preica_test'))) and mapped(p)==p:continue
   try:s=raw.decode('utf-8')
   except UnicodeDecodeError:continue
   new=transform(p,s)
   if new!=s:
    if p.suffix=='.py':ast.parse(new.lstrip('\ufeff'),filename=str(p))
    if p.suffix=='.json':json.loads(new.lstrip('\ufeff'))
    stage=HERE/'staged'/str(len(edits));stage.parent.mkdir(exist_ok=True);stage.write_bytes(new.encode('utf-8'))
    edits.append(dict(old=str(p),new=str(mapped(p)),before=hashlib.sha256(raw).hexdigest(),after=sha(stage),stage=str(stage)))
 (HERE/'edits.json').write_text(json.dumps(edits,indent=2))
 (HERE/'office_references.json').write_text(json.dumps(office,indent=2))
 print(f'Staged {len(edits)} text updates; Office files containing paths: {office}',flush=True)
 inventory=[]
 for a,b in MOVES:
  assert a.is_dir() and not b.exists()
  for p in a.rglob('*'):
   if p.is_file():inventory.append(dict(old=str(p),new=str(mapped(p)),bytes=p.stat().st_size,sha256=sha(p)))
  print(f'Hashed {a.name}: cumulative {len(inventory)} files',flush=True)
 (HERE/'move_inventory.json').write_text(json.dumps(inventory,indent=2))
def apply():
 inv=json.loads((HERE/'move_inventory.json').read_text());edits=json.loads((HERE/'edits.json').read_text())
 for x in inv:
  p=Path(x['new']);assert p.is_file() and p.stat().st_size==x['bytes'] and sha(p)==x['sha256'],x['new']
 print(f'All {len(inv)} moved files match original hashes',flush=True)
 for x in edits:assert sha(Path(x['new']))==x['before'],x['new']
 for x in edits:Path(x['new']).write_bytes(Path(x['stage']).read_bytes())
 for x in edits:assert sha(Path(x['new']))==x['after']
 (HERE/'result.json').write_text(json.dumps(dict(moved_files=len(inv),text_updates=len(edits),all_moved_hashes_verified=True),indent=2))
 print(f'Applied and verified {len(edits)} path updates',flush=True)
if __name__=='__main__':{'prepare':prepare,'apply':apply}[sys.argv[1]]()
