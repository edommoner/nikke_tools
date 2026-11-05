"""Ordinary upstream marker semantics, never declared acquisition/frozen locks."""
import copy
from portable_runtime import UnsupportedPortable

PROJECTILE_RETURN=1048576
SOURCES={
    'gpu/product_battle_entry.slang':'gpu/product_ordinary_lock_battle_entry.slang',
    'gpu/product_fixed_battle_entry.slang':'gpu/product_ordinary_lock_fixed_battle_entry.slang',
}

def compile_product(prepared):
    if prepared.get('reference_models'):
        raise UnsupportedPortable('Ordinary lock markers cannot omit a declared model consumer')
    from portable_detail import compile_product as producer
    from portable_enemy_specs import enemy_buff_plan
    from destructible_skill_specs import coefficient
    from portable_specs import LIMITS as L,FIELDS as F
    lowered=copy.deepcopy(prepared);markers=[];inert=[];projectiles=[]
    names={c['name']:c for c in prepared['chars']}
    for i,row in enumerate(lowered['effects']):
        e=row['effect'];stat=e.get('stat')
        if stat=='lock_on':
            e['stat']=''
            if e.get('type')!='buff' or enemy_buff_plan(e) is None:
                raise UnsupportedPortable('Ordinary Lock On requires a supported named enemy marker recipient')
            markers.append(i)
        elif stat in ('effect_target_count_add','effect_range_pct'):
            # Neither stat has an upstream ordinary numeric consumer. Retain
            # its named carrier, values, trigger and bullet lifetime verbatim.
            from effect_target_count_policy import validate_effect as count
            from effect_range_policy import validate_effect as radius
            (radius if stat=='effect_range_pct' else lambda x:count(x,allow_marked_allies=True))(e)
            e['stat']='';inert.append(i)
        if e.get('target')=='all_projectiles':
            # Exact current upstream _handle_damage_eff early return. Keep a
            # real damage definition/activation budget; suppress its handler,
            # not its coefficient or authored rows. Periodic variants remain
            # refused until their timer lifecycle is separately represented.
            coefficient(e,names[row['owner']]);e['target']='boss';projectiles.append(i)
    if not markers:raise ValueError('Original ordinary Lock On marker required')
    source,iw,ow,words,meta=producer(lowered)
    from portable_product_s2_entries import ORDINARY,checked_wrapper
    sources={**SOURCES,**ORDINARY}
    if source not in sources or not checked_wrapper(source,iw,ow):
        raise UnsupportedPortable('Ordinary lock markers require their checked BODY/ADD product composition')
    if set(meta['binding_source_indices'])!=set(range(len(prepared['effects']))):
        raise UnsupportedPortable('Complete ordinary original definitions required')
    for i in markers:
        row=meta['binding_source_indices'].index(i);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
        if words[at+F['KIND']]!=4 or not meta['enemy_buff_definitions'][row]:
            raise ValueError('Ordinary enemy marker must retain generic enemy-state ownership')
    for i in projectiles:
        row=meta['binding_source_indices'].index(i);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
        if words[at+F['KIND']]!=3 or words[at+F['DAMAGE_FLAGS']] & ~(524288|131072):
            raise UnsupportedPortable('Plain upstream projectile early-return row required')
        words[at+F['DAMAGE_FLAGS']] |= PROJECTILE_RETURN
    affected=markers+inert+projectiles
    meta['product_ordinary_lock']=dict(marker_indices=markers,inert_named_indices=inert,projectile_return_indices=projectiles,
        original_definitions={i:copy.deepcopy(prepared['effects'][i]) for i in affected},
        declared_lock_model_inferred=False,cpu_state_or_schedule_supplied=False,
        selection='upstream-aimed-live-ADD-then-spawn-order; BODY fallback')
    return sources[source],iw,ow,words,meta
