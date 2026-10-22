"""Private presence marker and authored aim policy, never a numeric stat alias."""
STAT=91
MAGIC=0x46414330


def enabled(effect):
    return effect.get('type')=='buff' and effect.get('stat')=='focus_fire'


def validate(effect, *, combat, world_frame):
    if set(effect.get('trigger',{}).get('condition',[])) & {'focusing','no_broken_cover_ally'} and (combat is None or not world_frame):
        raise ValueError('Cover/camera predicates require a private combat world')
    if not enabled(effect):return
    if combat is None or not world_frame:
        raise ValueError('Focus fire requires a private combat world')
    if effect.get('scaling') is not None or effect.get('tick_interval'):
        raise ValueError('Focus fire is presence, without scaling or periodic ticks')


def compiler_effect(effect):
    return dict(effect,stat='') if enabled(effect) else effect


def pack(words,limits,effects,layer2):
    if type(layer2) is not bool:raise ValueError('Focus aim layer2 must be a literal boolean')
    if layer2 or any(enabled(effect) for effect,_ in effects):
        words[limits['WORLD_META_BASE']+4]=MAGIC|int(layer2)
