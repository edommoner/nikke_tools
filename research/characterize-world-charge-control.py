"""Freeze actual full-native manual charge/hold contracts; GPU0."""
import hashlib,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
import engine_worker
from world_charge_control_cases import fixtures
from world_charge_control_native import observe

def main():
 rows=[]
 with patch('portable_backend.build',side_effect=AssertionError('GPU build forbidden')),patch('portable_backend.execute',side_effect=AssertionError('GPU execute forbidden')):
  for c in fixtures():
   try:n,t=observe(c);rows.append(dict(name=c['name'],case=c,native=n,skill_trace=t,error=None))
   except ValueError as e:rows.append(dict(name=c['name'],case=c,error=str(e)))
 report=dict(passed=False,cases=rows,native_battles=sum(c['error'] is None for c in rows),native_runtime_rejections=sum(c['error'] is not None for c in rows),authored_cases=len(rows),gpu_calls=0,typed_manual_charge_hold=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('research/world_frame_native.py','research/world_charge_control_cases.py','research/world_charge_control_native.py','research/world_team_native.py','research/world_skill_native.py','app/weapon_mode_runtime.py')})
 p=ROOT/'research/portable-world-charge-control-native-contract.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 errors=[c for c in rows if c['error']];assert len(errors)==1 and errors[0]['name']=='manual-charge-simultaneous-strict',[(c['name'],c['error']) for c in errors]
 report['passed']=True;p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('Manual charge native',len(rows)-1,'battles;strict collision1;GPU0')
if __name__=='__main__':main()
