"""Literal native non-core predicates, independent of portable admission."""
import copy,importlib.util
from pathlib import Path
from portable_ammo_equivalent_cases import fixtures as ammo_fixtures
from portable_nonfull_charge_cases import fixtures as tap_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field


def synthetic_fixtures():
    seed=copy.deepcopy(ammo_fixtures()[0]);seed.pop('contract');seed['effects']=[seed['effects'][0]];seed['owners']=[0];rows=[]
    def add(label,core=0,timing='hit_count',conditions=None):
        c=copy.deepcopy(seed);c['name']='not-core-'+label;c['enemy']['core_px']=core
        c['effects'].append(field('atk_pct',10,'self','noncore-watch',timing=timing,duration=10,max_stack=128,condition=conditions or ['not_core']));c['owners'].append(0);rows.append(c);return c
    add('zero-core')
    add('guaranteed-core',1000000)
    add('fractional-core',10)
    add('small-core',1)
    c=add('last-owner',10);c['owners']=[4,4];c['combat']['weapons'][0],c['combat']['weapons'][4]=c['combat']['weapons'][4],c['combat']['weapons'][0]
    for label,pellets,muzzles in [('pellets3',3,1),('muzzles2',1,2),('scatter15-muzzles2',15,2)]:
        c=add(label,10);c['combat']['weapons'][0].update(pellets=pellets,muzzles=muzzles)
    add('attack-context-absent',1000000,timing='on_attack')
    add('battle-context-absent',1000000,timing='battle_start')
    c=add('last-bullet-context-absent',1000000,timing='last_bullet');c['combat']['weapons'][0]['capacity']=3
    add('first-condition-false',10,conditions=['self_hp_below:1','not_core'])
    add('last-condition-false',10,conditions=['not_core','self_hp_below:1'])
    add('duplicate-condition',10,conditions=['not_core','not_core'])
    c=add('duplicate-descriptor',10);c['effects'][-1]['trigger']['timing']*=2
    add('probability-first-zero',10,conditions=['prob:0','not_core'])
    add('probability-last-zero',10,conditions=['not_core','prob:0'])
    add('independent-probability',10,conditions=['not_core','prob:50'])
    add('every-second-hit',10,timing='hit_count:2')
    c=add('activation-budget',10);c['effects'][-1]['max_trigger']=1
    c=add('frozen-before-accuracy-callback',10);c['effects'].insert(1,field('accuracy_pct',100,'self','change-accuracy','on_attack',duration=10,max_stack=3));c['owners'].insert(1,0)
    c=add('full-charge',10);c['combat']['weapons'][0].update(mode='charge',charge=.05);c['post_fire_delays'][0]=.05
    c=copy.deepcopy(tap_fixtures()[1]);c['name']='not-core-partial-charge';c.pop('contract');c['enemy']['core_px']=10;c['effects'][1]=field('atk_pct',10,'self','noncore-watch','hit_count',duration=10,max_stack=128,condition=['not_core']);rows.append(c)
    add('passive-context',10,timing='passive')
    c=add('nested-notify-restores-parent',10)
    c['effects'][-1]=instant('heal_hp_pct',1,'self','noncore-parent','hit_count');c['effects'][-1]['trigger']['condition']=['not_core']
    c['effects'] += [field('atk_pct',1,'self','noncore-child','event:heal_received',max_stack=128,condition=['not_core']),field('atk_pct',1,'self','noncore-sibling','hit_count',max_stack=128,condition=['not_core'])];c['owners'] += [0,0]
    return rows


def real_fixtures():
    s=importlib.util.spec_from_file_location('not_core_real_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));real=importlib.util.module_from_spec(s);s.loader.exec_module(real)
    name='길로틴 : 윈터 슬레이어'
    return [dict(name='not-core-real/'+name+'/'+str(t)+'s',body=dict(real.body_for(real.policy.roster_for(name),t),burst_gauge_mode='accumulate')) for t in (3,30)]


def fixtures():return synthetic_fixtures()+real_fixtures()
