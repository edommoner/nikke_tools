"""Canonical named periodic interval operators in the existing MODE union."""
FLAG=512
MAGIC=0x53494e31
OFFSET=6
END=10
KINDS={'effect_interval':1,'skill_cooldown':2}


def enabled(effect):return effect.get('stat') in KINDS


def validate(effect,*,combat,world_frame):
    if not enabled(effect):return
    if effect.get('type')!='buff' or combat is None or not world_frame:
        raise ValueError('Named periodic interval requires a private combat world buff')
    if not isinstance(effect.get('target_effect',''),str):raise ValueError('Invalid periodic target name')


def pack(words,L,effects,rows):
    for i,(effect,_) in enumerate(effects):
        if not enabled(effect):continue
        row=rows[i]
        if int(row[1])!=4 or int(row[220])!=KINDS[effect['stat']]:
            raise ValueError('Canonical periodic operator changed')
        at=L['MODE_BASE']+i*L['MODE_WORDS']+OFFSET
        words[at:at+END-OFFSET]=[MAGIC,int(row[220]),int(row[221]),int(row[222])]
        words[L['DEFINITION_EXTRA_BASE']+i*L['DEFINITION_EXTRA_WORDS']+3]|=FLAG
