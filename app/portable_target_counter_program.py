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
    original = detail_gpu.compile_effects(chars, [(compiler_effect(e), owner) for e, owner in effects])
    allocate_names(effects, original['states'])
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
