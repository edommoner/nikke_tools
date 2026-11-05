"""Preserve upstream-inert named modifiers in ordinary undeclared battles.

Upstream 67835ca3 reads neither stat. Matching names alone do not opt into the
separate declared spatial/count model. Every original carrier is retained.
"""
import copy
from portable_runtime import UnsupportedPortable
from effect_range_policy import validate_effect as range_effect
from effect_target_count_policy import validate_effect as count_effect
STATS={'effect_target_count_add':93,'effect_range_pct':94}

def required(prepared):
    return any(row['effect'].get('stat') in STATS for row in prepared['effects'])

def compile_product(prepared,producer):
    from portable_specs import LIMITS as L,FIELDS as F
    if prepared.get('reference_models'):raise UnsupportedPortable('Named carriers require their matching combined model consumer')
    names={row['effect'].get('name') for row in prepared['effects']}
    original=prepared;inner=copy.deepcopy(prepared);inner['_product_named_carriers_compiled']=True;domains={}
    for index,row in enumerate(prepared['effects']):
        e=row['effect'];stat=e.get('stat')
        if stat not in STATS:continue
        if stat=='effect_range_pct':range_effect(e)
        else:count_effect(e,allow_marked_allies=True)
        domains[index]=STATS[stat];inner['effects'][index]['effect']['stat']=''
    if not domains:raise ValueError('Original named modifier definitions required')
    source,iw,ow,words,meta=producer(inner)
    sources={'gpu/product_battle_entry.slang':(104400,786432),
        'gpu/product_fixed_battle_entry.slang':(104400,786432),
        'gpu/product_group_battle_entry.slang':(104408,1048576),
        'gpu/product_fixed_group_battle_entry.slang':(104408,1048576)}
    if sources.get(source)!=(iw,ow):
        raise UnsupportedPortable('Named modifier carriers require their checked ordinary BODY product entry')
    if set(meta['binding_source_indices'])!=set(range(len(prepared['effects']))):raise ValueError('Complete original definition coverage required')
    for index,stat in domains.items():
        row=meta['binding_source_indices'].index(index);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS'];e=prepared['effects'][index]['effect'];name=e['target_effect']
        if words[at+F['KIND']]!=4 or words[at+F['STAT']]!=0:raise ValueError('Original named carrier placeholder changed')
        if name not in meta['states']:
            if len(meta['states'])>=L['DEFINITIONS']:raise ValueError('Named modifier symbol capacity exceeded')
            meta['states'][name]=len(meta['states'])
        words[at+F['KIND']]=0;words[at+F['STAT']]=stat;words[at+F['TARGET_NAME']]=meta['states'][name]
        words[at+F['FLAGS']] &= ~2048 # Marker-only lazy revival flag, retain every other lifetime flag.
    meta['product_named_carriers']=dict(source_indices=list(domains),definitions=[copy.deepcopy(prepared['effects'][i]) for i in domains],
        no_matching_definition_names=all(prepared['effects'][i]['effect']['target_effect'] not in names for i in domains),all_original_effects_preserved=True,cpu_state_or_schedule_supplied=False)
    fixed='fixed_' in source
    grouped='group_' in source
    return 'gpu/product_named_carriers_'+('fixed_' if fixed else '')+('group_' if grouped else '')+'battle_entry.slang',iw,ow,words,meta
