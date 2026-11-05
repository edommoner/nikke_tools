"""Dynamic charge, window latching, arbitration and mixed physical controls."""
import copy
from portable_nonfull_charge_cases import fixtures as native_fixtures
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant


def fixtures():
    seed=native_fixtures()[1];rows=[]
    def add(name,partial,full):
        c=copy.deepcopy(seed);c['name']='partial-extended-'+name;c['contract'].update(partial=partial,full=full,activations=partial,hp=[5000+100*partial]+[5000]*4);rows.append(c);return c
    def buff(c,stat,value,**kw):c['effects'].append(field(stat,value,'self','extended-'+stat,**kw));c['owners'].append(0)
    c=add('speed-full',0,3);buff(c,'charge_speed_pct',100)
    c=add('speed-expires',2,1);buff(c,'charge_speed_pct',100,duration=.4)
    c=add('speed-arrives',1,2);buff(c,'charge_speed_pct',100,timing='every:0.4s',max_trigger=1)
    c=add('slow-fixed-full',0,2);c['controls'][0]['click'][0]['rate']=2;buff(c,'charge_time_fixed',.05)
    c=add('slow-fixed-expires',1,1);c['controls'][0]['click'][0]['rate']=2;buff(c,'charge_time_fixed',.05,duration=.4)
    c=add('window-latched-shot',1,2);c['controls'][0]['click'][0]['window']='burst_charge';c['combat']['initial_gauge']=0;c['effects'].insert(0,instant('burst_charge_pct',99,'all_allies','initial-gauge'));c['owners'].insert(0,0)
    for i in range(3):c['combat']['weapons'][i]['stage']=i+1
    c=add('parallel-warn',3,0);c['control_mode']='warn';c['controls'][1]=copy.deepcopy(c['controls'][0])
    c=add('preempted-shot',2,1);c['controls'][1]=dict(sequence=[dict(action='hold',t=.4,until=.8)])
    c=add('spontaneous-full-no-hold-notice',0,1);c['duration']=1.5;c['controls'][0]['click'][0]['rate']=1;buff(c,'atk_pct',1,timing='charge_hold:0',max_stack=10)
    c=add('partial-ignores-charge-buffs',3,0);buff(c,'charge_dmg_pct',100);buff(c,'charge_dmg_mag_pct',100)
    c=add('full-uses-charge-buffs',0,3);buff(c,'charge_speed_pct',100);buff(c,'charge_dmg_pct',100);buff(c,'charge_dmg_mag_pct',100)
    c=add('down-charge-tap',3,0);c['weapon_metadata'].update(input_type='DOWN_Charge',fire_stance_hold=0);c['post_fire_delays']=[0.]*5
    for w in c['combat']['weapons']:w['min_cycle']=.4
    c=add('after-on-attack',3,0)
    gate=instant('gauge_charge',1,'self','partial-order-gate','on_attack');gate.update(gauge_id='partial-order',gauge_max=100,max_trigger=1);c['effects'].append(gate);c['owners'].append(0);c['effects'][1]['trigger']['condition']=['gauge_eq:partial-order:1']
    c=add('before-hit-count',3,0)
    gate=instant('gauge_charge',1,'self','partial-order-gate','non_full_charge_fire_count:1');gate.update(gauge_id='partial-order',gauge_max=100,max_trigger=1);c['effects'].insert(1,gate);c['owners'].insert(1,0);c['effects'][2]['trigger']=dict(timing=['hit_count'],condition=['gauge_eq:partial-order:1']);c['contract']['activation_events']=['hit_count']
    return rows
