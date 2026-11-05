"""Authored auto-skill metadata/current-actor weapon contrast; no GPU oracle."""
import copy
from portable_ammo_equivalent_cases import fixtures as ammo
from world_enemy_attack_cases import field
from portable_entry_reload_cases import fixtures as entry

def fixtures():
    seed=copy.deepcopy(ammo()[0]);seed.pop('contract');rows=[]
    for base in ('AR','RL','SR'):
        for declaration in (None,'AR','RL','SR'):
            c=copy.deepcopy(seed);c['name']='skill-weapon-'+base+'-'+str(declaration)
            for w in c['combat']['weapons']:w.update(mode='charge',charge=10,interval=10,min_cycle=10,full_charge_mult=100)
            c['combat']['weapons'][0]['base_weapon_type']=base
            e=dict(name='weapon-source',source='스킬1',type='damage',stat='auto_damage',damage_formula='normal_attack',fixed_value=100,target='target',tick_interval=.1,duration=.25,tick_start='immediate',trigger=dict(timing=['battle_start'],condition=[]))
            if declaration is not None:e['weapon_type']=declaration
            c['effects']=[field('crit_rate',-100,'self','no-crit'),field('projectile_explosion_dmg_pct',100,'self','explosion-factor'),e];c['owners']=[0]*3
            c['contract']=dict(base=base,declared=declaration,current=[base]*3,explosion=[base=='RL']*3,reference_model_gap=declaration is not None and declaration!=base)
            rows.append(c)
    for base,mode in [('AR','RL'),('RL','SR')]:
        c=copy.deepcopy(next(c for c in rows if c['contract']['base']==base and c['contract']['declared']==base));c['name']='skill-weapon-mode-'+base+'-'+mode
        w=copy.deepcopy(entry()[0]['effects'][-1]);w.update(name='skill-weapon-mode',weapon_type=mode,charge=True,charge_time=10,duration=.15,entry_reload=False);w.pop('duration_bullets',None)
        c['effects'].insert(2,w);c['owners'].insert(2,0)
        c['combat']['weapons'][0].update(mode='auto',interval=.1,min_cycle=.1)
        c['entry_delays']=[dict(owner=0,name='skill-weapon-mode',value=0)]
        c['contract'].update(current=[base]*3,explosion=[base=='RL']*3,mode_active=[False,True,False])
        rows.append(c)
    return rows
