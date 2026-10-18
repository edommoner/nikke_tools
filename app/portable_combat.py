"""Strict mechanical input for the bounded shared squad-frame executor.

Frames are sampling times, never precomputed shots or burst casts. Values are
normalized mechanics, shared by both backends; character identity is irrelevant.
"""
from impact_specs import ActorHandle, ActorKind
from portable_specs import LIMITS as L


def pack_combat(words, config, double_words):
    if not isinstance(config,dict) or set(config)-{'weapons','targets','initial_gauge','reentry_delay','trace'}:
        raise ValueError('Unsupported combat configuration')
    weapons=config.get('weapons',[]);targets=config.get('targets',[])
    if len(weapons)!=5 or not 1<=len(targets)<=8:raise ValueError('Expected five weapons and 1..8 targets')
    def number(value,lo,hi):
        double_words(value)
        if not lo<=value<=hi:raise ValueError('Combat numeric range exceeded')
        return value
    trace=config.get('trace','full')
    if trace not in ('full','summary'):raise ValueError('Invalid trace policy')
    words[5]=int(trace=='full')
    words[3]=1;words[4]=len(targets)
    words[28:30]=double_words(number(config.get('initial_gauge',0),0,100))
    words[30:32]=double_words(number(config.get('reentry_delay',.5),0,180))
    for i,w in enumerate(weapons):
        allowed={'enabled','mode','coefficient','capacity','interval','reload','charge','gauge','stage','cooldown','pellets','muzzles','full_charge_mult','optimal','element_match'}
        if not isinstance(w,dict) or set(w)-allowed or type(w.get('enabled',False)) is not bool:
            raise ValueError('Unsupported weapon fields')
        enabled=w.get('enabled',False);mode=w.get('mode','auto')
        if mode not in ('auto','charge'):raise ValueError('Only fixed-rate auto and automatic full-charge modes are ported')
        cap=w.get('capacity',1);stage=w.get('stage',0)
        if type(cap) is not int or not 1<=cap<=10000 or type(stage) is not int or stage not in (0,1,2,3,4):raise ValueError('Invalid magazine or burst stage')
        pellets=w.get('pellets',1);muzzles=w.get('muzzles',1)
        if type(pellets) is not int or type(muzzles) is not int or not 1<=pellets<=64 or not 1<=muzzles<=8:
            raise ValueError('Invalid physical shot dimensions')
        at=L['WEAPON_EXTRA_BASE']+i*4;words[at:at+2]=[pellets,muzzles]
        words[at+2:at+4]=double_words(number(w.get('full_charge_mult',100),0,1e6))
        if any(type(w.get(k,False)) is not bool for k in ('optimal','element_match')):raise ValueError('Attack context must be boolean')
        words[L['ATTACK_CONTEXT_BASE']+i]=int(w.get('optimal',False)) | (int(w.get('element_match',False))<<1)
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


def pack_mode(words,index,row,double_words):
    """Reuse legacy compiler's mechanics; reject every discarded behavior."""
    if int(row[224]) not in (1,3) or row[24]!=row[28] or row[239] or row[233] or row[234]!=-1 or row[235]:
        raise ValueError('Unported warmup, entry reload, dynamic magazine or skill-mode policy')
    if row[42]!=0:
        raise ValueError('Authored mode entry delays require explicit sampling design')
    capacity=int(row[27]);pellets=int(row[25]);muzzles=int(row[29]);limit=int(row[232])
    if capacity!=-1 and not 1<=capacity<=10000 or not 1<=pellets<=64 or not 1<=muzzles<=8 or limit < -1 or limit>10000:
        raise ValueError('Invalid bounded mode dimensions')
    if not 0<row[28]<=1e6 or not 0<=row[237]<=180 or not 0<row[225]<=180 or not 0<=row[227]<=180 or not 0<=row[249]<=100:
        raise ValueError('Invalid mode timing or gauge')
    if not 0<=row[226]<=1e6:raise ValueError('Invalid mode charge multiplier')
    if not 0<=row[26]<=1e6 or not -1<=row[236]<=1e6 or not 0<=row[228]<=1e6:raise ValueError('Invalid mode coefficient/core multiplier')
    if capacity==-1 and limit>=0:raise ValueError('Infinite modes cannot have a round-count lifetime')
    at=L['MODE_BASE']+index*L['MODE_WORDS']
    words[at:at+4]=[int(row[224]==3),max(0,capacity),pellets,muzzles]
    for offset,value in [(4,row[26]),(6,row[28]),(8,row[237]),(10,row[225]),(12,row[249]),(14,row[228]),(16,row[236]),(18,row[227])]:
        words[at+offset:at+offset+2]=double_words(value)
    words[at+20:at+23]=[limit & 0xffffffff,int(capacity==-1),int(row[238])]
    words[at+24:at+26]=double_words(row[226]);words[at+26]=int(bool(row[30]))
