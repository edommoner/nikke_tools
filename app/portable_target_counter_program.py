"""Private carrier recipes; runtime progress and impacts remain GPU-owned.

The common compiler packs a zero-valued sentinel carrier and named-event
descriptor. Original CounterSpec and native event58 descriptors determine the
private mapping. No public admission or battle execution is added here.
"""
import copy
from target_counter_specs import specification


def compiler_effects(effects):
    result = copy.deepcopy(effects)
    for effect in result:
        if specification(effect) is not None:
            effect.pop('target_counter')
            effect.update(stat='def_pct', fixed_value=0)
        trigger = effect.get('trigger', {})
        trigger['timing'] = [
            t.replace('event:target_counter_complete:', 'event:', 1)
            if t.startswith('event:target_counter_complete:') else t
            for t in trigger.get('timing', [])]
    return result


def patch_program(words, metadata, chars, effects):
    import detail_gpu
    from portable_specs import LIMITS as L, FIELDS as F
    from portable_trigger_specs import pack_event_candidates
    from portable_target_state_specs import compiler_effect, allocate_names
    from portable_pellet_shot_specs import compiler_effect as pellet_shot_compiler_effect
    original = detail_gpu.compile_effects(chars, [(pellet_shot_compiler_effect(compiler_effect(e)), owner) for e, owner in effects])
    allocate_names(effects, original['states'])
    # Portable code IDs include the literal enemy code even when no condition
    # references that exact spelling. Rebuild the same immutable symbol table;
    # do not weaken the exact namespace comparison to a subset test.
    from portable_code_specs import code_names
    world=L['WORLD_META_BASE'];code=words[world]
    names=[name for name,index in metadata['states'].items() if index+1==code]
    if code!=0 and len(names)!=1:raise ValueError('Private counter enemy code identity changed')
    expected=code_names(effects,names[0] if code else None,original['states'],L['DEFINITIONS'])
    if expected!=(code,words[world+1]):raise ValueError('Private counter enemy code descriptor changed')
    if original['states'] != metadata['states']:
        raise ValueError('Private counter compiler name symbols changed')
    from portable_team_hit_specs import bound_effects
    effects=bound_effects(effects,metadata,[c['name'] for c in chars])
    def identity(effect):
        return effect.get('type'), effect.get('stat') if effect.get('type') == 'buff' else effect.get('stat', '')
    # A real def_pct carrier must not merge with the private counter recipe.
    stat_keys = {key: i for i, key in enumerate(dict.fromkeys(identity(e) for e, _ in effects))}
    for i, ((effect, owner), row) in enumerate(zip(effects, original['effects'])):
        at = L['DEFINITION_BASE'] + i * L['DEFINITION_WORDS']
        if specification(effect) is not None:
            words[at + F['KIND']] = 4
            words[at + F['STAT']] = 0
        # Non-allied removal and enemy instant mutations reserve all eight
        # words. Enemy buff-stack carriers instead own an actual recipient plan.
        kind=words[at + F['KIND']]
        reserved_recipient = (kind==1 and words[at + F['TARGET']]!=1 or
                              kind in (15,16,17,18,19,20,21,26) and words[at + F['TARGET']]==2 and
                              words[L['HEALTH_DEFINITION_BASE']+i*L['HEALTH_DEFINITION_WORDS']+3]==0)
        if not reserved_recipient:
            words[L['RECIPIENT_BASE'] + i * 8 + 6] = stat_keys[identity(effect)]
        for slot in range(int(row[144])):
            base = 145 + slot * 7
            if row[base] != 58:
                continue
            event = L['EVENT_BASE'] + i * L['EVENT_WORDS'] + slot * 8
            if words[event] != 31 or words[event + 4] != int(row[base + 3]):
                raise ValueError('Private completion event mapping changed')
            words[event] = 58
            if slot == 0:
                words[at + F['EVENT']] = 58
    pack_event_candidates(words, L)
