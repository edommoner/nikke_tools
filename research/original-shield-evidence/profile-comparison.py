import sys,json,time,importlib.util,hashlib
from pathlib import Path
r=Path.cwd();sys.path[:0]=[str(r/'app'),str(r/'research'),str(r/'scripts')]
s=importlib.util.spec_from_file_location('profile_benchmark',r/'research/verify-coordinate-original-shield-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
from world_coordinate_sampled_skill_native import creation_indices
from native_python_profile import RECEIPTS
from nikke_gpu import forbid_gpu
who=sys.argv[1];out=Path(sys.argv[2]);row=next(x for x in a.fixtures() if x['name'].endswith('/'+who+'/chipped'));c,p=a.prepare_case(row);c['shield_witness']=row['shield_witness'];w,m,b,d=a.compile_coordinate_battle(p);domain=(c,m,b,d);runs=[]
for enabled in (False,True):
 c['python_observers_only']=enabled;start=time.monotonic()
 with forbid_gpu(),creation_indices(c) as indices:n=a.native_reference(domain)
 runs.append(dict(enabled=enabled,seconds=time.monotonic()-start,native_sha256=a.cross.digest(n),receipts=RECEIPTS[-1:] if enabled else []));print(json.dumps(runs[-1]),flush=True)
 out.write_text(json.dumps(dict(case=row['name'],runs=runs,gpu_calls=0,calculation_verified=False),indent=2))
assert runs[0]['native_sha256']==runs[1]['native_sha256'],'All native fields and observations must match'
out.write_text(json.dumps(dict(case=row['name'],runs=runs,full_native_observation_equal=True,gpu_calls=0,calculation_verified=False),indent=2))
