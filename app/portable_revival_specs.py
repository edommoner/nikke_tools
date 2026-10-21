"""Private world revival identity; canonical definitions remain untouched."""
import math,re
PERSIST=1024
MAGIC=0x52565631
BASE=766752
LOST=BASE+8
RNG=LOST+5*512
TRACE=RNG+632
TRACE_COUNT=128
WORDS=TRACE+TRACE_COUNT*8-BASE
assert BASE+WORDS<=786416


def validate(effect,*,combat,world_frame):
    if 'persist_on_revive' in effect:
        if type(effect['persist_on_revive']) is not bool or effect.get('type')!='buff' or combat is None or not world_frame:
            raise ValueError('Revival persistence requires a private combat world buff and boolean flag')
    if effect.get('stat')!='revive':
        def down_target(target):return any(down_target(t) for t in target) if isinstance(target,list) else isinstance(target,str) and target.startswith('allies_down_')
        if down_target(effect.get('target','self')):raise ValueError('Down-only recipients currently require a revive instant')
        return
    if effect.get('type')!='instant' or combat is None or not world_frame:raise ValueError('Revive requires a private combat world instant')
    value=effect.get('fixed_value')
    values=effect.get('values',{})
    candidates=[value] if value is not None else list(values.values()) if isinstance(values,dict) else []
    if not candidates or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in candidates):raise ValueError('Revive requires a positive finite HP percentage')
    if effect.get('scaling') is not None or effect.get('tick_interval'):raise ValueError('Periodic or scaled revival is not ported')


def pack(words,L,effects,rows,seed):
    enabled=any(e.get('stat')=='revive' or e.get('persist_on_revive') for e,_ in effects)
    for i,((effect,_),row) in enumerate(zip(effects,rows)):
        if enabled and effect.get('type')=='buff' and int(row[1]) in (4,12):words[L['DEFINITION_BASE']+i*L['DEFINITION_WORDS']+28]|=2048
        if effect.get('persist_on_revive'):words[L['DEFINITION_BASE']+i*L['DEFINITION_WORDS']+28]|=PERSIST
        if effect.get('stat')!='revive':continue
        if type(seed) is not int or not 0<=seed<=2**64-1:raise ValueError('Revive requires a literal unsigned64 allied RNG seed')
        if int(row[1])!=29:raise ValueError('Canonical revival identity changed')
        at=L['MODE_BASE']+i*L['MODE_WORDS'];words[at:at+4]=[MAGIC,seed&0xffffffff,seed>>32,0]
