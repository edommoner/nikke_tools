"""Native births justify every prior raw timestamp correction after GPU readback."""
import copy,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/d) for d in ('app','scripts')]
s=importlib.util.spec_from_file_location('v',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from portable_enemy_oracle import observe as enemy
from portable_pending_oracle import observe as pending
cases={c['name']:c for c in v.fixtures()};result=json.loads((R/'research/portable-combat-metal.json').read_text());gpu={c['name']:r for c,r in zip(result['cases'],result['results'])}
contract=json.loads((R/'research/portable-stack-previous-output-contract.json').read_text());rows=[]
for change in contract['changed_cases']:
 c=copy.deepcopy(cases[change['name']]);c['inspect_carrier_activation']=True
 if not c.get('pending_reference') and any(w.get('enabled',False) for w in c['combat']['weapons']):c['inspect_physical_frames']=True
 from portable_carrier_observer import capture
 with capture():native=(pending if c.get('pending_reference') else enemy)(c)
 carriers=[]
 for word in change['words']:
  assert word['field']=='carrier.activated'
  from portable_specs import LIMITS as L
  index=(word['word']-L['CARRIER_STATE_BASE'])//L['CARRIER_WORDS']
  carrier=gpu[c['name']]['carriers'][index];observed=native['carrier_births'][carrier['order']-1]
  assert observed['definition']==carrier['definition'] and observed['activated']==carrier['activated'],(c['name'],carrier,observed,native['carrier_births'])
  if not carriers or carriers[-1]!=observed:carriers.append(observed)
 rows.append(dict(name=c['name'],passed=True,native_carriers=carriers,all_native_births=native['carrier_births']))
assert len(rows)==18
(R/'research/portable-stack-prior-native-timestamps.json').write_text(json.dumps(dict(passed=True,cases=rows,cpu_trace_used_as_gpu_input=False,scope='Every changed prior timestamp word matched the corresponding independent native carrier birth order and definition.'),indent=2)+'\n');print('All 18 prior timestamp corrections matched native births')
