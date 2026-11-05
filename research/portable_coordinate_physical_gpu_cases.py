"""Authored extensions to the shared-policy real physical battle corpus."""
import copy
from portable_coordinate_physical_common_cases import fixtures as original
from world_enemy_attack_cases import field


def fixtures():
    rows=original()
    def add(label,index=0):
        case=copy.deepcopy(rows[index]);case['name']='coordinate-physical-gpu/'+label;rows.append(case);return case
    case=add('rotated-rectangle');shape=case['patterns'][0]['targets'][0]
    shape.pop('r');shape.update(x=1.5,y=-1.,w=6.,h=3.,rotation=37.)
    case=add('critical-fraction');case['effects'].pop(0);case['owners'].pop(0)
    case['effects'].append(field('crit_rate',25,'self','critical'));case['owners'].append(0)
    case=add('accuracy');case['effects'].append(field('accuracy_pct',50,'self','accuracy'));case['owners'].append(0)
    case=add('two-owners');case['combat']['weapons'][3]=copy.deepcopy(case['combat']['weapons'][0])
    case=add('unbreakable');case['patterns'][0]['targets'][0]['hp']=0
    case=add('same-shot-retirement',4);case['duration']=.15
    case['combat']['weapons'][0].update(pellets=3,muzzles=2)
    case=add('interrupt-reach',6)
    case['patterns'].insert(0,dict(id='interrupt',kind='interrupt',targets=[dict(name='stop',hp=1e8,x=0,y=0,r=2,z=3)]))
    case['effects'].append(field('intercept_dmg_pct',70,'self','interrupt-factor'));case['owners'].append(0)
    case=add('weapon-change')
    case['effects'].append(dict(name='coordinate-mode',source='스킬1',type='weapon_change',weapon_type='AR',damage_coeff=150,max_ammo=-1,fire_rate=10,fire_rate_max=10,charge=False,charge_time=.2,full_charge_mult=100,pellets=3,muzzles=2,post_fire_delay=0,burst_energy=0,core_dmg_mult=200,skill_damage=True,target='self',duration=2,trigger=dict(timing=['battle_start'],condition=[])))
    case['owners'].append(0)
    return rows
