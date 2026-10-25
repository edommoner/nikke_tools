"""Actual world overlays, direct boss attacks and valid split damage with geometry."""
import copy
from portable_coordinate_group_cases import fixtures as groups
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant

def fixtures():
    base=groups()[0];rows=[]
    def add(label,adds=0,hp=1e8):
        c=copy.deepcopy(base);c.update(name='coordinate-group-common/mixed-'+label,duration=.35)
        if adds:c['patterns'].insert(0,dict(id='adds',kind='summon',spec=dict(count=adds,hp=hp)))
        rows.append(c);return c
    def split(c,target='all_enemies',parts=False):
        e=dict(name='mixed-split',source='declared',type='damage',stat='split_damage',fixed_value=100,target=target,trigger=dict(timing=['every:0.1s'],condition=[]),max_trigger=1)
        if parts:e['hits_parts']=True
        c['effects'].append(e);c['owners'].append(0)
    split(add('split-all',2))
    split(add('split-add-retirement',3,1))
    split(add('split-ranked',2),'enemies_top_hp:2')
    split(add('split-random',7),'enemies_random:3')
    for adds in (0,2):
        c=add('vanish-'+str(adds),adds);c['patterns'].append(dict(id='hide',kind='vanish',until=dict(time=.15)))
        c=add('shield-'+str(adds),adds);c['patterns'].append(dict(id='guard',kind='shield',code='작열',until=dict(time=.15)))
    c=add('buff-order');c['patterns'].extend([dict(id='def',kind='buff',enemy=dict(def_add=100)),dict(id='received',kind='buff',enemy=dict(received_dmg_pct=-50),until=dict(time=.15))])
    c=add('move-distance');c['patterns'].append(dict(id='far',kind='move',distance=70,until=dict(time=.15)))
    c=add('move-weapon');c['patterns'].append(dict(id='reach',kind='move',weapons=['SR'],until=dict(time=.15)))
    def attack(c):c['patterns'].append(dict(id='incoming',kind='attack',delay=.05,spec=dict(atk=300,coeff=100,target='all',hits=3,interval=.1)))
    attack(add('boss-attack'))
    c=add('boss-attack-lifesteal',2);attack(c);c['effects'].insert(0,instant('current_hp_reduce',50,'self','drain'));c['owners'].insert(0,0);c['effects'].append(field('lifesteal_pct',10,'self','leech'));c['owners'].append(0)
    c=add('groggy',2);c['patterns'].append(dict(id='down',kind='groggy',delay=.1,until=dict(time=.2)))
    c=add('core-add',2);c['enemy']['coord']['auto_aim']=None;c['patterns'].extend([dict(id='core-a',kind='core',core_px=8,x=4,y=1),dict(id='core-b',kind='core',core_px=8,x=-4,y=1,delay=.15)])
    c=add('combined-split-parts',2);c['duration']=.45;split(c,parts=True);attack(c);c['patterns'].append(dict(id='hide',kind='vanish',delay=.15,until=dict(time=.25)))
    for label,coefficient,adds in [('split-tie-odd',.15,1),('split-tie-even',.25,1),('split-round-zero',.05,2)]:
        c=add(label,adds);split(c);c['effects'][-1]['fixed_value']=coefficient
    return rows
