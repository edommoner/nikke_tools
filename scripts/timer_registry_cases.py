"""Authored shared clock schedules; no reference execution is a GPU stimulus."""
from enemy_recipient_cases import manager,NAMES


def effect(name,kind,stat,value=0,event='battle_start',**kw):
    return dict(name=name,source='스킬1',type=kind,stat=stat,fixed_value=value,target='target' if kind=='damage' else 'self',trigger=dict(timing=[event],condition=[]),**kw)


def cases():
    for immediate in (False,True):
        dot=effect('clock','damage','dot_damage',100,tick_interval=.25,duration=1)
        if immediate:dot['tick_start']='immediate'
        yield dict(name='boundary-'+('immediate' if immediate else 'delayed'),effects=[dot],times=[0,.25,.5,.75,1,1.25],totals=[1000,2000,3000,4000,4000,4000] if immediate else [0,1000,2000,3000,4000,4000])
    for mode in ('self-refresh','sibling-refresh','sibling-cancel','sibling-restart','sibling-recreate'):
        first=effect('first','damage','dot_damage',100,tick_interval=.25,duration=1)
        target='first' if mode=='self-refresh' else 'second'
        if mode=='self-refresh':first['source']='스킬3';effects=[first]
        else:
            second=effect('second','damage','auto_damage' if mode=='sibling-restart' else 'dot_damage',200,tick_interval=.25,duration=1)
            second['source']='스킬3';effects=[first,second]
        if mode in ('sibling-cancel','sibling-recreate'):
            effects.append(effect('cancel','instant','remove_named_buff',event='hit_count:first:1',target_effect=target,max_trigger=1))
        if mode!='sibling-cancel':
            effects.append(effect('refresh','instant','force_skill_use',event='hit_count:first:1',target_skill='스킬3',max_trigger=1))
        times=[0,.25,.5,.75,1,1.25]
        totals=[0,1000,2000,3000,4000,5000] if mode=='self-refresh' else [0,1000,2000,3000,4000,4000] if mode=='sibling-cancel' else [0,3000,6000,9000,12000,14000] if mode=='sibling-refresh' else [0,1000,4000,7000,10000,12000]
        yield dict(name=mode,effects=effects,times=times,totals=totals)
    first=effect('declared-first','damage','dot_damage',100,event='on_attack',tick_interval=.25,duration=1)
    second=effect('registered-first','damage','dot_damage',200,tick_interval=.5,duration=1)
    child=effect('ordered strength','buff','atk_pct',100,event='hit_count:registered-first:1',duration=2,max_trigger=1)
    yield dict(name='registration-order-with-live-child-buff',effects=[first,second,child],times=[0,.25,.5,.75,1,1.25],events={.25:'on_attack'},totals=[0,0,4000,6000,12000,14000])


def prepare(case):
    effects=[effect('no critical','buff','crit_rate',-15,duration=-1)]+case['effects']
    bm=manager(effects)
    bm.char_effects=lambda name:[eff for eff,owner in bm._effects if owner==name]
    return bm


def exercise(case):
    bm=prepare(case);total=0;observed=[];firings=[]
    def damage(eff,caster,t):
        nonlocal total
        total+=round(bm._effective_atk(caster)*eff['fixed_value']/100);firings.append((eff['name'],t))
        bm.notify('hit_count:'+eff['name'],t,caster)
    bm.register_damage_handler(damage)
    for i,t in enumerate(case['times']):
        bm.tick(t)
        if i==0:bm.notify('battle_start',t,NAMES[0])
        elif t in case.get('events',{}):bm.notify(case['events'][t],t,NAMES[0])
        bm.tick(t);observed.append(total)
    assert observed==case['totals'],(case['name'],observed,case['totals'],firings)
    return dict(passed=True,totals=observed,firings=firings)
