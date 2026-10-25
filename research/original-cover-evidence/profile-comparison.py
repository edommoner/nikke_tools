import sys,json,time,importlib.util
from pathlib import Path
r=Path.cwd();sys.path[:0]=[str(r/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('profile_benchmark',r/'research/verify-coordinate-original-cover-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
from world_coordinate_sampled_skill_native import creation_indices
from native_python_profile import RECEIPTS
from nikke_gpu import forbid_gpu
who,raw_enabled,out=sys.argv[1:];enabled=raw_enabled=='true';row=next(x for x in a.fixtures() if x['name'].endswith('/'+who+'/pool'));c,p=a.prepare_case(row);c['cover_witness']=row['cover_witness'];c['python_observers_only']=enabled;w,m,b,d=a.compile_coordinate_battle(p);start=time.monotonic()
with forbid_gpu(),creation_indices(c) as indices:n=a.native_reference((c,m,b,d))
result=dict(case=row['name'],enabled=enabled,seconds=time.monotonic()-start,native_sha256=a.cross.digest(n),creation_indices_sha256=a.cross.digest(indices),receipts=RECEIPTS[-1:] if enabled else [],gpu_calls=0,calculation_verified=False)
Path(out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='receipts'}),flush=True)
