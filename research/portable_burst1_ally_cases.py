"""Authored live B1 roster-presence contracts; no GPU-derived expectations."""
import copy
from portable_ammo_equivalent_cases import fixtures as ammo
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field
from world_frame_native import roster_names

def fixtures():
    seed=copy.deepcopy(ammo()[0]);seed.pop('contract');rows=[]
    def add(label,condition,stages,expected,owner=0):
        c=copy.deepcopy(seed);c['name']='burst1-ally-'+label
        for w,stage in zip(c['combat']['weapons'],stages):w['stage']=stage
        if owner!=0:c['combat']['weapons'][0],c['combat']['weapons'][owner]=c['combat']['weapons'][owner],c['combat']['weapons'][0]
        e=instant('heal_hp_pct',10,'self','burst1-listener','on_attack');e['trigger']['condition']=[condition]
        c['effects']=[instant('current_hp_reduce',50,'all_allies','drain'),e];c['owners']=[0,owner]
        c['contract']=dict(owner=owner,condition=condition,results=expected,hp=5000+1000*sum(expected));rows.append(c);return c
    for kind in ('has','no'):
        condition='has_burst1_ally' if kind=='has' else 'no_burst1_ally';yes=kind=='has'
        add(kind+'-self-only',condition,[1,2,3,3,3],[not yes]*3)
        add(kind+'-other',condition,[2,1,3,3,3],[yes]*3)
        add(kind+'-absent',condition,[2,2,3,3,3],[not yes]*3)
        c=add(kind+'-down-other-still-counts',condition,[2,1,3,3,3],[yes]*3)
        c['patterns']=[dict(id='down-b1',kind='attack',delay=0,spec=dict(atk=1e12,coeff=100,target='slot:2',ignore_taunt=True))]
        c=add(kind+'-live-override-expires',condition,[2,2,3,3,3],[yes,not yes,not yes])
        c['effects'].insert(1,field('burst_stage_override:1',1,'self','temporary-b1',duration=.05));c['owners'].insert(1,1)
        c=add(kind+'-self-override-excluded',condition,[2,2,3,3,3],[not yes]*3)
        c['effects'].insert(1,field('burst_stage_override:1',1,'self','self-temporary-b1',duration=.05));c['owners'].insert(1,0)
    return rows
