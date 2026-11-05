"""Authored manual-action worlds; the input producer never simulates a battle."""
import copy
from portable_coordinate_sampled_vital_cases import fixtures as vital
from world_enemy_attack_cases import field

def fixtures():
    rows=[];base=vital()[0]
    def add(label,sequence,*,mode=False):
        c=copy.deepcopy(base);c.update(name='coordinate-manual/'+label,manual_controls=True,duration=.8,seed=231+len(rows))
        if not mode:c['effects'].pop();c['owners'].pop()
        c['controls'][0]={'sequence':copy.deepcopy(sequence)}
        c['effects'].append(field('atk_pct',1,'self','cover-notice','event:cover',max_stack=10));c['owners'].append(0)
        rows.append(c);return c
    def cover(t=0,duration=.2):return dict(action='cover',t=t,duration=duration)
    add('timed-full',[cover()])
    add('zero-at-zero',[cover(duration=0)])
    add('zero-later',[cover(.2,0)])
    add('until-reload-full',[cover(duration=None)])
    add('cancel-loaded',[cover(.2,.1)])
    c=add('cancel-empty',[cover(.2,.1)]);c['combat']['weapons'][0]['capacity']=2
    c=add('until-reload-empty',[cover(.2,None)]);c['combat']['weapons'][0]['capacity']=2
    c=add('charge-cancel',[cover(.2,.2)]);c['combat']['weapons'][0].update(mode='charge',charge=.1,interval=.2,min_cycle=.2,full_charge_mult=100)
    add('same-frame-replace',[cover(0,.1),cover(0,.4)])
    add('reentry',[cover(0,.2),cover(.4,.2)])
    add('sorted-sequence',[cover(.4,.1),cover(0,.1)])
    add('mode-auto',[cover(.1,.2)],mode=True)
    c=add('mode-charge',[cover(.1,.2)],mode=True);c['effects'][-2].update(charge=True,charge_time=.1,weapon_type='SR')
    c=add('entry-reload',[cover(.1,.2)],mode=True);c['effects'][-2].update(entry_reload=True,reload_time=.2)
    c=add('disabled-entry',[cover(0,.2)]);c['effects'].append(field('cover_disabled',1,'self','disabled'));c['owners'].append(0)
    c=add('disabled-during',[cover(0,.6)]);c['effects'].append(field('cover_disabled',1,'self','disabled','every:0.2s'));c['owners'].append(0)
    c=add('incoming-cover',[cover(0,.4)]);c['patterns'].append(dict(id='cover-hit',kind='attack',delay=.2,spec=dict(atk=500,coeff=100,target='slot:1',ignore_taunt=True)))
    c=add('camera-preempt',[cover(0,.6)]);c['controls'][1]={'sequence':[cover(.2,.2)]}
    c=add('hold-then-cover',[dict(action='hold',t=0,until=.5),cover(.2,.2)]);c['weapon_metadata']['input_type']='UP';c['combat']['weapons'][0].update(mode='charge',charge=.1,interval=.2,min_cycle=.2,full_charge_mult=100)
    add('eight-actions',[cover(i*.1,.04) for i in range(8)])
    for label,value in [('clip-cancel',.1),('clip-until-reload',None)]:
        c=add(label,[cover(.16,value)]);c['duration']=1.;c['weapon_metadata']['clip_count']=3;c['combat']['weapons'][0].update(capacity=3,interval=.05,reload=.2,clip_count=3)
    c=add('cover-then-hold',[cover(0,.2),dict(action='hold',t=.1,until=1.5)]);c['weapon_metadata']['input_type']='UP';c['combat']['weapons'][0].update(mode='charge',charge=.1,interval=.2,min_cycle=.2,full_charge_mult=100)
    for label,timing in [('mode-charge-visibility','on_attack'),('mode-charge-cover-visibility','every:0.05s')]:
        c=copy.deepcopy(next(c for c in rows if c['name'].endswith('/mode-charge')));c.update(name='coordinate-manual/'+label,seed=231+len(rows));c['effects'].append(field('atk_pct',10,'self','charge-visible',timing,condition=['during_charge'],max_stack=10));c['owners'].append(0);rows.append(c)
    for c in rows:
        if c['weapon_metadata'].get('input_type')=='UP':
            for w in c['combat']['weapons']:
                if w.get('mode')=='charge':w['min_cycle']=0
    return rows
