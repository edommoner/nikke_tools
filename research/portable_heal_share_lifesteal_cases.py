"""Literal landed-skill/lifesteal prerequisites for shared GPU healing."""
import copy
from portable_heal_share_cases import fixtures as original
from world_enemy_attack_cases import field
from world_frame_native import roster_names


def fixtures():
    base=next(c for c in original() if c['name']=='heal-share-presence-1')
    rows=[]
    def add(label,hp,*,rate=100,plans=1,notices=1,weights=None,damage=None):
        c=copy.deepcopy(base);c['name']='heal-share-lifesteal-'+label;c['enemy']['def']=0
        # Keep native physical attacks outside this short skill-packet window.
        for weapon in c['combat']['weapons']:weapon.update(mode='charge',charge=10,interval=10,min_cycle=10,full_charge_mult=100)
        c['observe_lifesteal']=True;c['observe_heal_sources']=True
        packet=dict(name='packet',source='스킬2',type='damage',stat='bonus_damage',fixed_value=100,target='boss',trigger=dict(timing=['battle_start'],condition=[]))
        c['effects'][-1:]=[field('crit_rate',-100,'self','no-crit'),field('lifesteal_pct',rate,'self','lifesteal'),packet]
        c['owners']=[0]*len(c['effects'])
        c['contract'].update(hp=hp,plans=plans,notices=notices,weights=weights if weights is not None else [(i,1) for i in range(5)],lifesteal_damage=damage if damage is not None else [2000],heal_sources=[0]*notices)
        rows.append(c);return c
    add('five-member',[5400]*5)
    add('zero-rate',[5000]*5,rate=0,plans=0,notices=0,weights=[])
    add('negative-rate',[5000]*5,rate=-100,plans=0,notices=0,weights=[])
    c=add('full-member-storage',[5400]*4+[10000]);c['effects'][0]['target']='allies_top_atk:4'
    c['effects'].insert(-1,field('heal_overcharge_store',20,'all_allies','storage'));c['owners'].insert(-1,0)
    c['contract']['storage']=[0,0,0,0,400]
    c=add('original-multipliers-once',[6200]*5)
    for effect in [field('outgoing_heal_pct',50,'self','outgoing'),field('heal_received_pct',100,'self','received'),field('heal_received_pct',200,'all_allies_excl_self','other-received')]:
        c['effects'].insert(-1,effect);c['owners'].insert(-1,0)
    c=add('rate-provider-is-not-heal-source',[5400]*5);c['owners'][3]=1
    c['effects'][3]['target']=roster_names(c)[0]
    c['effects'][-1]['trigger']['timing']=['every:0.2s']
    c=add('two-packets',[5800]*5,plans=2,notices=2,damage=[2000,2000]);c['effects'][-1]['stat']='bonus_damage:2'
    c['contract']['hp_pct']=[57.99999999999999]*5
    # Native damage clamps rounded low damage to1. Ten percent of that packet
    # gives the independent 0.1 healing boundary without fractional hit damage.
    c=add('one-member-direct-amount',[5000.1,5000,5000,5000,5000],rate=10,weights=[(0,1)],damage=[1])
    c['effects'][1]['target']='self';c['effects'][-1]['fixed_value']=.005
    c['contract'].update(portion_sequence=[(0,.1)],notice_order=[0],original_amounts=[.1])
    c=add('zero-potency-still-notifies',[5000]*5,plans=0,notices=1,weights=[])
    c['effects'].insert(-1,field('outgoing_heal_pct',-100,'self','zero-outgoing'));c['owners'].insert(-1,0)
    c['contract'].update(portion_sequence=[(0,0)],notice_order=[0],original_amounts=[0])
    return rows
