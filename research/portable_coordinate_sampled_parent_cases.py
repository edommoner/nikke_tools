"""Declared sampled full-charge parent cases; no damage or RNG schedules."""
import copy
from portable_coordinate_sampled_battle_cases import fixtures as battles
from world_enemy_attack_cases import field
def fixtures():
    base=battles()[7];rows=[]
    def add(label,pct=25,muzzles=1,pellets=1,timing='full_charge_hit'):
        c=copy.deepcopy(base);c['name']='coordinate-sampled-parent/'+label;c['sampled_parent']=True
        c['combat']['weapons'][0].update(muzzles=muzzles,pellets=pellets)
        c['effects'].append(dict(name='sampled-parent',source='스킬2',type='damage',stat='dealt_fixed_damage',fixed_value=pct,target='target_body',trigger=dict(timing=[timing],condition=[])));c['owners'].append(0);rows.append(c);return c
    add('pierce')
    for muzzles in (3,5,7):add('odd-muzzles-'+str(muzzles),muzzles=muzzles,pellets=7)
    add('zero',pct=0);add('negative',pct=-30);add('truncates-to-zero',pct=.001)
    c=add('duplicate');c['effects'][-1]['trigger']['timing']*=2
    c=add('budget-one');c['effects'][-1]['max_trigger']=1
    add('every-second',timing='full_charge_hit_count:2')
    add('absent-hit-count',timing='hit_count');add('absent-battle-start',timing='battle_start')
    c=add('large-integer',muzzles=3,pellets=7);c['base_atk'][0]=10**16
    c=add('two-shooters',muzzles=3,pellets=7);c['combat']['weapons'][3]=copy.deepcopy(c['combat']['weapons'][0]);c['effects'].append(copy.deepcopy(c['effects'][-1]));c['owners'].append(3)
    c=add('later-atk-buff',muzzles=3,pellets=7);c['effects'].insert(0,field('atk_pct',100,'self','later','full_charge_hit',max_stack=10));c['owners'].insert(0,0)
    c=add('interrupt',muzzles=3,pellets=7);c['patterns'].insert(0,dict(id='interrupt',kind='interrupt',targets=[dict(name='stop',hp=1e8,x=0,y=0,r=3,z=3)]))
    return rows
