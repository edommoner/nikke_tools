"""Canonical base-copy policies and a disjoint tagged MODE payload."""
from base_copy_runtime import POLICIES
FLAG=1024
MAGIC=0x42435031
OFFSET=6
END=10
STATE_BASE=763680
STATE_WORDS=512*6
assert STATE_BASE+STATE_WORDS<=786416


def enabled(effect):return effect.get('stat') in POLICIES


def validate(effect,*,combat,world_frame):
    if not enabled(effect):return
    policy=POLICIES[effect['stat']]
    if effect.get('type')!='buff' or combat is None or not world_frame:
        raise ValueError('Base-stat copy requires a private combat world buff')
    if effect.get('copy_from')!=policy.selector:raise ValueError('Unsupported base-stat copy selector')
    if effect.get('scaling') is not None or effect.get('duration_bullets',-1)!=-1:
        raise ValueError('Unsupported base-stat copy scaling or bullet lifetime')


def pack(words,L,effects,rows):
    for i,(effect,_) in enumerate(effects):
        if not enabled(effect):continue
        stat=POLICIES[effect['stat']].code
        if int(rows[i][1])!=0 or int(rows[i][2])!=stat:raise ValueError('Canonical copy identity changed')
        at=L['MODE_BASE']+i*L['MODE_WORDS']+OFFSET
        words[at:at+4]=[MAGIC,stat,1 if stat==85 else 2,0]
        words[L['DEFINITION_EXTRA_BASE']+i*L['DEFINITION_EXTRA_WORDS']+3]|=FLAG
