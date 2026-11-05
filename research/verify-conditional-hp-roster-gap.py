"""CPU-only diagnosis using retained full decoded failed real profiles."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
s=importlib.util.spec_from_file_location('roster',ROOT/'scripts/verify-portable-roster-battles.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from portable_conditional_hp_gap import native_reference,verify_difference
old=json.loads((ROOT/'research/portable-attack-flags-first-roster-metal.json').read_text());rows=[]
for c in old['cases']:
 if c['passed']:continue
 body={**v.body_for(v.roster_for(c['character']),duration=180,grown=c['grown']),'burst_gauge_mode':'accumulate'}
 p=v.adapter.evaluate({**body,'_portable_static_inputs':True});assert not p['cpu_battle_executed']
 cpu,evidence=native_reference(body,p,v.reference.native_reference)
 # Passthrough observation must preserve the original CPU result completely.
 assert cpu==c['native_reference']
 difference=v.reference.compare_native_result(c['gpu_result'],p,cpu)
 assert difference==c['differences']
 known=verify_difference(difference,evidence);assert known is not None
 rows.append(dict(character=c['character'],grown=c['grown'],known_cpu_difference=known))
assert len(rows)==2
paths=['research/verify-conditional-hp-roster-gap.py','scripts/portable_conditional_hp_gap.py',
       'tests/fixtures/portable-health-runtime.json','research/portable-health-runtime-metal.json']
report=dict(passed=True,cpu_only_replay=True,gpu_reexecuted=False,cases=rows,initial_raw_readback_missing=True,
 source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
 scope='CPU passthrough produces the exact original native result;strict contract accounts for only the10 observed HP fields per profile;other fields unchanged')
(ROOT/'research/portable-conditional-hp-roster-diagnosis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('2 real profiles diagnosed:original CPU results unchanged;only10 exact HP fields differ in each')
