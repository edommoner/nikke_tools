"""Authored manual mode-reload stimuli; no computed schedule or battle state."""
import copy
from portable_entry_reload_cases import fixtures as entry_fixtures
from world_enemy_attack_cases import field


def fixtures():
    base=copy.deepcopy(entry_fixtures()[0]);base['duration']=1.1
    base['combat']['weapons'][0]['capacity']=100
    mode=base['effects'][-1];mode.update(name='swap-mode',entry_reload=False,duration=2)
    mode['trigger']=dict(timing=['event:full_reload'],condition=['self_state:swap-gate'])
    gate=field('atk_pct',0,'self','swap-gate')
    base.update(effects=[gate,mode],owners=[0,0],manual_swap=[True,False,False,False,False])
    rows=[]
    def add(label):
        c=copy.deepcopy(base);c['name']='manual-swap-'+label;rows.append(c);return c
    add('ready-at-start')
    c=add('disabled');c['manual_swap'][0]=False
    c=add('absent');c.pop('manual_swap')
    c=add('no-condition');c['effects'][1]['trigger']['condition']=[]
    c=add('wrong-event');c['effects'][1]['trigger']['timing']=['event:unrelated']
    c=add('false-condition');c['effects'][1]['trigger']['condition']=['self_state:missing']
    c=add('other-owner');c['owners'][1]=4
    c=add('last-owner');c['owners']=[4,4];c['manual_swap']=[False]*4+[True]
    c=add('gate-arrives');c['effects'][0]['trigger']['timing']=['every:0.2s'];c['effects'][0]['max_trigger']=1
    c=add('gate-expires-before-finish');c['effects'][0]['duration']=.2
    c=add('speed');c['effects'].insert(0,field('reload_speed_pct',50,'self','speed'));c['owners'].insert(0,0)
    c=add('speed-expires-latched');c['effects'].insert(0,field('reload_speed_pct',50,'self','speed',duration=.1));c['owners'].insert(0,0)
    c=add('fixed-zero');c['effects'].insert(0,field('reload_time_fixed',0,'self','fixed'));c['owners'].insert(0,0)
    c=add('fixed-negative');c['effects'].insert(0,field('reload_time_fixed',-.2,'self','fixed'));c['owners'].insert(0,0)
    c=add('charge-cancel');c['effects'][0]['trigger']['timing']=['every:0.1s'];c['effects'][0]['max_trigger']=1;c['combat']['weapons'][0].update(mode='charge',base_weapon_type='SR',charge=.4,interval=.4,min_cycle=.4);c['post_fire_delays'][0]=0
    c=add('already-active');c['effects'][1]['trigger']['timing'].insert(0,'battle_start')
    c=add('reenter');c['effects'][1]['duration']=.2;c['duration']=1.8
    c=add('exhausted-budget');c['effects'][1]['duration']=.2;c['effects'][1]['max_trigger']=1;c['duration']=1.8
    c=add('condition-alternative');c['effects'].insert(1,dict(copy.deepcopy(mode),name='false-mode',trigger=dict(timing=['event:full_reload'],condition=['self_state:missing'])));c['owners'].insert(1,0)
    c=add('cover-pump-order');c['controls'][0]=dict(sequence=[dict(action='cover',t=0,duration=.2)])
    c=add('charge-mode');c['effects'][1].update(weapon_type='SR',charge=True,charge_time=.2)
    c=add('non-weapon-effect');c['effects'][1]=field('atk_pct',10,'self','not-mode',timing='event:full_reload',condition=['self_state:swap-gate'])
    c=add('and-false');c['effects'][1]['trigger']['condition'].append('self_hp_below:1')
    c=add('duplicate-trigger');c['effects'][1]['trigger']['timing']*=2
    return rows
