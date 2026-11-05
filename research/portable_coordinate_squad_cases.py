"""Squad action literals; no recipient mask or action timetable from simulate."""
import copy
from portable_coordinate_policy_cases import fixtures as policies
from world_frame_native import roster_names
from world_enemy_attack_cases import field

def fixtures():
    base=policies()[0];names=roster_names(base);rows=[]
    def add(label,sequence):
        c=copy.deepcopy(base);c.update(name='coordinate-squad/'+label,squad_controls=True,duration=2.,sequence=sequence,seed=601+len(rows));c['controls']=[{} for _ in range(5)];rows.append(c);return c
    add('no-owner', [dict(t=.2,action='cover_all',duration=.3)])
    add('forced-owner',[dict(t=.1,action='focus',target=names[2]),dict(t=.2,action='cover_all',duration=.3)])
    c=add('live-owner',[dict(t=.2,action='cover_all',duration=.3)]);c['controls'][1]={'sequence':[dict(t=.1,action='cover',duration=.5)]}
    add('cover-before-focus',[dict(t=.2,action='cover_all',duration=.3),dict(t=.2,action='focus',target=names[2])])
    add('focus-before-cover',[dict(t=.2,action='focus',target=names[2]),dict(t=.2,action='cover_all',duration=.3)])
    add('release-focus',[dict(t=.1,action='focus',target=names[2]),dict(t=.2,action='focus',target=''),dict(t=.2,action='cover_all',duration=.3)])
    add('unsorted',[dict(t=.4,action='cover_all',duration=.2),dict(t=.1,action='focus',target=names[2])])
    add('until-reload',[dict(t=.2,action='cover_all')])
    add('zero-at-zero',[dict(t=0,action='cover_all',duration=0)])
    add('zero-later',[dict(t=.2,action='cover_all',duration=0)])
    add('repeated',[dict(t=.2,action='cover_all',duration=.8),dict(t=.4,action='cover_all',duration=.1)])
    c=add('blocked',[dict(t=.2,action='cover_all',duration=.3)]);c['effects'].append(field('cover_disabled',1,'self','squad-blocked'));c['owners'].append(1)
    c=add('policy-composition',[dict(t=.7,action='cover_all',duration=.3)]);c['controls'][0]={'cover':{'policy':'own_full_burst'}}
    c=add('sequence-composition',[dict(t=.2,action='cover_all',duration=.3)]);c['controls'][1]={'sequence':[dict(t=.2,action='cover',duration=.1)]}
    from portable_entry_reload_cases import fixtures as entries
    for label,at,trigger,duration in [('active-mode',.2,['battle_start'],.45),('new-mode-same-frame',.2,['every:0.2s'],.45),('expired-mode',.5,['battle_start'],.3)]:
        c=add(label,[dict(t=at,action='cover_all',duration=.2)])
        mode=copy.deepcopy(entries()[0]['effects'][-1]);mode.update(entry_reload=False,duration=duration,trigger=dict(timing=trigger,condition=[]),max_trigger=1)
        c['effects'].append(mode);c['owners'].append(0)
    c=add('partial-clips',[dict(t=.2,action='cover_all',duration=.1)]);c['combat']['weapons'][0]['clip_count']=3;c['weapon_metadata']['clip_count']=3
    return rows
