"""Every own-effect preflight candidate: complete simple-boss real profiles.
No effects are filtered. Missing/failed cases remain failed in the full matrix.
CPU battles run only after GPU readback and never supply GPU state or traces.
"""
import argparse,copy,datetime,hashlib,importlib.util,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker as adapter
from detail_coverage import body_for
from portable_roster_input import compile_static_battle
from portable_runtime import run_programs,UnsupportedPortable
import portable_runtime as runtime
from portable_conditional_hp_gap import native_reference as observe_native,verify_difference
spec=importlib.util.spec_from_file_location('portable_real_reference',ROOT/'scripts/verify-portable-real-battle.py')
reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)


def roster_for(name):
    stage=str(adapter.META[name]['burst_stage'])
    fillers={'1':['도라','드레이크','N102','메어리','미란다'],
             '2':['미란다','드레이크','N102','메어리','도라'],
             '3':['미란다','도라','N102','메어리','드레이크']}
    if stage not in fillers:raise UnsupportedPortable('Add an explicit full-roster policy for stage '+stage)
    return [name]+[n for n in fillers[stage] if n!=name][:4]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('metal','cuda'),default='metal');args=parser.parse_args()
    path=ROOT/f'research/portable-roster-battles-{args.backend}.json';start=time.perf_counter()
    tracked=[p for folder in ('app','scripts') for p in (ROOT/folder).glob('*.py')]
    tracked += [p for folder in ('calculator','runner','data') for p in (ROOT/'research/upstream/nikke-calc-master'/folder).rglob('*') if p.suffix in ('.py','.json')]
    tracked += [ROOT/'data/engine-effect-overrides.json',ROOT/'scripts/run-metal-probe.swift',ROOT/'tests/fixtures/portable-health-runtime.json']
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(tracked))}
    audit=[]
    for name,data in adapter.META.items():
        if not isinstance(data,dict) or name.startswith(('_','test_')) or adapter.spec.is_preview(name):continue
        names=[name]+[n for n in ('모더니아','루주','마스트 : 로망틱 메이드','도라','얀') if n!=name][:4]
        row=adapter.evaluate({**body_for(names),'_audit_portable':True})
        audit.append(dict(character=name,own_effect_preflight_passed=row['all_effects_preflight_passed']))
    candidates=[r['character'] for r in audit if r['own_effect_preflight_passed']]
    cases=[];programs=[];plans=[]
    for name in candidates:
        for grown in (False,True):
            row=dict(character=name,grown=grown,duration=180,passed=False)
            cases.append(row)
            try:
                body={**body_for(roster_for(name),duration=180,grown=grown),'burst_gauge_mode':'accumulate'}
                prepared=adapter.evaluate({**body,'_portable_static_inputs':True});program=compile_static_battle(prepared,trace='burst')
            except (UnsupportedPortable,ValueError,KeyError) as error:row['compile_error']=str(error)
            else:
                row.update(squad=body['squad'],prepared_effects=len(prepared['effects']),cpu_battle_executed_for_gpu_input=prepared['cpu_battle_executed'])
                programs.append(program);plans.append((len(cases)-1,body,prepared))
    report=dict(passed=False,stage='gpu-execution-pending',audit=audit,candidates=candidates,required_cases=len(cases),cases=cases,validation_sha256=hashes,
        real_prepared_input_connected=True,normal_ui_connected=False,full_character_verified=0,all_character_effects_included=True,cpu_trace_used_as_gpu_input=False,
        scope='Every own-effect-preflight candidate, two 180-second simple-boss auto/expected profiles, favorite0/no cube; not all variants or full catalog',gpu_batches=[])
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    readbacks=[]
    for begin in range(0,len(programs),4):
        batch_start=time.perf_counter();original_dispatch=runtime.dispatch_programs;captured={}
        def retain(items,**kwargs):
            folder=ROOT/'research/portable-build'/('roster-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
            (folder/'input.bin').write_bytes(runtime.pack_programs(items))
            raw,evidence=original_dispatch(items,**kwargs)
            (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
            captured.update(input_path=str(folder/'input.bin'),readback_path=str(folder/'readback.bin'))
            return raw,evidence
        runtime.dispatch_programs=retain
        try:out=run_programs(programs[begin:begin+4],backend=args.backend)
        finally:runtime.dispatch_programs=original_dispatch
        report['gpu_batches'].append(dict(case_indices=[p[0] for p in plans[begin:begin+4]],wall_seconds=time.perf_counter()-batch_start,captured=captured,**{k:v for k,v in out.items() if k!='results'}))
        readbacks.extend(out['results'])
        report['stage']='gpu-readback-progress';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    report['stage']='original-CPU-comparison';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for (index,body,prepared),gpu in zip(plans,readbacks):
        row=cases[index];cpu_start=time.perf_counter()
        try:
            cpu,evidence=observe_native(copy.deepcopy(body),prepared,reference.native_reference);diff=reference.compare_native_result(gpu,prepared,cpu)
            known=verify_difference(diff,evidence)
            if known is not None:row['known_cpu_difference']=known;diff=[]
        except (AssertionError,ValueError,KeyError) as error:row.update(verification_error=str(error),passed=False)
        else:row.update(passed=not diff,differences=diff,native_reference=cpu,gpu_result=gpu)
        row['cpu_reference_wall_seconds']=time.perf_counter()-cpu_start
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in hashes}
    report['known_cpu_difference_cases']=[dict(character=c['character'],grown=c['grown'],evidence=c['known_cpu_difference']) for c in cases if 'known_cpu_difference' in c]
    report.update(passed=bool(cases) and all(r['passed'] for r in cases),stage='verified' if all(r['passed'] for r in cases) else 'real-roster-gaps',elapsed_wall_seconds=time.perf_counter()-start)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],candidates=len(candidates),required_cases=len(cases),passed_cases=sum(c['passed'] for c in cases),failed=[{k:v for k,v in c.items() if k not in ('native_reference','gpu_result')} for c in cases if not c['passed']]),ensure_ascii=False))
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
