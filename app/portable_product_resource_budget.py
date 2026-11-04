"""Conservative supply bound for complete ordinary resource notification history.

No battle state or measured event rate enters this calculation. Unsupported
producers retain the existing bounded, fail-closed history rather than a guess.
"""
import math

# Reuse an already admitted transport width (41,690,688 bytes per case).
SUPPLY_OUTPUT_WORDS=10422672

def notification_bound(prepared):
    from portable_specs import LIMITS as L
    effects=[r['effect'] for r in prepared['effects']]
    # Forced skill dispatch ignores the authored timing. It needs a separate
    # producer bound; never count it as one ordinary stage/start notification.
    if any(e.get('stat')=='force_skill_use' for e in effects):return None
    # Every-stack can cross many boundaries per charge. This proof is limited
    # to the ammo notifications emitted by consumption, not that second reader.
    if any(t.startswith('every_stack:') for e in effects for t in e.get('trigger',{}).get('timing',[])):
        return None
    supply=0
    for e in effects:
        if e.get('stat') in ('gauge_consume','gauge_consume_as_ammo'):
            value=e.get('fixed_value')
            if (type(value) not in (int,float) or not math.isfinite(value) or
                value!=int(value) or not -1<=value<=2**53 or
                any(e.get(k) is not None for k in ('values','scaling','scaling_ref'))):
                return None
        if e.get('stat')!='gauge_charge':continue
        value=e.get('fixed_value');timings=e.get('trigger',{}).get('timing',[])
        if (e.get('type')!='instant' or e.get('target')!='self' or
            type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=2**53 or value!=int(value) or
            any(e.get(k) is not None for k in ('values','scaling','scaling_ref','tick_interval','tick_start')) or e.get('trigger_values') or
            not timings or len(set(timings))!=len(timings)):
            return None
        occurrences=0
        for timing in timings:
            if timing=='battle_start':occurrences+=1
            elif timing in ('burst_enter:1','burst_enter:2','burst_enter:3'):
                # Any successful battle has at most BURST_TRACE stage entries;
                # the common logger fails closed before the next stage.
                occurrences+=L['BURST_TRACE']
            else:return None
        supply+=math.ceil(value)*occurrences
        if supply>2**53:return None
    # Resources begin at zero. Consumption cannot spend more than the positive
    # literal supply; caps/conditions/rounding down int(consumed) only reduce it.
    return supply

def output_words(prepared,ordinary_output):
    from portable_enemy_ammo_wire import LAYOUT as E
    bound=notification_bound(prepared)
    capacity=lambda words:128+(words-E['OUTPUT_BASE']-E['RESOURCE_BASE'])//8
    if bound is not None and capacity(ordinary_output)<bound<=capacity(SUPPLY_OUTPUT_WORDS):
        return SUPPLY_OUTPUT_WORDS,bound
    return ordinary_output,bound
