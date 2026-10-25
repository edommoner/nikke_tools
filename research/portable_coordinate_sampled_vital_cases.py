"""Authored sampled weapon/health worlds; no GPU schedule or oracle."""
import copy
from portable_coordinate_sampled_battle_cases import fixtures as battles
from portable_coordinate_sampled_burst_cases import fixtures as bursts
from portable_entry_reload_cases import fixtures as entries
from portable_coordinate_sampled_skill_cases import damage
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field

def fixtures():
    rows=[]
    def add(label,base=None):
        c=copy.deepcopy(battles()[6] if base is None else base);c.update(name='coordinate-sampled-vital/'+label,sampled_vital=True,sampled_burst=True,sampled_skill=True,coordinate_packet_trace=False,duration=.9,seed=121+len(rows))
        for a in c['environment']['allies']:a['base_hp']=10000
        c['environment']['allies'][4]['base_hp']=20000
        c['effects'].append(field('crit_rate',35,'self','sampled-rate'));c['owners'].append(0);rows.append(c);return c
    def append(c,e,owner=0):c['effects'].append(e);c['owners'].append(owner);return e
    def mode(c,**kw):
        e=copy.deepcopy(entries()[0]['effects'][-1]);e.update(entry_reload=False,damage_coeff=123,duration=.45);e.update(kw);append(c,e);return e
    mode(add('mode-auto'))
    mode(add('mode-charge'),charge=True,charge_time=.1,weapon_type='SR')
    mode(add('mode-shotgun-muzzles'),weapon_type='SG',pellets=4,muzzles=3)
    mode(add('mode-charge-muzzles'),charge=True,charge_time=.1,weapon_type='RL',pellets=3,muzzles=2)
    c=add('mode-charge-parent');mode(c,charge=True,charge_time=.1,weapon_type='RL',pellets=3,muzzles=2);append(c,damage('parent',stat='dealt_fixed_damage',timing='full_charge_hit'))
    mode(add('mode-first-coefficient'),first_damage_coeff=277,pellets=3)
    mode(add('mode-bullet-exhaustion'),duration=-1,duration_bullets=2,pellets=3)
    mode(add('mode-expired-before-entry'),entry_reload=True,reload_time=.3,duration=.1)
    mode(add('mode-entry-reload'),entry_reload=True,reload_time=.2)
    mode(add('mode-delayed'),trigger=dict(timing=['every:0.2s'],condition=[]),max_trigger=1)
    c=add('mode-replacement');mode(c,duration=-1);mode(c,name='replacement',charge=True,charge_time=.1,weapon_type='SR',duration=.2,trigger=dict(timing=['every:0.3s'],condition=[]),max_trigger=1)
    mode(add('mode-toggle'),toggle=True,duration=-1,trigger=dict(timing=['battle_start','every:0.3s'],condition=[]),max_trigger=2)
    c=add('mode-two-casters');c['combat']['weapons'][1]=copy.deepcopy(c['combat']['weapons'][0]);mode(c,pellets=2);e=copy.deepcopy(c['effects'][-1]);e.update(name='other-mode',muzzles=2);append(c,e,1)
    c=add('mode-skill-child');mode(c,pellets=3,muzzles=2);append(c,damage(stat='bonus_damage:3'))
    c=add('mode-burst-legacy',bursts()[0]);mode(c,pellets=2)
    c=add('mode-burst-optin',next(c for c in bursts() if c['name'].endswith('/optin-three')));mode(c,charge=True,charge_time=.1,weapon_type='SR')
    def health(label,**kw):
        c=add(label);append(c,instant('current_hp_reduce',60,'all_allies','drain'));e=instant('heal_hp_pct',10,'self','heal','every:0.2s');e.update(kw);append(c,e);return c
    health('heal-self')
    health('heal-allies',target='all_allies')
    health('heal-zero',fixed_value=0)
    health('heal-overflow',fixed_value=200)
    health('heal-negative',fixed_value=-10)
    c=health('heal-received-bonus',target='all_allies');append(c,field('heal_received_pct',50,'all_allies','received'))
    c=health('heal-caster-maxhp',target='all_allies',scaling='max_hp');append(c,field('max_hp_pct',50,'self','large'))
    c=health('heal-other-owner',target='all_allies',scaling='max_hp');c['owners'][-1]=4
    c=health('heal-notification-child');append(c,field('atk_pct',10,'self','healed','event:heal_received',max_stack=10))
    c=add('lifesteal-packets');append(c,instant('current_hp_reduce',80,'self','drain'));append(c,field('lifesteal_pct',50,'self','life'));mode(c,pellets=3,muzzles=2)
    c=add('cover-repair');c['combat']['weapons'][0].update(capacity=1,reload=.4);c['patterns'].append(dict(id='cover-hit',kind='attack',delay=.2,spec=dict(atk=500,coeff=100,target='slot:1',ignore_taunt=True)));append(c,instant('cover_heal_pct',25,'self','repair','every:0.3s'),0)
    c=copy.deepcopy(rows[-1]);c.update(name='coordinate-sampled-vital/cover-broken-no-revive',seed=121+len(rows));c['patterns'][-1]['spec']['atk']=2000;rows.append(c)
    c=add('mode-health-mixed',bursts()[0]);mode(c,pellets=3,muzzles=2);append(c,instant('current_hp_reduce',50,'all_allies','drain'));append(c,instant('heal_hp_pct',10,'all_allies','heal','full_burst_start'));append(c,field('lifesteal_pct',25,'self','life'))
    return rows
