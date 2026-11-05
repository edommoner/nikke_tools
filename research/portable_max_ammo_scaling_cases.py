"""Live recipient maximum-ammunition stimuli; no packing or simulation on import."""
import copy
from portable_parent_fixed_cases import fixtures as parent_fixtures
from portable_entry_reload_cases import fixtures as mode_fixtures
from world_enemy_attack_cases import field

def fixtures():
    seed=copy.deepcopy(parent_fixtures()[0]);seed.update(effects=[seed['effects'][0]],owners=[0])
    for w in seed['combat']['weapons']:w['capacity']=5
    rows=[]
    def add(label,*,value=10,target='self',owner=0,before=(),after=()):
        c=copy.deepcopy(seed);scaled=field('charge_dmg_pct',value,target,'ammo-scaled',scaling='max_ammo_count')
        c.update(name='max-ammo-scaling-'+label,effects=c['effects']+copy.deepcopy(list(before))+[scaled]+copy.deepcopy(list(after)),owners=[0]+[owner]*(len(before)+1+len(after)))
        c['contract']=dict(kind=label,owner=owner);rows.append(c);return c
    add('basic');add('zero',value=0);add('negative',value=-2)
    c=add('owner-four',owner=4)
    c=add('recipient-allies',target='all_allies',owner=4)
    for i,w in enumerate(c['combat']['weapons']):w['capacity']=i+3
    add('percent',before=[field('max_ammo_pct',50,'self','capacity-percent')])
    add('flat',before=[field('max_ammo_flat',2.5,'self','capacity-flat')])
    add('minimum-one',before=[field('max_ammo_pct',-200,'self','capacity-negative')])
    a=field('max_ammo_pct',10,'self','round-a');b=field('max_ammo_pct',10,'self','round-b')
    add('separate-rounding',before=[a,b])
    for e in (a,b):e.update(_source_tag='equipment',_quant_group='same-group')
    add('grouped-rounding',before=[a,b])
    c=add('stack-two',value=2);c['effects'][-1].update(max_stack=3);c['effects'][-1]['trigger']['timing']*=2
    add('arrives-live',after=[field('max_ammo_flat',4,'self','arrive','every:0.4s',max_trigger=1)])
    add('expires-live',before=[field('max_ammo_flat',4,'self','expire',duration=.4)])
    c=add('one-bullet-late');c['effects'][-1].update(duration_bullets=1);c['effects'][-1]['trigger']['timing']=['full_charge_hit'];c['effects'][-1]['max_trigger']=1
    c['effects'].append(field('max_ammo_flat',4,'self','arrive','every:0.4s',max_trigger=1));c['owners'].append(0)
    c=add('one-bullet-start');c['effects'][-1]['duration_bullets']=1
    c=add('condition-false');c['effects'][-1]['trigger']['condition']=['during_full_burst']
    mode=copy.deepcopy(mode_fixtures()[1]['effects'][-1]);mode.update(name='scaling-mode',entry_reload=False,max_ammo=2,reload_time=.3,post_fire_delay=0)
    add('mode-fixed',before=[mode,field('max_ammo_flat',4,'self','ignored-flat')])
    mode['max_ammo_buff_applies']=True
    add('mode-buffed',before=[mode,field('max_ammo_flat',4,'self','flat')])
    add('mode-latched',before=[mode],after=[field('max_ammo_flat',4,'self','late-flat','every:0.4s',max_trigger=1)])
    mode['duration']=.4
    add('mode-expires',before=[mode,field('max_ammo_flat',4,'self','flat')])
    return rows
