"""Independent v38 whole-squad and per-name decoy-frame parity."""
import argparse,ast,copy,hashlib,importlib.util,inspect,json,sys,textwrap
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
g=load('decoy_stage_runtime','scripts/staged-decoy-healing-runtime.py').install()
v=load('decoy_independent_survival_oracle','scripts/verify-survival-scaling.py');N=v.N;B=v.B;E=v.E;BuffManager=v.BuffManager
from calculator.buff_manager import _DECOY_STATS

def attack(at=.1,atk=100000,target='slot:1',hits=2,interval=.4,pierce=True):
    return dict(id='decoy hit '+str(at),kind='attack',delay=at,until={'time':1.2},spec=dict(coeff=100,atk=atk,target=target,hits=hits,interval=interval,pierce=pierce))
def fixtures():
    variants=['absent','full','partial','caster-max','overheal','negative','zero','consumed','expired','periodic','caster-max-changes','ordered-duplicates','shared-empty','newer-layers','equal-time','cover-gates','shield-gates','received-heal-modifier','stack-reference','timer-source-down','owner-revives']
    for case in variants:
        b=v.body(1.2);b['_debug_decoy_frames']=True;extra={n:[] for n in N};recipient=N[0];healer=N[1];target=recipient;value=1;kw=dict(event='every:0.3s',max_trigger=1)
        d=B('decoy older','decoy',100)
        if case in ('ordered-duplicates','shared-empty','equal-time'):d['target']='all_allies'
        if case=='expired':d['duration']=.2
        if case!='absent':extra[N[0]].append(d)
        if case not in ('absent','full'):b['enemy']['patterns']=[attack()]
        if case in ('caster-max','caster-max-changes','timer-source-down'):kw['scaling']='max_hp'
        if case=='overheal':value=500
        if case=='negative':value=-1
        if case=='zero':value=0;target='allies_random:2'
        if case=='consumed':b['enemy']['patterns']=[attack(atk=100000000)]
        if case=='periodic':kw=dict(tick_interval=.2,duration=1)
        if case=='caster-max-changes':
            kw.update(event='every:0.3s',max_trigger=3);extra[healer].append(B('healer maximum','max_hp_pct',100,event='every:0.4s',max_trigger=1))
        if case=='ordered-duplicates':target=[recipient,'all_allies',recipient];b['enemy']['patterns']=[attack(target='all',atk=300000)];value=5
        if case=='shared-empty':b['enemy']['patterns']=[attack(atk=100000000,hits=1)];value=5
        if case=='newer-layers':
            extra[N[0]].append(B('decoy newer','decoy',100,event='every:0.05s',max_trigger=1))
            b['enemy']['patterns']=[attack(at=.01,hits=1),attack(at=.1,hits=2)]
        if case=='equal-time':
            extra[N[0]].append(B('decoy newer','decoy',100,'all_allies'))
            b['enemy']['patterns']=[attack(at=.1,atk=100000000,hits=1),attack(at=.2,hits=2)]
        if case=='cover-gates':
            extra[N[0]]+=[E('cover','instant','force_reload',0),B('leave cover','cover_disabled',1,event='every:0.4s',max_trigger=1)]
            b['enemy']['patterns']=[attack(pierce=False)];kw['max_trigger']=3
        if case=='shield-gates':
            extra[N[0]].append(B('temporary shield','shield_from_max_hp_pct',100,duration=.4))
            b['enemy']['patterns']=[attack(pierce=False)];kw['max_trigger']=3
        if case=='received-heal-modifier':extra[N[0]].append(B('body healing power','heal_received_pct',100))
        if case=='stack-reference':extra[healer].append(B('repair gauge','',event='every:0.05s',max_stack=3));kw.update(scaling='stack_count',scaling_ref='repair gauge')
        if case=='timer-source-down':kw=dict(tick_interval=.2,duration=1,scaling='max_hp');b['enemy']['patterns'].append(v.s.lethal('slot:2',at=.15))
        if case=='owner-revives':
            b['enemy']['patterns']=[attack(at=.1,atk=100000000,hits=2,interval=.1),attack(at=.5,hits=1)]
            extra[N[2]].append(E('revive owner','instant','revive',50,'allies_down_top_atk_excl:1',event='event:ally_down',max_trigger=1));kw['max_trigger']=3
            extra[N[0]].append(B('post-revival decoy','decoy',100,event='every:0.4s',max_trigger=1))
        extra[healer].append(E('repair decoy','instant','decoy_heal_pct',value,target,**kw))
        for label,event in [('body','event:heal_received'),('cover','event:cover_healed'),('shield','event:shield_applied')]:extra[N[2]].append(B(label+' notification witness','atk_pct',11,event=event,max_stack=100))
        yield 'decoy-heal-'+case,b,extra

def real_fixtures():
    for case in ('no-shots','incoming','accumulate','owned-growth','reordered','revival','dead-first-B1'):
        names=['라이',N[0],N[1],N[3],N[2]] if case!='revival' else ['라푼젤',N[0],N[1],'라이',N[3]]
        b=v.body(30,True,names);b['_debug_decoy_frames']=True;extra={n:[] for n in names};b['burst_gauge_mode']='accumulate' if case=='accumulate' else 'fixed'
        if case=='dead-first-B1':
            names=['라이','라푼젤',N[1],N[3],N[2]];b=v.body(30,True,names);b['_debug_decoy_frames']=True;b['burst_gauge_mode']='fixed';extra={n:[] for n in names}
        if case not in ('no-shots','revival'):b['enemy']['patterns']=[dict(id='Rei incoming',kind='attack',delay=.1,until={'time':30},spec=dict(coeff=100,atk=20000,target='slot:1',hits=35,interval=.8,pierce=True))]
        if case=='owned-growth':
            c=b['profile']['chars']['라이'];c.update(core_enhancement=2,breakthrough=3,affinity=20,skill_levels={'1':7,'2':5,'3':9},collection_stage='SR15',cube={'name':'렐릭 베어 큐브','level':4});c['equip_skills'].update(atk_pct=[11.11,11.11,12.34],charge_speed_pct=[2.34,2.34,4.3]);b['stat_deltas']={'라이':{'atk':12000,'hp':100000,'def':250}}
        if case=='reordered':b['squad']=list(reversed(b['squad']));b['enemy']['patterns'][0]['spec']['target']='slot:5'
        if case in ('revival','dead-first-B1'):
            slot='slot:4' if case=='revival' else 'slot:1'
            b['enemy']['patterns']=[v.s.lethal(slot,at=2.8,hits=2,interval=.1),dict(id='post-revival hits',kind='attack',delay=4,until={'time':30},spec=dict(coeff=100,atk=20000,target=slot,hits=30,interval=.8,pierce=True))]
        yield 'raw-Rei-decoy-heal-'+case,b,extra
