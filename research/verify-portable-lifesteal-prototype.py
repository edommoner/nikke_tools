import sys,json,copy,importlib.util,hashlib,argparse
from pathlib import Path
sys.path[:0]=['app','scripts'];sp=importlib.util.spec_from_file_location('v','scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
from portable_lifesteal_oracle import observe
from portable_runtime import run_programs,UnsupportedPortable
from portable_specs import LIMITS as L,FIELDS as F
parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('metal','cuda'),default='metal');args=parser.parse_args()
cs=json.load(open('tests/fixtures/portable-lifesteal-prototype.json'))['cases'];programs=[];native=[]
for c in cs:
 n=observe(c);v.contains(n['queries'],c['expected_queries'],c['name']+'.hand-native');native.append(n)
 print('native',c['name'],n['queries'][0]['allies'][0]['hp'],flush=True)
 programs.append(v.compile_case(c))
r=run_programs(programs,backend=args.backend);p=Path(f'research/portable-lifesteal-focused-{args.backend}.json');r['passed']=False;p.write_text(json.dumps(r,indent=2)+'\n')
for c,n,g in zip(cs,native,r['results']):v.contains(g['queries'],n['queries'],c['name']+'.native');v.contains(g['queries'],c['expected_queries'],c['name']+'.hand')
r.update(passed=True,cases=[dict(name=c['name'],passed=True,native=n) for c,n in zip(cs,native)],scope='Working wire-only normal landing/recovery prototype; production admission closed; queued skill/pending paths not connected; not full battle/catalog certification',validation_sha256={n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in ['app/portable_lifesteal_reference.py','scripts/portable_lifesteal_oracle.py','tests/fixtures/portable-lifesteal-prototype.json']});p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('Lifesteal normal prototype passed',len(cs))
