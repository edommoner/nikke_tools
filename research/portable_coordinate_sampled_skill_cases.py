"""Authored random skill worlds; no precomputed packets or random schedules."""
import copy
from portable_coordinate_sampled_battle_cases import fixtures as battles
from world_enemy_attack_cases import field

def damage(name='source',stat='bonus_damage',timing='on_attack',**kw):
    return dict(name=name,source='스킬1',type='damage',stat=stat,fixed_value=100,target='target_body',trigger=dict(timing=[timing],condition=[]),**kw)

def fixtures():
    rows=[]
    def add(label,effects,index=5,owners=None):
        c=copy.deepcopy(battles()[index]);c.update(name='coordinate-sampled-skill/'+label,sampled_skill=True)
        c['effects']+=effects;c['owners']+=owners or [0]*len(effects);rows.append(c);return c
    for value in (-100,0,35,85,200):add('rate-'+str(value),[field('crit_rate',value,'self','rate'),damage(stat='bonus_damage:3')])
    add('multi-hit-frozen-buffs',[field('crit_rate',35,'self','rate'),damage(stat='bonus_damage:5'),field('atk_pct',100,'self','child-atk','hit_count:source:1',max_stack=10),field('crit_rate',100,'self','child-rate','hit_count:source:1',max_stack=10)])
    for stat in ('core_damage:3','armor_break_damage:3','burst_damage:3','projectile_attachment_damage:3','sequential_damage:3','split_damage:3'):
        add('family-'+stat.split(':')[0],[damage(stat=stat)])
    c=add('normal-formula',[field('normal_atk_crit_rate',80,'self','normal-rate'),damage(stat='bonus_damage:3')]);c['effects'][-1]['damage_formula']='normal_attack'
    child=damage('child',stat='bonus_damage:2',timing='hit_count:source:1');child['trigger']['condition']=['trigger_hit_crit']
    add('nested-critical-children',[field('crit_rate',35,'self','rate'),damage(stat='bonus_damage:3'),child,field('atk_pct',10,'self','critical-witness','hit_count:child:1',condition=['trigger_hit_crit'],max_stack=10)])
    c=add('two-casters',[damage(),damage('other')],owners=[0,1]);c['combat']['weapons'][1]=copy.deepcopy(c['combat']['weapons'][0])
    add('battle-start-before-physical',[damage(timing='battle_start',stat='bonus_damage:3')])
    add('zero-coefficient',[dict(damage(),fixed_value=0)])
    c=add('periodic',[damage(stat='dot_damage',timing='battle_start')]);c['effects'][-1].update(duration=.3,tick_interval=.05)
    c=add('parts-reuse-critical',[damage(stat='bonus_damage:3',hits_parts=True)],index=6)
    c=add('pierce-reuse-critical',[damage(stat='pierce_damage:3')],index=6)
    c=add('explosion-reuse-critical',[damage(stat='projectile_explosion_damage:3')],index=6)
    c=add('parent-and-ordinary',[damage(stat='bonus_damage:3'),damage('parent',stat='dealt_fixed_damage',timing='full_charge_hit')],index=7)
    return rows
