"""Probe a pending raw-wire instant-list boundary without relaxing host admission."""
import copy,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_specs import LIMITS as L
from portable_runtime import run_programs
from portable_protection_oracle import observe
s=importlib.util.spec_from_file_location('probe_main',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
group=dict(name='group',source='스킬1',type='buff',stat='received_dmg_split_even',target=['self']*21,duration=-1,max_stack=1,trigger=dict(timing=['on_attack'],condition=[]))
heal=dict(name='heal',source='스킬1',type='instant',stat='heal_hp_pct',fixed_value=1,target='self',trigger=dict(timing=['event:full_reload'],condition=[]))
case=dict(name='pending-instant-list-21',effects=[group,heal],script=[[0,0,7,0,0,-1,0,0],[.1,0,19,0,0,-1,0,0],[.2,2,0,0,0,0,0,0]],environment=dict(allies=[dict(base_hp=1000,hp=100)]+[dict(base_hp=1000) for _ in range(4)]))
words,metadata=v.compile_case(case);base=L['RECIPIENT_BASE'];words[base+8:base+14]=words[base:base+6]
output=run_programs([(words,metadata)],backend='metal');result=output.pop('results')[0]
native_case=copy.deepcopy(case);native_case['effects'][1]['target']=['self']*21;cpu=observe(native_case)
actual=result['allies'][0]['hp'];expected=cpu['queries'][0]['allies'][0]['hp'];assert expected==310
report=dict(probe_completed=True,scope='Private raw-wire diagnostic; normal host admission still rejects instant target lists',source_commit='d12b365',authored_case=native_case,wire_change='Copy only the literal composite selector plan from group to heal. No CPU result supplies GPU input.',gpu_admitted_unported_instant_list=result['status']==0,expected_hp=expected,actual_hp=actual,full_instant_list_supported=result['status']==0 and actual==expected,gpu=result,native=cpu,**output)
(R/'research/portable-instant-list-admission-probe-metal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('probe_completed','gpu_admitted_unported_instant_list','full_instant_list_supported','expected_hp','actual_hp')}))
