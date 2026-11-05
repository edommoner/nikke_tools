"""Literal carrier retirement, retained pools, persistence and revival contracts."""
import copy
from portable_heal_charge_cases import fixtures as prior,instant
from world_enemy_attack_cases import field
from world_frame_native import roster_names

def fixtures():
    seed=copy.deepcopy(prior()[1]);names=roster_names(seed);rows=[]
    def add(kind,target='self',duration=1.5,persist=False,owner=0,revive=True,delayed=False,extra=False,dead=False):
        c=copy.deepcopy(seed);c.update(name='heal-charge-lifetime-'+kind,effects=[],owners=[],contract=dict(kind=kind),duration=.95)
        c['patterns']=[dict(id='down',kind='attack',delay=.3,spec=dict(atk=1e12,coeff=100,target='slot:1',pierce=True,ignore_taunt=True))]
        def put(e,o):c['effects'].append(e);c['owners'].append(o)
        put(field('crit_rate',-100,'all_allies','no-crit'),0)
        pool=field('heal_overcharge_store_atk_pct',150,target,'pool',duration=duration)
        if persist:pool['persist_on_revive']=True
        put(pool,owner)
        put(instant('heal_hp_pct',10,names[0] if owner==0 else target,'deposit','battle_start' if owner==0 else 'every:0.1s',max_trigger=1),0 if owner==0 else owner)
        if extra:put(instant('heal_hp_pct',10,names[1],'other-heal','every:0.35s',max_trigger=1),1)
        if revive:put(instant('revive',50,'allies_down_top_atk_excl:1','revive','every:0.5s' if delayed else 'event:ally_down',max_trigger=1),1)
        put(instant('heal_overcharge_discharge',0,'all_allies','release','every:0.7s',target_effect='pool',max_trigger=1),owner)
        rows.append(c);return c
    add('ended-down-revive',duration=.2)
    add('live-self-down-revive')
    add('persistent-self-down-revive',persist=True)
    add('shared-live-down-revive',target='all_allies')
    add('shared-collect-while-owner-down',target='all_allies',delayed=True,extra=True)
    add('other-owner-recipient-down',target=names[0],owner=1)
    add('other-owner-ended-kept',duration=.2,owner=1)
    add('persistent-owner-still-down',persist=True,revive=False,extra=True)
    add('shared-owner-still-down',target='all_allies',revive=False,extra=True)
    add('ended-owner-still-down',duration=.2,revive=False)
    add('other-recipient-owner-down',target=names[1],delayed=True,extra=True)
    add('shared-expired-while-owner-down',target='all_allies',duration=.4,delayed=True,extra=True)
    return rows
