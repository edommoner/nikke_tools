"""CPU-only full original coordinate packing and literal kind catalog, not admission."""
import array,collections,copy,hashlib,json,sys,time
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
from portable_original_identity_inventory import prepared_profiles

def rejected_effects(words,metadata,prepared,unsupported):
    """Bind compiled rejections back to exact original rows, never row positions."""
    from portable_specs import LIMITS as L,FIELDS as F
    bindings=metadata['binding_source_indices'];effects=prepared['effects'];rows=[]
    if len(bindings)!=words[1]:raise ValueError('Incomplete original rejection bindings')
    for rejected in unsupported:
        index=rejected['row'];kind=rejected['kind']
        if type(index) is not int or not 0<=index<len(bindings):raise ValueError('Invalid compiled rejection row')
        at=L['DEFINITION_BASE']+index*L['DEFINITION_WORDS']+F['KIND']
        if words[at]!=kind:raise ValueError('Rejection kind differs from actual wire')
        source=bindings[index]
        if type(source) is not int or not 0<=source<len(effects):raise ValueError('Invalid original rejection source')
        item=effects[source];effect=item['effect'];trigger=effect.get('trigger',{})
        operator=dict(kind=kind,effect_type=effect.get('type'),stat=effect.get('stat'),
            target=copy.deepcopy(effect.get('target','self')),timing=copy.deepcopy(trigger.get('timing',[])),
            conditions=copy.deepcopy(trigger.get('condition',[])),scaling=effect.get('scaling'),
            references={key:copy.deepcopy(effect[key]) for key in ('target_effect','target_skill','scaling_ref','remove_scope') if key in effect},
            fields=sorted(effect))
        rows.append(dict(compiled_row=index,source_row=source,owner=item['owner'],name=effect.get('name'),operator=operator,
            effect_sha256=hashlib.sha256(json.dumps(effect,ensure_ascii=False,sort_keys=True).encode()).hexdigest()))
    return rows

def operator_priorities(profiles,*,effect_key='rejected_effects'):
    """Count profiles, original definitions and compiled bindings separately."""
    groups={}
    for profile in profiles:
        for row in profile.get(effect_key,[]):
            operator=row['operator'];key=json.dumps(operator,ensure_ascii=False,sort_keys=True)
            group=groups.setdefault(key,dict(operator=copy.deepcopy(operator),definitions=[]))
            group['definitions'].append(dict(character=profile['character'],favorite_stage=profile['favorite_stage'],
                **{key:row[key] for key in ('compiled_row','source_row','owner','name','effect_sha256')}))
    for group in groups.values():
        definitions=group['definitions'];profiles=sorted({(row['character'],row['favorite_stage']) for row in definitions})
        group['profiles']=[dict(character=name,favorite_stage=stage) for name,stage in profiles]
        group.update(profile_count=len(profiles),original_definition_count=len({(row['character'],row['favorite_stage'],row['source_row']) for row in definitions}),compiled_definition_count=len(definitions))
        definitions.sort(key=lambda row:(row['character'],row['favorite_stage'],row['compiled_row']))
    return sorted(groups.values(),key=lambda group:(-group['profile_count'],-group['original_definition_count'],group['operator']['kind'],json.dumps(group['operator'],ensure_ascii=False,sort_keys=True)))

def kind_dependencies(profiles):
    groups=collections.defaultdict(list)
    for profile in profiles:
        required=tuple(sorted({row['kind'] for row in profile.get('kind_admission',{}).get('unsupported',[])}))
        if required:groups[required].append(dict(character=profile['character'],favorite_stage=profile['favorite_stage']))
    return [dict(required_kinds=list(required),profile_count=len(rows),profiles=sorted(rows,key=lambda row:(row['character'],row['favorite_stage'])))
        for required,rows in sorted(groups.items(),key=lambda item:(-len(item[1]),item[0]))]

def run(output,*,write,forbid_gpu,source=None,comparison_source=None):
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
        from portable_coordinate_roster_input import compile_coordinate_battle,SOURCE as DEFAULT_SOURCE
        source=source or DEFAULT_SOURCE
        from portable_coordinate_kind_admission import KindAdmission
        policy=KindAdmission(Path(__file__).resolve().parents[1],source)
        comparison=KindAdmission(Path(__file__).resolve().parents[1],comparison_source) if comparison_source else None
        from portable_specs import LIMITS as L,FIELDS as F
        root=Path(__file__).resolve().parents[1]
        sources=[root/p for p in ('app/portable_original_entry_inventory.py','app/portable_original_identity_inventory.py','app/portable_coordinate_roster_input.py','app/portable_world_roster_input.py','app/portable_runtime.py','app/engine_worker.py','app/effect_spec.py')]
        sources=sorted(set(sources+list((root/'app').glob('*.py'))+list((root/'data').glob('*.json'))+list((root/'research/upstream/nikke-calc-master/data').rglob('*.json'))+list((root/'research/upstream/nikke-calc-master/calculator').glob('*.py'))+list((root/'research/upstream/nikke-calc-master/runner').glob('*.py'))+[root/'research/audit-world-roster-input.py',root/'scripts/detail_coverage.py']))
        report['source']=source
        source_hashes=lambda:{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
        report['source_sha256']=source_hashes();report['gpu_source_sha256']=portable_backend.source_hashes(source)
        if comparison is not None:
            report.update(comparison_source=comparison_source,comparison_gpu_source_sha256=portable_backend.source_hashes(comparison_source),
                expansion_scope='Definition kind scope only; expanded handlers retain separate runtime/model/native verification requirements')
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
                    row.update(input_packed=True,input_words=len(words),input_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),prepared_definitions=len(prepared['effects']),bound_definitions=len(metadata['effects']),definition_kinds=found,kind_admission=policy.inspect(words))
                    for kind in found:kinds[str(kind)].append(dict(character=name,favorite_stage=stage))
                except (ValueError,TypeError,KeyError) as error:row['error']=str(error)
                else:
                    row['rejected_effects']=rejected_effects(words,metadata,prepared,row['kind_admission'].get('unsupported',[]))
                    if comparison is not None:
                        baseline=comparison.inspect(words);current=row['kind_admission']
                        if not baseline['checked'] or not current['checked']:raise ValueError('Kind expansion requires two sampled-vital policies')
                        still_rejected={(r['row'],r['kind']) for r in current['unsupported']}
                        expanded=[r for r in baseline['unsupported'] if (r['row'],r['kind']) not in still_rejected]
                        row.update(comparison_kind_admission=baseline,expanded_kind_effects=rejected_effects(words,metadata,prepared,expanded))
                report['profiles'].append(row)
        if report['source_sha256']!=source_hashes() or report['gpu_source_sha256']!=portable_backend.source_hashes(source):raise ValueError('Static entry inventory source changed during audit')
        if comparison is not None and report['comparison_gpu_source_sha256']!=portable_backend.source_hashes(comparison_source):raise ValueError('Comparison source changed during static inventory')
        if calls!=dict(cpu_battle=0,gpu=0):raise AssertionError('Static entry inventory made forbidden calls')
        report.update(passed=True,profile_count=len(report['profiles']),packed_profiles=sum(row['input_packed'] for row in report['profiles']),definition_kind_profiles=dict(kinds))
        report['kind_rejected_profiles']=sum(bool(row.get('kind_admission',{}).get('unsupported')) for row in report['profiles'])
        report['operator_priorities']=operator_priorities(report['profiles'])
        report['rejected_operator_categories']=len(report['operator_priorities'])
        if comparison is not None:
            report['expanded_kind_profiles']=sum(bool(r.get('expanded_kind_effects')) for r in report['profiles'])
            report['expanded_kind_operator_priorities']=operator_priorities(report['profiles'],effect_key='expanded_kind_effects')
        report['kind_dependencies']=kind_dependencies(report['profiles'])
        report['packing_failures']=[{key:row[key] for key in ('character','favorite_stage','error','original_definitions_sha256')} for row in report['profiles'] if not row['input_packed']]
        report.pop('current_profile',None)
    except BaseException as error:
        report['error']=type(error).__name__+': '+str(error);raise
    finally:
        report['elapsed_seconds']=time.perf_counter()-started;write(output,report)
    result={key:report[key] for key in ('stage','passed','profile_count','packed_profiles','kind_rejected_profiles','rejected_operator_categories','forbidden_calls','calculation_verified','gpu_admission_verified','full_character_verified','elapsed_seconds')}
    if comparison is not None:result['expanded_kind_profiles']=report['expanded_kind_profiles']
    return result
