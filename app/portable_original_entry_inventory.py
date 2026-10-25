"""CPU-only full original coordinate packing and literal kind catalog, not admission."""
import array,collections,copy,hashlib,json,sys,time
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
from portable_original_identity_inventory import prepared_profiles

def run(output,*,write,forbid_gpu):
    output=Path(output)
    with output.open('x',encoding='utf-8') as stream:stream.write('{}\n')
    started=time.perf_counter();calls=dict(cpu_battle=0,gpu=0)
    report=dict(schema=1,stage='static-original-coordinate-inputs',passed=False,profiles=[],definition_kind_profiles={},forbidden_calls=calls,
        calculation_verified=False,gpu_admission_verified=False,full_character_verified=0,full_goal_complete=False,
        scope='Default-growth/no-cube complete original rosters, all base/favorite stages; literal idle coordinate world; static packing and kind catalog only')
    try:
        if sys.flags.optimize:raise RuntimeError('Static entry inventory requires assertions enabled')
        import engine_worker,portable_backend,portable_runtime
        from calculator import timeline
        from portable_coordinate_roster_input import compile_coordinate_battle,SOURCE
        from portable_specs import LIMITS as L,FIELDS as F
        root=Path(__file__).resolve().parents[1]
        sources=[root/p for p in ('app/portable_original_entry_inventory.py','app/portable_original_identity_inventory.py','app/portable_coordinate_roster_input.py','app/portable_world_roster_input.py','app/portable_runtime.py','app/engine_worker.py','app/effect_spec.py')]
        sources=sorted(set(sources+list((root/'app').glob('*.py'))+list((root/'data').glob('*.json'))+list((root/'research/upstream/nikke-calc-master/data').rglob('*.json'))+list((root/'research/upstream/nikke-calc-master/calculator').glob('*.py'))+list((root/'research/upstream/nikke-calc-master/runner').glob('*.py'))+[root/'research/audit-world-roster-input.py',root/'scripts/detail_coverage.py']))
        report['source']=SOURCE
        source_hashes=lambda:{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
        report['source_sha256']=source_hashes();report['gpu_source_sha256']=portable_backend.source_hashes(SOURCE)
        kinds=collections.defaultdict(list)
        def stop(kind):
            def forbidden(*args,**kwargs):calls[kind]+=1;raise AssertionError('Static entry inventory forbids '+kind)
            return forbidden
        with forbid_gpu(),ExitStack() as guards:
            for module,name,kind in [(timeline,'simulate','cpu_battle'),(timeline.CharState,'tick','cpu_battle'),(portable_backend,'build','gpu'),(portable_backend,'execute','gpu'),(portable_backend,'execute_batches','gpu'),(portable_runtime,'execute','gpu'),(portable_runtime,'execute_batches','gpu')]:guards.enter_context(patch.object(module,name,stop(kind)))
            for name,stage,prepared in prepared_profiles():
                report['current_profile']=dict(character=name,favorite_stage=stage)
                row=dict(character=name,favorite_stage=stage,input_packed=False,gpu_admission_verified=False)
                original=copy.deepcopy(prepared)
                row['original_definitions_sha256']=hashlib.sha256(json.dumps(prepared['effects'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
                world=copy.deepcopy(prepared);world['enemy'].update(coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=[dict(id='world',kind='idle')])
                try:
                    words,metadata,_,_=compile_coordinate_battle(world)
                    if prepared!=original:raise AssertionError('Static entry packing mutated original input')
                    if set(metadata['binding_source_indices'])!=set(range(len(prepared['effects']))):raise AssertionError('Static entry discarded original definitions')
                    found=sorted({words[L['DEFINITION_BASE']+i*L['DEFINITION_WORDS']+F['KIND']] for i in range(words[1])})
                    raw=array.array('I',words)
                    if sys.byteorder!='little':raw.byteswap()
                    row.update(input_packed=True,input_words=len(words),input_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),prepared_definitions=len(prepared['effects']),bound_definitions=len(metadata['effects']),definition_kinds=found)
                    for kind in found:kinds[str(kind)].append(dict(character=name,favorite_stage=stage))
                except (ValueError,TypeError,KeyError) as error:row['error']=str(error)
                report['profiles'].append(row)
        if report['source_sha256']!=source_hashes() or report['gpu_source_sha256']!=portable_backend.source_hashes(SOURCE):raise ValueError('Static entry inventory source changed during audit')
        if calls!=dict(cpu_battle=0,gpu=0):raise AssertionError('Static entry inventory made forbidden calls')
        report.update(passed=True,profile_count=len(report['profiles']),packed_profiles=sum(row['input_packed'] for row in report['profiles']),definition_kind_profiles=dict(kinds))
        report.pop('current_profile',None)
    except BaseException as error:
        report['error']=type(error).__name__+': '+str(error);raise
    finally:
        report['elapsed_seconds']=time.perf_counter()-started;write(output,report)
    return {key:report[key] for key in ('stage','passed','profile_count','packed_profiles','forbidden_calls','calculation_verified','gpu_admission_verified','full_character_verified','elapsed_seconds')}
