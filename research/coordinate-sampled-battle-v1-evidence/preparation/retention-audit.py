import subprocess,json,hashlib
from pathlib import Path
PYTHON='/Users/edo/Documents/ChatGPT/nikke_tools/.venv/bin/python'
script='''import importlib.util,sys,json
from pathlib import Path
R=Path.cwd();sys.path[:0]=[str(R/'app'),str(R/'research')]
s=importlib.util.spec_from_file_location('cli',R/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
with cli.forbid_gpu():
 a=cli.open_suite(dict(suite='coordinate-sampled-battle'));entries,_=a.prepare();rows=[]
 for name,words,domain in entries[:11]:rows.append(dict(name=name,input_sha256=hashlib.sha256(__import__('array').array('I',words).tobytes()).hexdigest(),native=a.native_reference(domain)))
Path(sys.argv[1]).write_text(json.dumps(rows))
'''.replace('import importlib.util,sys,json','import importlib.util,sys,json,hashlib')
values=[]
for suffix in ['v1','v3']:
 output=Path('/tmp/nikke-sampled-battle-retained-native-'+suffix+'.json');assert not output.exists()
 subprocess.run([PYTHON,'-c',script,str(output)],cwd='/tmp/nikke-sampled-battle-develop-'+suffix,check=True);values.append(json.loads(output.read_text()))
old,new=values
for a,b in zip(old,new,strict=True):
 assert a['name']==b['name'] and a['input_sha256']==b['input_sha256'];x=a['native'];y=b['native'];assert set(y)-set(x)=={'sampled_draws'}
 assert {k:v for k,v in x.items() if k!='scope'}=={k:y[k] for k in x if k!='scope'},a['name']
assert Path('/tmp/nikke-sampled-battle-metal-v1/result.json').exists() and Path('/tmp/nikke-sampled-battle-metal-v3/result.json').exists()
N=11*1507328*4;left=hashlib.sha256();right=hashlib.sha256()
with Path('/tmp/nikke-sampled-battle-metal-v1/readback.bin').open('rb') as a,Path('/tmp/nikke-sampled-battle-metal-v3/readback.bin').open('rb') as b:
 remaining=N
 while remaining:
  n=min(8388608,remaining);x=a.read(n);y=b.read(n);assert len(x)==len(y)==n and x==y;left.update(x);right.update(y);remaining-=n
out=dict(passed=True,retained_inputs=11,retained_raw_bytes=N,raw_prefix_sha256=left.hexdigest(),old11_inputs_identical=True,all_original_native_fields_except_scope_identical=True,added_observation_only=['sampled_draws'],scope_metadata_updated=True,old_native_proofs_rebound=False,gpu_calls=0,calculation_verified=False)
Path('/tmp/nikke-sampled-battle-retention-v3.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
