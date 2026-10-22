"""Static identities for per-shot notices; raw integer spelling is significant."""
PREFIX='pellet_hit_in_shot:'
MINIMUM=-(2**31)
MAXIMUM=2**31-1


def parse(timing):
    if not isinstance(timing,str) or not timing.startswith(PREFIX):return None
    raw=timing[len(PREFIX):]
    try:value=int(raw)
    except ValueError:raise ValueError('Per-shot pellet threshold requires an integer') from None
    if not MINIMUM<=value<=MAXIMUM:raise ValueError('Per-shot pellet threshold exceeds signed32')
    return value,raw


def bindings(effects,names):
    found={name:{} for name in names}
    for effect,owner in effects:
        for timing in effect['trigger']['timing']:
            parsed=parse(timing)
            if parsed is not None:
                value,raw=parsed;found[owner][raw]=value
    return {owner:{raw:i+1 for i,(_,raw) in enumerate(sorted((value,raw) for raw,value in values.items()))} for owner,values in found.items()}


def compiler_effect(effect):
    # Legacy CUDA requires positive event27 thresholds. Its output is only a
    # static intermediate: restore the literal signed32 value during packing.
    timings=effect.get('trigger',{}).get('timing',[])
    lowered=[PREFIX+'1' if (parsed:=parse(t)) is not None and parsed[0]<=0 else t for t in timings]
    if lowered==timings:return effect
    return dict(effect,trigger=dict(effect['trigger'],timing=lowered))
