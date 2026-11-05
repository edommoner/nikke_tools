"""Sampled skill-mode and receipt-group worlds, with no supplied schedule."""
import copy
from portable_coordinate_sampled_vital_cases import fixtures as vital
from portable_coordinate_sampled_battle_cases import fixtures as physical
from portable_coordinate_sampled_skill_cases import damage
from world_enemy_attack_cases import field

def fixtures():
    seeds={c['name'].rsplit('/',1)[1]:c for c in vital()};rows=[]
    def add(label,seed='mode-auto'):
        c=copy.deepcopy(seeds[seed]);c.update(name='coordinate-sampled-delivery/'+label,sampled_delivery=True,seed=181+len(rows),duration=.65);rows.append(c);return c
    def append(c,e,owner=0):c['effects'].append(e);c['owners'].append(owner)
    for label,seed in [('skill-auto','mode-auto'),('skill-charge-parent','mode-charge-parent'),('skill-first','mode-first-coefficient'),('skill-life','lifesteal-packets')]:
        c=add(label,seed)
        for e in c['effects']:
            if e.get('type')=='weapon_change':e['skill_damage']=True
        append(c,field('normal_atk_crit_rate',100,'self','normal-only-rate'))
    def group(label,seed='mode-auto',body=False):
        c=add(label,seed);c['sampled_groups']=True
        if body:c['patterns']=copy.deepcopy(physical()[5]['patterns']);c['enemy']=copy.deepcopy(physical()[5]['enemy'])
        append(c,field('atk_pct',0,'self','group-one','multi_hit:1'));append(c,field('atk_pct',0,'self','group-two','multi_hit:2'))
        e=damage('group-child',stat='bonus_damage',timing='multi_hit:1');e.update(target='target',fixed_value=10);append(c,e);return c
    group('group-body',body=True)
    group('group-parts')
    c=group('group-front');c['patterns']=copy.deepcopy(physical()[1]['patterns']);c['enemy']=copy.deepcopy(physical()[1]['enemy'])
    group('group-muzzles','mode-shotgun-muzzles')
    group('group-charge-parent','mode-charge-parent')
    c=group('group-two-owners','mode-two-casters');append(c,field('atk_pct',0,'self','other-one','multi_hit:1'),1);append(c,field('atk_pct',0,'self','other-two','multi_hit:2'),1)
    for label,hp in [('alive',1e8),('retirement',1)]:
        c=group('group-add-'+label,body=True);c['patterns'].insert(0,dict(id='adds',kind='summon',spec=dict(count=2,hp=hp)))
        for e in c['effects']:
            if e.get('type')=='weapon_change':e.update(pellets=3,muzzles=2)
    c=group('group-buff-next');append(c,field('atk_pct',100,'self','group-atk','multi_hit:1',max_stack=128))
    c=group('group-skill-excluded',body=True);c['duration']=.35
    for e in c['effects']:
        if e.get('type')=='weapon_change':e.update(skill_damage=True,duration=-1)
    return rows
