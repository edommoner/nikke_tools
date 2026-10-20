"""Complete real Neon profiles under matching/nonmatching/unspecified global codes."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import engine_worker as adapter
from detail_coverage import body_for
from portable_roster_input import compile_static_battle
from portable_runtime import run_programs
spec=importlib.util.spec_from_file_location('roster',R/'scripts/verify-portable-roster-battles.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
tracked=[p for folder in ('app','scripts') for p in (R/folder).glob('*.py')]
tracked += [p for folder in ('calculator','runner','data') for p in (R/'research/upstream/nikke-calc-master'/folder).rglob('*') if p.suffix in ('.py','.json')]
hashes={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(tracked))}
plans=[]
for code in ('작열','풍압',None):
    for grown in (False,True):
        body={**body_for(v.roster_for('네온 : 블루 오션'),duration=180,grown=grown),'burst_gauge_mode':'accumulate'}
        body['enemy']['code']=code
        prepared=adapter.evaluate({**body,'_portable_static_inputs':True});assert not prepared['cpu_battle_executed'] and prepared['all_character_effects_included']
        assert prepared['enemy'].get('code')==code,'Authored enemy code changed during preparation'
        program=compile_static_battle(prepared,trace='burst');plans.append((code,grown,body,prepared,program))
rows=[];batches=[]
for begin in range(0,len(plans),2):
    selected=plans[begin:begin+2];output=run_programs([p[4] for p in selected],backend='metal');results=output.pop('results');batches.append(output)
    for (code,grown,body,prepared,program),gpu in zip(selected,results):
        native=v.reference.native_reference(copy.deepcopy(body));diff=v.reference.compare_native_result(gpu,prepared,native,program=program)
        rows.append(dict(character='네온 : 블루 오션',enemy_code=code,grown=grown,passed=not diff,differences=diff,gpu_result=gpu,native_reference=native,all_character_effects_included=True,cpu_trace_used_as_gpu_input=False))
    report=dict(passed=len(rows)==len(plans) and all(r['passed'] for r in rows),complete=len(rows)==len(plans),cases=rows,gpu_batches=batches,tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),validation_sha256=hashes,scope='Complete180-second simple-boss auto/expected profiles with all prepared effects; CPU battles only after readback. Not all variants or full catalog.')
    (R/'research/portable-enemy-code-real-metal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Real enemy codes',[(r['enemy_code'],r['grown'],r['passed'],r['differences']) for r in rows],flush=True)
assert hashes=={path:hashlib.sha256((R/path).read_bytes()).hexdigest() for path in hashes}
raise SystemExit(0 if report['passed'] else 1)
