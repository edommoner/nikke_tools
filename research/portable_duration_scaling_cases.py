"""Authored native duration-reference stimuli; no portable packing."""
import copy,importlib.util
from pathlib import Path
from portable_ammo_equivalent_cases import fixtures as ammo_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field

REF='duration-reference'
def carrier(count=3,**changes):
    e=field('crit_rate',0,'self',REF,max_stack=128,**changes);e['trigger']['timing']*=count;return e
def gauge(value):
    e=instant('gauge_charge',value,'self','duration-gauge','battle_start');e.update(gauge_id=REF,gauge_max=100);return e

def synthetic_fixtures():
    seed=copy.deepcopy(ammo_fixtures()[0]);seed.pop('contract');seed['effects']=seed['effects'][:1];seed['owners']=[0];rows=[]
    def add(label,counts=(3,3,3),before=None,changes=None):
        c=copy.deepcopy(seed);e=field('atk_pct',10,'self','duration-scaled','on_attack',duration=.05,max_stack=128)
        e.update(duration_scaling='stack_count',duration_scaling_ref=REF);e.update(changes or {})
        c['effects'] += [carrier() if before is None else before,e];c['owners'] += [0,0]
        c.update(name='duration-scaling-'+label,contract=dict(reference_values=list(counts)));rows.append(c);return c
    add('three')
    add('one',(1,1,1),before=carrier(1))
    add('missing',(None,None,None),before=field('crit_rate',0,'self','other-reference'))
    add('empty-reference',(None,None,None),changes=dict(duration_scaling_ref=''))
    add('zero-duration',changes=dict(duration=0))
    add('negative-finite-duration',changes=dict(duration=-2))
    add('infinite-sentinel',(),changes=dict(duration=-1))
    add('infinite-absent',(),changes=dict(duration=None))
    add('fractional-duration',changes=dict(duration=.125))
    add('gauge-zero',(0,0,0),before=gauge(0))
    add('gauge-fraction',(2,2,2),before=gauge(2.9))
    c=add('zero-gauge-shadows-stack',(0,0,0));c['effects'].insert(2,gauge(0));c['owners'].insert(2,0)
    c=add('last-owner');c['owners']=[4]*len(c['effects']);c['combat']['weapons'][0],c['combat']['weapons'][4]=c['combat']['weapons'][4],c['combat']['weapons'][0]
    c=add('caster-local',(None,None,None));c['owners'][-1]=4;c['combat']['weapons'][0],c['combat']['weapons'][4]=c['combat']['weapons'][4],c['combat']['weapons'][0]
    c=add('growing-before',(1,2,3),before=carrier(1,timing='on_attack'))
    c=add('growing-after',(None,1,2),before=carrier(1,timing='on_attack'));c['effects'][-2:]=c['effects'][-2:][::-1]
    c=add('ref-expired',(3,None,None),before=carrier(duration=.05))
    c=add('self-reference-before-increment',(None,1,2),changes=dict(name=REF,duration=.5));c['effects']=c['effects'][:1]+c['effects'][-1:];c['owners']=[0,0];c['effects'][-1]['trigger']['timing']=['battle_start']*3
    add('value-scaling-independent',changes=dict(scaling='stack_count',scaling_ref='unrelated-value-reference'))
    c=add('level-duration');c['effects'][-1].pop('duration');c['effects'][-1]['duration_values']={'1':.01,'10':.125}
    add('explicit-duration-precedes-level',changes=dict(duration_values={'10':9}))
    c=add('two-independent-definitions');e=copy.deepcopy(c['effects'][-1]);e.update(name='duration-scaled-other',duration=.125);c['effects'].append(e);c['owners'].append(0);c['contract']['reference_values']=[3]*6
    c=add('same-name-alias-source-duration');e=copy.deepcopy(c['effects'][-1]);e.update(duration=.125);c['effects'].append(e);c['owners'].append(0);c['contract']['reference_values']=[3]*6
    c=add('same-name-alias-distinct-reference');e=copy.deepcopy(c['effects'][-1]);e.update(duration_scaling_ref='other-reference',duration=.125)
    c['effects'].insert(2,field('crit_rate',0,'self','other-reference'));c['owners'].insert(2,0);c['effects'].append(e);c['owners'].append(0);c['contract']['reference_values']=[3,1]*3
    add('stealth',changes=dict(stat='stealth',fixed_value=1,polarity='beneficial'))
    c=add('stun',counts=(3,3),changes=dict(stat='stun',fixed_value=1,polarity='harmful'))
    c=add('allied-target',changes=dict(target='all_allies'))
    return rows

def real_fixtures():
    s=importlib.util.spec_from_file_location('duration_real_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    name='레이블'
    rows=[]
    for t in (3,30):
        for attacked in (False,True):
            body=dict(m.body_for(m.policy.roster_for(name),t),burst_gauge_mode='accumulate')
            if attacked:body['enemy']['patterns']=[dict(id='break-shield',kind='attack',delay=1,spec=dict(atk=1600000,coeff=100,target='slot:1',ignore_taunt=True))]
            rows.append(dict(name='duration-scaling-real/'+name+'/'+str(t)+'s'+('/shield-break' if attacked else '/baseline'),body=body,contract=dict(reference_values=[1,1] if attacked else [])))
    return rows

def fixtures():return synthetic_fixtures()+real_fixtures()
