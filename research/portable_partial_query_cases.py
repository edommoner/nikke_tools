"""Partial/full charge clocks with real lazy and direct numeric consumers."""
import copy
from portable_nonfull_charge_cases import fixtures as charge_fixtures
from world_enemy_attack_cases import field


def fixtures():
    rows=[]
    for label in ('late-caster','late-hp','mapped-speed','mapped-flat','mapped-fixed','speed-and-late','expires','post-hit-mutation','periodic-full','spontaneous-full','automatic','reload','callback-mode','logging'):
        c=copy.deepcopy(charge_fixtures()[22 if label=='callback-mode' else 1]);c.pop('contract')
        c['name']='partial-query-'+label;c['seed']=19;c['environment']['allied_seed']=19
        def buff(stat,value,target='allies_random:1',owner=4,**kw):
            c['effects'].append(field(stat,value,target,'query-'+stat,**kw));c['owners'].append(owner)
        if label.startswith('mapped-'):
            stat,value={'mapped-speed':('charge_speed_pct',30),'mapped-flat':('charge_time_flat',-.15),'mapped-fixed':('charge_time_fixed',.1)}[label]
            buff(stat,value)
        else:
            buff('atk_from_hp_pct' if label=='late-hp' else 'atk_caster_based_pct',10,duration=.4 if label=='expires' else -1)
        if label=='speed-and-late':buff('charge_speed_pct',30,target='allies_random:2')
        if label=='post-hit-mutation':buff('atk_pct',0,target='self',owner=0,timing='on_attack',max_stack=128)
        if label=='periodic-full':c['controls'][0]['click'][0]['full_charge_interval']=.3
        if label=='spontaneous-full':c['duration']=1.5;c['controls'][0]['click'][0]['rate']=1
        if label=='automatic':c['controls']=[{} for _ in range(5)]
        if label=='reload':c['combat']['weapons'][0].update(capacity=1,reload=.2)
        if label=='logging':c['native_snapshot_logging']=True;c['environment']['native_snapshot_logging']=True
        rows.append(c)
    c=copy.deepcopy(rows[12]);c['name']='partial-query-callback-round-limit';c['effects'][2].pop('duration');c['effects'][2]['duration_bullets']=3;rows.append(c)
    c=copy.deepcopy(rows[7]);c['name']='partial-query-full-mutation';c['controls']=[{} for _ in range(5)];c['effects'][1]['trigger']['timing']=['full_charge_fire_count:1'];rows.append(c)
    c=copy.deepcopy(rows[7]);c['name']='partial-query-auto-mutation';c['controls']=[{} for _ in range(5)];c['combat']['weapons'][0].update(mode='auto',interval=.1,min_cycle=.1);c['post_fire_delays'][0]=0.;c['effects'][1]['trigger']['timing']=['on_attack']
    mutation=c['effects'].pop();owner=c['owners'].pop();c['effects'].insert(1,mutation);c['owners'].insert(1,owner);rows.append(c)
    return rows
