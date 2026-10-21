"""Static canonical trigger-reducer bindings; no simulated counters or state."""
import math

FLAG=256
MAGIC=0x54525231
OFFSET=6
MASK_OFFSET=9
END=17


def enabled(effect):return effect.get('stat')=='trigger_count_reduce'


def validate(effect,*,combat,world_frame):
    if not enabled(effect):return
    if effect.get('type')!='buff' or combat is None or not world_frame:
        raise ValueError('Trigger-count reduction requires a private combat world buff')
    if not isinstance(effect.get('target_effect',''),str):raise ValueError('Invalid trigger reduction target')
    value=effect.get('fixed_value',0)
    if type(value) not in (int,float) or abs(value)>1e8 or not math.isfinite(value):
        raise ValueError('Invalid trigger reduction amount')


def pack(words,L,effects,rows,legacy,double_words):
    for i,(effect,_) in enumerate(effects):
        if not enabled(effect):continue
        # detail_gpu already encodes raw timing intersection and caster identity.
        # Transpose its per-target reducer mask into this reducer's tagged MODE
        # union; weapon target records keep their original full MODE payload.
        at=L['MODE_BASE']+i*L['MODE_WORDS']
        words[at+OFFSET:at+MASK_OFFSET]=[MAGIC,*double_words(rows[i][243])]
        for target,row in enumerate(rows):
            if int(row[legacy.REDUCER_MASK+i//32])&(1<<(i%32)):
                words[at+MASK_OFFSET+target//32]|=1<<(target%32)
        words[L['DEFINITION_EXTRA_BASE']+i*L['DEFINITION_EXTRA_WORDS']+3]|=FLAG
