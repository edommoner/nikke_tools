"""Native character-mode boundaries; authored times and effects only."""
import copy,math
from portable_coordinate_squad_cases import fixtures as squads
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant

def fixtures():
    base=next(c for c in squads() if c['name'].endswith('/expired-mode'));rows=[]
    def add(label,at,*,duration=.7):
        c=copy.deepcopy(base);c.update(name='coordinate-squad-mode/'+label,squad_mode_state=True,duration=duration,seed=701+len(rows));c['sequence']=[] if at is None else [dict(t=at,action='cover_all',duration=.1)];rows.append(c);return c
    def mode(c):return next(e for e in c['effects'] if e['type']=='weapon_change')
    add('finite-before',.28)
    add('finite-exact',.3)
    add('finite-next-frame',math.nextafter(.3,math.inf))
    add('finite-later',.5)
    for label,at in [('charge-exact',.3),('charge-after',.32)]:mode(add(label,at)).update(charge=True,charge_time=.1,weapon_type='SR')
    for label,at in [('bullet-next-pump',.01),('bullet-next-base',.02)]:mode(add(label,at)).update(duration=-1,duration_bullets=1)
    for label,at in [('toggle-exact',.3),('toggle-after',.32)]:mode(add(label,at)).update(duration=-1,toggle=True,trigger=dict(timing=['battle_start','every:0.3s'],condition=[]),max_trigger=2)
    for label,at in [('stunned-exit',.4),('stunned-after',.6)]:
        c=add(label,at);c['effects'].append(field('stun',1,'self','pause-mode-exit',timing='every:0.1s',duration=.4,max_trigger=1));c['owners'].append(0)
    add('end-in-mode',.1,duration=.2)
    add('no-squad-actions',None,duration=.2)
    for label,with_mode in [('revive-base',False),('revive-mode',True)]:
        c=add(label,.3)
        if with_mode:mode(c)['duration']=.6
        if not with_mode:
            i=next(i for i,e in enumerate(c['effects']) if e['type']=='weapon_change');c['effects'].pop(i);c['owners'].pop(i)
        c['patterns'].append(dict(id='mode-lethal',kind='attack',delay=.3,spec=dict(atk=1e8,coeff=100,target='slot:1',ignore_taunt=True,pierce=True)))
        c['effects'].append(dict(instant('revive',50,'allies_down_top_atk_excl:1','mode-revive','event:ally_down'),max_trigger=1));c['owners'].append(1)
    c=add('reload-activated',.3);c['combat']['weapons'][0].update(capacity=1,reload=.1);mode(c).update(trigger=dict(timing=['event:full_reload'],condition=[]),duration=.1)
    c=add('two-mode-owners',.3);e=copy.deepcopy(mode(c));e['name']='second-mode';c['effects'].append(e);c['owners'].append(1)
    c=add('owner4-exact',.3);i=next(i for i,e in enumerate(c['effects']) if e['type']=='weapon_change');c['owners'][i]=4
    mode(add('entry-wait-exact',.3)).update(entry_reload=True,reload_time=.6)
    c=copy.deepcopy(next(c for c in rows if c['name'].endswith('/reload-activated')));c.update(name='coordinate-squad-mode/reload-activated-entry-wait',duration=.9,seed=701+len(rows));mode(c).update(entry_reload=True,duration=.35);rows.append(c)
    c=add('cover-policy-expiry',None,duration=1.);mode(c)['duration']=.6;c['controls'][0]={'cover':{'policy':'own_full_burst'}}
    c=add('cover-policy-expiry-stunned',None,duration=1.1);mode(c)['duration']=.6;c['controls'][0]={'cover':{'policy':'own_full_burst'}};c['effects'].append(field('stun',1,'self','late-pause',timing='every:0.55s',duration=.25,max_trigger=1));c['owners'].append(0)
    c=add('cover-policy-expiry-forced',None,duration=1.);mode(c)['duration']=.6;c['controls'][0]={'cover':{'policy':'own_full_burst'}}
    from world_frame_native import roster_names
    c['sequence']=[dict(t=.1,action='focus',target=roster_names(c)[0])]
    return rows
