"""Strict mechanical input for the bounded shared squad-frame executor.

Frames are sampling times, never precomputed shots or burst casts. Values are
normalized mechanics, shared by both backends; character identity is irrelevant.
"""
from impact_specs import ActorHandle, ActorKind
from portable_specs import LIMITS as L


def pack_combat(words, config, double_words):
    if not isinstance(config,dict) or set(config)-{'weapons','targets','initial_gauge'}:
        raise ValueError('Unsupported combat configuration')
    weapons=config.get('weapons',[]);targets=config.get('targets',[])
    if len(weapons)!=5 or not 1<=len(targets)<=8:raise ValueError('Expected five weapons and 1..8 targets')
    def number(value,lo,hi):
        double_words(value)
        if not lo<=value<=hi:raise ValueError('Combat numeric range exceeded')
        return value
    words[3]=1;words[4]=len(targets)
    words[28:30]=double_words(number(config.get('initial_gauge',0),0,100))
    for i,w in enumerate(weapons):
        allowed={'enabled','mode','coefficient','capacity','interval','reload','charge','gauge','stage','cooldown'}
        if not isinstance(w,dict) or set(w)-allowed or type(w.get('enabled',False)) is not bool:
            raise ValueError('Unsupported weapon fields')
        enabled=w.get('enabled',False);mode=w.get('mode','auto')
        if mode not in ('auto','charge'):raise ValueError('Only fixed-rate auto and automatic full-charge modes are ported')
        cap=w.get('capacity',1);stage=w.get('stage',0)
        if type(cap) is not int or not 1<=cap<=10000 or type(stage) is not int or stage not in (0,1,2,3):raise ValueError('Invalid magazine or burst stage')
        at=L['WEAPON_BASE']+i*L['WEAPON_WORDS'];words[at:at+4]=[int(enabled),int(mode=='charge'),cap,stage]
        values=[('coefficient',100,0,1e6),('interval',1,1e-6,180),('reload',1,0,180),('charge',1,1e-6,180),('gauge',0,0,100),('cooldown',40,0,180)]
        for j,(key,default,lo,hi) in enumerate(values):words[at+4+2*j:at+6+2*j]=double_words(number(w.get(key,default),lo,hi))
        if mode=='charge' and w.get('interval',1)<w.get('charge',1):raise ValueError('Charge cycle must include charging time')
    identities=set()
    for i,t in enumerate(targets):
        if not isinstance(t,dict) or set(t)-{'kind','identity','generation','hp','defense','active'}:raise ValueError('Unsupported target fields')
        handle=ActorHandle(t.get('kind',0),t.get('identity',i),t.get('generation',1))
        if handle.kind not in (ActorKind.BODY,ActorKind.ADD) or (i==0)!=(handle.kind==ActorKind.BODY):raise ValueError('Slot zero must be the unique body; other targets must be adds')
        if (handle.kind,handle.identity) in identities:raise ValueError('Duplicate target identity')
        identities.add((handle.kind,handle.identity))
        active=t.get('active',True)
        if type(active) is not bool:raise ValueError('Target active must be boolean')
        at=L['TARGET_BASE']+i*L['TARGET_WORDS']
        words[at:at+4]=[int(handle.kind),handle.identity,handle.generation,int(active)]
        words[at+4:at+6]=double_words(number(t.get('hp',1e12),1,1e30))
        words[at+6:at+8]=double_words(number(t.get('defense',0),0,1e12))
    return dict(targets=targets,weapons=weapons)
