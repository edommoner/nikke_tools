"""Observe actual calculator inputs/results once, without additional state queries."""
import inspect
from contextlib import contextmanager
from unittest.mock import patch
import engine_worker
from calculator import timeline
from world_frame_native import roster_names
from world_projectile_native import observe as plain

@contextmanager
def capture(names):
    original=timeline.calc_damage;rows=[]
    def calculate(*args,**kwargs):
        caller=inspect.currentframe().f_back
        try:
            if caller.f_code.co_name!='_handle_damage_eff' or caller.f_locals.get('eff',{}).get('stat')!='auto_damage':return original(*args,**kwargs)
            v=caller.f_locals;e=v['eff'];actor=v['cs'];hit=kwargs['hit_type'];weapon=kwargs['weapon']
            row=dict(owner=names.index(v['caster']),time=v['t'],name=e.get('name'),declared=e.get('weapon_type'),base=actor.base_weapon_type,mode_active=actor._in_weapon_change,current=weapon.get('weapon_type'),normal=hit['is_normal_atk'],explosion=hit['is_projectile_explosion'],coeff=hit['coeff'])
            result=original(*args,**kwargs);row['damage']=result['damage'];rows.append(row);return result
        finally:del caller
    with patch.object(timeline,'calc_damage',calculate):yield rows

def observe(case):
    with capture(roster_names(case)) as rows:n,t=plain(case)
    n['skill_weapon_calls']=rows;return n,t
