"""Authored controls/effects; GPU derives cast times, waits and predictions."""
import copy,math
from portable_coordinate_policy_cases import fixtures as policies
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field
from world_frame_native import roster_names

def fixtures():
    base=policies()[0];rows=[]
    def add(label,duration=4.):
        c=copy.deepcopy(base);c.update(name='coordinate-burst-control/'+label,burst_controls=True,squad_controls=True,squad_mode_state=True,sequence=[],duration=duration,seed=901+len(rows));c['controls']=[{} for _ in range(5)]
        c['combat']['weapons'][3]['stage']=1;c['combat']['weapons'][4]['stage']=3
        # Same canonical static cooldown; shared buffs shorten actual ready times.
        for who,cd in enumerate([17,19,39,39,19]):
            c['effects'].append(field('burst_cooldown',cd,'self','control-cd-'+str(who)));c['owners'].append(who)
        next(e for e in c['effects'] if e['name']=='initial')['trigger']['timing'].append('every:2s')
        rows.append(c);return c
    add('default')
    c=add('delay-first');c['controls'][0]={'burst':{'delay':.3,'pattern':[1,2]}}
    c=add('delay-from-late-ready');c['controls'][0]={'burst':{'delay':.2,'wait_own_cooldown':3.,'pattern':[1,2]}}
    c=add('delay-ready-stage2');c['controls'][1]={'burst':{'delay':.4}}
    c=add('delay-ready-stage3');c['controls'][2]={'burst':{'delay':.4}}
    c=add('wait-for-owner');c['controls'][0]={'burst':{'wait_own_cooldown':1.5,'pattern':[1,2]}}
    c=add('wait-fallback-outside-range');c['controls'][0]={'burst':{'wait_own_cooldown':.5,'pattern':[1,2]}}
    c=add('wait-disabled');c['controls'][0]={'burst':{'wait_own_cooldown':False,'pattern':[1,2]}}
    c=add('empty-pattern');c['controls'][0]={'burst':{'pattern':[]}}
    c=add('pattern-cycles');c['controls'][0]={'burst':{'pattern':[1]}};c['controls'][3]={'burst':{'pattern':[2]}}
    c=add('resolved-every');c['burst_config']={'burst_pattern':{roster_names(c)[0]:'every:2'}}
    c=add('resolved-null');c['burst_config']={'burst_pattern':{roster_names(c)[0]:None}}
    c=add('explicit-order');n=roster_names(c);c['burst_config']={'burst_sequence':[{'1':[n[3],n[0]],'2':[n[1]],'3':[n[4],n[2]]}]};c['controls'][0]={'burst':{'pattern':[1]}}
    c=add('explicit-missing-stage');n=roster_names(c);c['burst_config']={'burst_sequence':[{'1':[n[0]],'3':[n[2]]}]}
    c=add('explicit-empty-cycle');c['burst_config']={'burst_sequence':[{}]}
    c=add('explicit-expired');n=roster_names(c);c['burst_config']={'burst_sequence':[{'1':[n[0]],'2':[n[1]],'3':[n[2]]}]}
    c=add('explicit-stage');c['combat']['weapons'][3]['explicit_burst_stage']=True
    c=add('A-stage');c['combat']['weapons'][0]['stage']=4;c['burst_config']={'burst_pattern':{roster_names(c)[0]:[]}}
    for label,where in [('stun-first',0),('stun-alternative',3)]:
        c=add(label);c['controls'][0]={'burst':{'pattern':[1,2],'wait_own_cooldown':3.}};c['effects'].append(field('stun',1,'self','control-stun',duration=.8));c['owners'].append(where)
    c=add('down-first');c['controls'][0]={'burst':{'pattern':[1,2],'wait_own_cooldown':3.}};c['patterns'].append(dict(id='control-lethal',kind='attack',delay=1.8,spec=dict(atk=1e8,coeff=100,target='slot:1',ignore_taunt=True,pierce=True)))
    for label,when in [('reduce-cooldown-wait',2.3),('reduce-delay-wait',3.1)]:
        c=add(label);c['controls'][0]={'burst':{'delay':.2,'wait_own_cooldown':3.,'pattern':[1,2]}};c['effects'].append(dict(instant('burst_cooldown_reduce',1,'self','control-reduce','every:'+str(when)+'s'),max_trigger=1));c['owners'].append(0)
    c=add('reentry');c['effects'] += [instant('burst_reentry',1,'self','control-reenter','burst_cast'),instant('burst_cooldown_reduce',100,'self','reenter-ready','burst_cast')];c['owners'] += [0,0];c['controls'][0]={'burst':{'delay':.1}}
    c=add('reload-into-next-fb');c['controls'][0]={'burst':{'delay':.3,'wait_own_cooldown':3.,'pattern':[1,2]},'reload':{'policy':'into_fb','margin':.1}}
    c=add('cover-and-squad');c['controls'][0]={'burst':{'delay':.2},'cover':{'policy':'own_full_burst'}};c['sequence']=[dict(t=.8,action='cover_all',duration=.2)]
    c=add('full-end-stage-override');c['effects'].append(field('burst_stage_override:2',1,'self','end-stage',timing='full_burst_end',duration=.3));c['owners'].append(3)
    for label,delay in [('delay-neighbor-below',math.nextafter(.3,0)),('delay-neighbor-above',math.nextafter(.3,math.inf))]:
        c=add(label);c['controls'][0]={'burst':{'delay':delay}}
    for label,pierce,prior in [('cover-down-all',True,False),('cover-break-only-all',False,False),('cover-down-after-prior',True,True),('cover-down-last',True,False)]:
        c=add(label,duration=2.5)
        if label=='cover-down-last':c['controls'][4]['sequence']=[dict(t=1.5,action='cover',duration=1.)]
        else:c['sequence']=[dict(t=1.5,action='cover_all',duration=1.)]
        if prior:c['patterns'].append(dict(id='prior-lethal',kind='attack',delay=1.6,spec=dict(atk=1e8,coeff=100,target='slot:5',ignore_taunt=True,pierce=True)))
        c['patterns'].append(dict(id='all-covers',kind='attack',delay=1.8,spec=dict(atk=1e8 if pierce else 2000,coeff=100,target='all',pierce=pierce)))
    return rows
