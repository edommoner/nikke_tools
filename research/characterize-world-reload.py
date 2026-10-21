"""Save full native reload behavior without GPU work."""
import hashlib,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
import engine_worker,portable_backend
from world_reload_cases import fixtures
from world_reload_native import observe

def main():
 def forbidden(*a,**kw):raise AssertionError('GPU forbidden in native characterization')
 with patch.object(portable_backend,'build',forbidden),patch.object(portable_backend,'execute',forbidden):rows=[dict(name=c['name'],case=c,native=n,skill_trace=t) for c in fixtures() for n,t in [observe(c)]]
 report=dict(passed=True,native_battles=len(rows),cases=rows,gpu_calls=0,typed_force_reload=False,typed_fixed_reload_time=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('research/world_reload_cases.py','research/world_reload_native.py','research/world_frame_native.py','app/weapon_mode_runtime.py')})
 (ROOT/'research/portable-world-reload-native-contract.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('Full native reload contracts',len(rows),'GPU0')
if __name__=='__main__':main()
