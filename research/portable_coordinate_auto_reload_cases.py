"""Authored automatic-reload latch/notification worlds; no computed timings."""
import copy
from portable_coordinate_mode_actions_cases import fixtures as modes
from portable_coordinate_sampled_skill_cases import damage
from world_enemy_attack_cases import field

def fixtures():
    base=next(c for c in modes() if c['name'].endswith('/automatic-reload-cover'));rows=[]
    def add(label,*,cover=True,speed_duration=None,witness=True,mode_duration=.75):
        c=copy.deepcopy(base);c.update(name='coordinate-auto-reload/'+label,observe_auto_reload=True,duration=1.2,seed=1021+len(rows))
        if not cover:c['controls'][0]['sequence']=[]
        speed=next(e for e in c['effects'] if e['name']=='fast-reload')
        if speed_duration is not None:speed['duration']=speed_duration
        mode=next(e for e in c['effects'] if e['type']=='weapon_change');mode['duration']=mode_duration
        if witness:
            c['effects'].extend([damage('auto-reload-witness',timing='event:full_reload'),field('atk_pct',20,'self','reload-child','event:full_reload',max_stack=10)])
            c['owners'].extend([0,0])
        rows.append(c);return c
    add('latched-speed-expiry',cover=False,speed_duration=.18)
    add('cover-cancels-phase')
    add('cover-then-speed-expiry',speed_duration=.18)
    c=add('until-reload-cover',speed_duration=.18);c['controls'][0]['sequence'][0]['duration']=None
    add('mode-expiry-latched',cover=False,speed_duration=.18,mode_duration=.2)
    c=add('mode-replacement-latched',cover=False,speed_duration=.18)
    mode=copy.deepcopy(next(e for e in c['effects'] if e['type']=='weapon_change'));mode.update(name='replace-pending-mode',charge=False,weapon_type='AR',duration=.3,trigger=dict(timing=['every:0.2s'],condition=[]),max_trigger=1);c['effects'].append(mode);c['owners'].append(0)
    add('zero-listener',speed_duration=.18,witness=False)
    c=add('zero-duration-cover',speed_duration=.18);c['controls'][0]['sequence'][0]['duration']=0
    c=add('pending-at-end-without-listener',speed_duration=.18,witness=False);c['duration']=.45
    return rows
