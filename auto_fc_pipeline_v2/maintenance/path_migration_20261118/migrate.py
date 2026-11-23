"""One-time same-depth v2 directory migration; preserve numerical data."""
from pathlib import Path
import importlib.util, re, os, sys, json
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
V2=PROJECT/'auto_fc_pipeline_v2'
spec=importlib.util.spec_from_file_location('migration_engine',PROJECT/'auto_fc_pipeline_v1/maintenance/path_migration_20261118/migrate_references.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.HERE=HERE
m.MOVES=[(V2/'extra_data_pipeline',V2/'PCD_output'),(V2/'outputs',V2/'TCP_output')]
m.SKIP.add('maintenance') # historical migration manifests deliberately retain former paths
m.NEEDLES=(b'extra_data_pipeline',b'outputs',b'PCD_output',b'TCP_output')

def replace(s):
    s=s.replace('extra_data_pipeline','PCD_output')
    for sep in ['\\\\','\\','/']:
        s=s.replace('auto_fc_pipeline_v2'+sep+'outputs','auto_fc_pipeline_v2'+sep+'TCP_output')
    return s

def transform(p,s):
    links={}
    if p.suffix=='.md':
        def link(match):
            target=match[1];plain=target.strip('<>')
            if re.match(r'(?:[A-Za-z]+:|#|/)',plain):return match[0]
            base,mark,anchor=plain.partition('#')
            old=(p.parent/base).resolve();new=m.mapped(old)
            if old!=new or m.mapped(p)!=p:
                dest=os.path.relpath(new,m.mapped(p).parent).replace('\\','/')+(mark+anchor if mark else '')
                token=f'__MIGRATION_LINK_{len(links)}__';links[token]=']('+('<'+dest+'>' if ' ' in dest else dest)+')';return token
            return match[0]
        s=re.sub(r'\]\(([^\n]+?)\)',link,s)
    s=replace(s)
    # ROOT is the v2 project directory in these top-level scripts, unlike RUN/HOME.
    if p.parent==V2/'scripts':
        s=re.sub(r'(\bROOT\s*/\s*[\x27\x22])outputs(?=[/\x27\x22])',r'\1TCP_output',s)
        if p.name=='run_tcp_rank_harmonized.py':s=s.replace('Writes only outputs/','Writes only TCP_output/')
    # Bare relative paths in the top-level v2 README are rooted at v2.
    if p==V2/'readme.md':
        s=re.sub(r'(?<![\w/\\])outputs/', 'TCP_output/',s)
    for a,b in links.items():s=s.replace(a,b)
    return s
m.replace=replace;m.transform=transform
if __name__=='__main__':{'prepare':m.prepare,'apply':m.apply}[sys.argv[1]]()
