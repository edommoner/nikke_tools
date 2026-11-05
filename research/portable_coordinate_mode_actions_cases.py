"""Literal mode/control boundary worlds; no simulated schedules as GPU input."""
import copy
from portable_coordinate_manual_cases import fixtures as manual
from world_enemy_attack_cases import field

def fixtures():
    rows=[];base=next(c for c in manual() if c['name'].endswith('/mode-charge'))
    def hold(t=0,until=.5):return dict(action='hold',t=t,until=until)
    def cover(t=.2,duration=.1):return dict(action='cover',t=t,duration=duration)
    def add(label,sequence,*,base_charge=True,**mode):
        c=copy.deepcopy(base);c.update(name='coordinate-mode-actions/'+label,duration=.9,seed=941+len(rows))
        c['controls'][0]={'sequence':copy.deepcopy(sequence)}
        w=c['combat']['weapons'][0]
        if base_charge:
            c['weapon_metadata']['input_type']='UP';w.update(mode='charge',base_weapon_type='SR',charge=.1,interval=.315,min_cycle=0,full_charge_mult=100)
            c['post_fire_delays'][0]=.215
        e=next(e for e in c['effects'] if e['type']=='weapon_change')
        e.update(duration=.75,charge=True,charge_time=.1,post_fire_delay=.2,weapon_type='SR',max_ammo=20)
        e.update(mode);rows.append(c);return c
    add('hold-active-mode',[hold(until=.45)])
    add('cover-then-hold',[cover(.1,.2),hold(.2,.6)])
    add('hold-then-cover',[hold(until=.7),cover()])
    add('same-frame-ordered',[hold(until=.7),cover(0,.1),hold(until=.5)])
    add('hold-release-before-ready',[hold(until=.05)])
    add('hold-none',[hold(until=None)])
    add('cover-post-delay-base-charge',[cover(.2,.05)])
    add('cover-post-delay-base-auto',[cover(.2,.05)],base_charge=False)
    add('cover-post-delay-until-reload',[cover(.2,None)])
    add('cover-post-delay-zero',[cover(.2,0)])
    add('cover-post-delay-mode-expires',[cover(.2,.2)],duration=.3)
    add('hold-mode-expires',[hold(until=.6)],duration=.3)
    add('hold-mode-auto',[hold(until=.6)],charge=False,weapon_type='AR',fire_rate=10)
    add('entry-wait-cover-hold',[cover(.1,.15),hold(.2,.6)],entry_reload=True,reload_time=.2)
    c=add('automatic-reload-post-delay',[],cover_during_delay=True,max_ammo=2)
    c['effects'].append(field('reload_speed_pct',100,'self','fast-reload'));c['owners'].append(0)
    c=add('automatic-reload-cover',[cover(.2,.05)],cover_during_delay=True,max_ammo=2)
    c['effects'].append(field('reload_speed_pct',100,'self','fast-reload'));c['owners'].append(0)
    for label,sequence in [('tap-mode',[]),('tap-mode-cover',[cover(.2,.1)])]:
        c=add(label,sequence);c['controls'][0]['click']=[dict(mode='tap',window='always',priority=20,rate=10)]
    c=add('base-min-cycle-not-inherited',[],post_fire_delay=0)
    c['weapon_metadata'].update(input_type='DOWN_Charge',fire_rate=2)
    for w in c['combat']['weapons']:
        if w.get('mode')=='charge':w['min_cycle']=.5
    c=add('blocked-cover-keeps-hold',[hold(until=.5),cover()])
    c['effects'].append(field('cover_disabled',1,'self','no-cover'));c['owners'].append(0)
    for c in rows:
        if c['weapon_metadata'].get('input_type')=='UP':
            for w in c['combat']['weapons']:
                if w.get('mode')=='charge':w['min_cycle']=0
    return rows
