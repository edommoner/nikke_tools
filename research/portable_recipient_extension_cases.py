"""Literal named/B3-cast selectors; same authored programs for both backends."""
import copy
from world_projectile_cases import fixtures as base_fixtures
from world_enemy_attack_cases import field
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(base_fixtures()[0]);base.update(duration=.8,effects=[],owners=[],state_queries=[])
    names=roster_names(base);rows=[]
    for label,target in [('present',names[4]),('absent','프리카'),('ordered-overlap',[names[4],'all_allies']),('ordered-two',[names[1],names[4]])]:
        c=copy.deepcopy(base);c.update(name='named-'+label,
            effects=[field('atk_pct',10,target,'named-'+label)],owners=[0]);rows.append(c)
    for timing in ('battle_start','full_burst_start'):
        c=copy.deepcopy(base);c.update(name='casted-b3-'+timing,effects=[
            dict(name='initial-gauge',source='스킬1',type='instant',stat='burst_charge_pct',fixed_value=100,target='all_allies',trigger=dict(timing=['battle_start'],condition=[])),
            field('atk_pct',10,'allies_burst_casted_burst3','casted-b3',timing)],owners=[0,0])
        for i,w in enumerate(c['combat']['weapons']):w.update(stage=i+1 if i<3 else 3)
        rows.append(c)
    return rows
