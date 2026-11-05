"""Actual fire/charge/pellet/mode methods with the owning BossScript clock."""
import copy
from destructible_shield_battle_cases import fixtures as prior
from world_enemy_attack_cases import field

def fixtures():
    base=copy.deepcopy(prior()[0]);base['effects']=base['effects'][:1];base['owners']=base['owners'][:1]
    rows=[]
    def add(name,*,kind=3,capacity=10000.,pellets=1,muzzles=1):
        c=copy.deepcopy(base);c.update(name='destructible-weapon-shield/'+name,weapon_shield_interception_v1=True,hit_shield_interception_v1=True)
        c['typed_bindings'][0].update(kind=kind,capacity=capacity)
        c['combat']['weapons'][0].update(pellets=pellets,muzzles=muzzles)
        rows.append(c);return c
    add('auto-hp-factor')
    add('auto-hit-credit',kind=4,capacity=2.)
    add('auto-break-no-overflow',capacity=500.)
    add('scatter-hp-factor',pellets=3)
    add('scatter-hit-break-before-third',kind=4,capacity=2.,pellets=3)
    c=add('scatter-hp-then-hit-then-body',capacity=300.,pellets=3);c['typed_bindings'].append(dict(node='idle',kind=4,identity=11,capacity=1.,owner=[0,0,1]))
    c=add('scatter-hit-then-hp',kind=4,capacity=1.,pellets=3);c['typed_bindings'].append(dict(node='idle',kind=3,identity=11,capacity=10000.,owner=[0,0,1]))
    from target_counter_cases import marker
    def watched(c,kind,child):
        m=marker(threshold=1,actor=dict(kind=kind,identity=10,generation=1),on_death=False,attackers='squad');m['target']='boss';m['trigger']['timing']=['battle_start']
        c['effects']=[m,*c['effects'],child];c['owners']=[0,*c['owners'],0];c['observe_target_counters']=True
    c=add('scatter-counter-child-keeps-shot-buff-snapshot',pellets=3)
    watched(c,'hp_shield',field('atk_pct',100,'self','counter-child','event:target_counter_complete:marker',duration=10))
    c=add('scatter-counter-skill-consumes-separate-credit',kind=4,capacity=2.,pellets=3)
    child=dict(name='counter-skill',source='스킬2',type='damage',stat='damage',target='boss',fixed_value=50.,trigger=dict(timing=['event:target_counter_complete:marker'],condition=[]))
    watched(c,'hit_shield',child)
    c=add('full-charge-hp-context');c['duration']=.5;c['combat']['weapons'][0].update(mode='charge',charge=.1,interval=.2,min_cycle=.2,full_charge_mult=200,base_weapon_type='SR');c['post_fire_delays'][0]=.215
    c=add('charge-scatter-hp-context',pellets=3);c['duration']=.5;c['combat']['weapons'][0].update(mode='charge',charge=.1,interval=.2,min_cycle=.2,full_charge_mult=200,base_weapon_type='SR');c['post_fire_delays'][0]=.215
    c=add('tap-hit-credit',kind=4,capacity=2.);c['duration']=.95;c['combat']['weapons'][0].update(mode='charge',charge=.2,interval=.2,min_cycle=.1,full_charge_mult=300,base_weapon_type='SR');c['controls']=[dict(click=[dict(window='always',mode='tap',rate=4,release=.05)]),{},{},{},{}];c['post_fire_delays'][0]=.215
    from world_overlay_skill_mode_cases import fixtures as modes
    template=modes()[0]['effects'][0]
    for skill in (False,True):
        c=add('weapon-change-'+str(skill));m=copy.deepcopy(template);m.update(name='declared-mode',duration=.2,skill_damage=skill)
        c['effects'].extend([m,field('normal_atk_dmg_pct',100,'self','normal-factor')]);c['owners'].extend([0,0])
    c=add('empty-owner-keeps-body');c['typed_bindings'][0].pop('owner')
    c=add('world-expiry-keeps-later-body');c['patterns'][0]['until']['time']=.15
    c=add('core-context-is-preserved');c['enemy']['core_px']=1000000.
    add('two-muzzles-hit-credit',kind=4,capacity=3.,muzzles=2)
    c=add('last-squad-owner');c['combat']['weapons'][4]=copy.deepcopy(c['combat']['weapons'][0]);c['post_fire_delays'][4]=0;c['combat']['weapons'][0].update(mode='charge',charge=10,interval=10,min_cycle=10);c['owners']=[4];c['post_fire_delays'][0]=.215
    c=add('two-allied-attackers',kind=4,capacity=1.);c['combat']['weapons'][1]=copy.deepcopy(c['combat']['weapons'][0]);c['post_fire_delays'][1]=0
    c=add('rl-explosion-charge-context');c['duration']=.5;c['combat']['weapons'][0].update(mode='charge',charge=.1,interval=.2,min_cycle=.2,full_charge_mult=200,base_weapon_type='RL');c['effects'].append(field('projectile_explosion_dmg_pct',100,'self','explosion-factor'));c['owners'].append(0);c['post_fire_delays'][0]=.215
    c=add('hp-policy-skips-hit-shield',kind=4,capacity=2.);c['hit_shield_interception_v1']=False
    return rows
