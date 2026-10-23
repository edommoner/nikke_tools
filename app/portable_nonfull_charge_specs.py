"""Preserve literal signed bases across the bounded legacy static compiler."""
import re
PREFIX='non_full_charge_fire_count:'


def parse(timing):
    if not isinstance(timing,str) or not timing.startswith(PREFIX):return None
    raw=timing[len(PREFIX):]
    if raw=='{0}':return (None,raw)
    if not re.fullmatch(r'-?[0-9]+',raw):raise ValueError('Non-full charge trigger requires an integer literal')
    value=int(raw)
    if not -(2**31)<=value<=2**31-1:raise ValueError('Non-full charge trigger exceeds signed32')
    return value,raw


def compiler_effect(effect):
    # Only the legacy static intermediate changes. pack_descriptors restores
    # the original threshold and raw spelling still drives reducer membership.
    timings=effect.get('trigger',{}).get('timing',[])
    lowered=[PREFIX+'1' if (p:=parse(t)) is not None and p[0] is not None and (p[0]<=0 or abs(p[0])>100000000) else t for t in timings]
    return effect if lowered==timings else dict(effect,trigger=dict(effect['trigger'],timing=lowered))
