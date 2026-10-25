"""Static original prepared-definition identities; no battle or packing proof."""
import collections,copy,importlib.util
from pathlib import Path

def prepared_profiles():
    import engine_worker
    root=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location('original_identity_rosters',root/'research/audit-world-roster-input.py');policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
    from detail_coverage import body_for
    for name,metadata in engine_worker.META.items():
        if not isinstance(metadata,dict) or name.startswith(('_','test_')) or engine_worker.spec.is_preview(name):continue
        for stage in ((0,1,2,3) if metadata.get('favorite_item') else (0,)):
            body=dict(body_for(policy.roster_for(name),30),burst_gauge_mode='accumulate')
            body['profile']['chars'][name]['favorite_stage']=stage
            if stage:body['profile']['chars'][name]['collection_stage']='SR15'
            yield name,stage,engine_worker.evaluate(dict(body,_portable_static_inputs=True))

def inspect():
    profiles=0;duplicates=[]
    for name,stage,prepared in prepared_profiles():
        profiles+=1
        groups=collections.defaultdict(list)
        for index,item in enumerate(prepared['effects']):
            effect=item['effect']
            if effect.get('type')=='damage':groups[effect['name']].append(dict(row=index,owner=item['owner'],periodic=bool(effect.get('tick_interval'))))
        for label,rows in groups.items():
            if len(rows)>1:duplicates.append(dict(character=name,favorite_stage=stage,label=label,sources=copy.deepcopy(rows),nonperiodic=any(not row['periodic'] for row in rows)))
    nonperiodic=[row for row in duplicates if row['nonperiodic']]
    return dict(scope='Complete default-growth/no-cube prepared five-member rosters; all base/favorite profiles',profiles=profiles,duplicate_groups=duplicates,nonperiodic_duplicate_groups=nonperiodic,
                nonperiodic_admission_restriction='observed-original-input-blocker' if nonperiodic else 'unobserved-restriction',
                battle_executed=False,packing_verified=False,gpu_supported=False,full_character_verified=0)
