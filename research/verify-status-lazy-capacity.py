"""Audit the formerly rejected native refresh, and a real post-cleanse capacity bound."""
import copy,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_runtime import run_programs,PortableExecutionError
from portable_status_oracle import compare
from timer_registry_cases import NAMES
import engine_worker
s=importlib.util.spec_from_file_location('v',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
old=json.loads((R/'tests/fixtures/portable-lazy-capacity-rejection.json').read_text());old.update(stack_reference=True,status_reference=True,status_damage_reference=True)
selectors=[prefix+':'+str(n) for prefix in ('allies_top_atk','allies_top_atk_excl','allies_lowest_hp','allies_lowest_hp_excl','allies_top_def','allies_lowest_atk_burst3') for n in range(1,6)]
weapons=list(dict.fromkeys(engine_worker.META[n]['weapon_type'] for n in NAMES))
selectors += [f'allies_weapon_top_atk:{w}:{n}' for w in weapons for n in range(1,6)]
assert len(selectors)>=42
new=copy.deepcopy(old);new['name']='lazy-cache-after-cleanse-capacity';new['effects']=[];new['owners']=[]
for owner in range(4):
 group=copy.deepcopy(old['effects'][owner*51:(owner+1)*51])
 for effect,target in zip(group[8:50],selectors):effect.update(target=target,polarity='harmful')
 group.append(dict(name='clear '+str(owner),source='스킬2',type='instant',stat='debuff_cleanse',target='all_allies',trigger=copy.deepcopy(group[-1]['trigger'])))
 new['effects']+=group;new['owners'] += [owner]*len(group)
(P:=R/'tests/fixtures/portable-lazy-cleanse-capacity-rejection.json').write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
try:run_programs([v.compile_case(old),v.compile_case(new)],backend='metal')
except PortableExecutionError as error:results=error.results;evidence=error.evidence;statuses=error.statuses
else:raise AssertionError('A genuine cache-capacity rejection is required')
assert statuses==[0,64],statuses
cpu=compare(old,results[0],v.contains)
from portable_enemy_oracle import observe
native_damage=observe(old);v.contains(results[0]['target_scored_damage'],native_damage['target_scored_damage'],'formerly-rejected.native-final-damage')
(R/'research/portable-status-lazy-capacity-repair.json').write_text(json.dumps(dict(passed=True,statuses=statuses,old_input_native_valid=True,cpu=cpu,native_damage=native_damage,execution=evidence),ensure_ascii=False,indent=2)+'\n')
print('Formerly rejected input matches native state/damage; post-cleanse cache bound rejects.')
