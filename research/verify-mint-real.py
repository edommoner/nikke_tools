"""Unfiltered real Mint profiles: native battle is evaluated after GPU readback."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import engine_worker as adapter
from detail_coverage import body_for
from portable_roster_input import compile_static_battle
from portable_runtime import run_programs
spec=importlib.util.spec_from_file_location('roster',R/'scripts/verify-portable-roster-battles.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
plans=[]
for grown in (False,True):
    body={**body_for(v.roster_for('민트'),duration=180,grown=grown),'burst_gauge_mode':'accumulate'}
    prepared=adapter.evaluate({**body,'_portable_static_inputs':True});assert not prepared['cpu_battle_executed'] and prepared['all_character_effects_included']
    plans.append((body,prepared,compile_static_battle(prepared,trace='burst')))
output=run_programs([p[2] for p in plans],backend='metal');results=output.pop('results');rows=[]
for grown,(body,prepared,_),gpu in zip((False,True),plans,results):
    native=v.reference.native_reference(copy.deepcopy(body));diff=v.reference.compare_native_result(gpu,prepared,native)
    rows.append(dict(character='민트',grown=grown,passed=not diff,differences=diff,gpu_result=gpu,native_reference=native,all_character_effects_included=True,cpu_trace_used_as_gpu_input=False,base_weapon_types=[w['base_weapon_type'] for w in prepared['weapons']]))
report=dict(passed=all(r['passed'] for r in rows),cases=rows,scope='Two complete180-second simple-boss auto/expected profiles, all prepared effects; not all variants or full catalog.',tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),**output)
(R/'research/portable-mint-real-metal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('Mint real profiles',[(r['grown'],r['passed'],r['differences']) for r in rows]);raise SystemExit(0 if report['passed'] else 1)
