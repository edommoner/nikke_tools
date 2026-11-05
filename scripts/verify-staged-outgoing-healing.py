"""v39 body-healing source/recipient and complete squad oracle verification."""
import argparse,copy,hashlib,importlib.util,json,sys
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
g=load('outgoing_stage_runtime','scripts/staged-outgoing-healing-runtime.py').install()
v=load('outgoing_survival_oracle','scripts/verify-survival-scaling.py');N=v.N;B=v.B;E=v.E;BuffManager=v.BuffManager

def fixtures():
    cases=['source-only','recipient-is-not-source','separate-layers','additive-sources','negative-source','negative-recipient','stacked-source','periodic','caster-max','duplicates','expired','lazy-target','conditional','lifesteal','lifesteal-negative','cover-unaffected','shield-unaffected','decoy-unaffected','registered-timer-source-down']
    for case in cases:
        b=v.body(1.2);extra={n:[] for n in N};source=N[1];recipient=N[0]
        extra[N[4]].append(B('room for body healing','max_hp_only_pct',100,'all_allies'))
        outgoing=B('source outgoing bonus','outgoing_heal_pct',50)
        if case=='recipient-is-not-source':outgoing['target']=recipient
        if case in ('negative-source','lifesteal-negative'):outgoing['fixed_value']=-150;outgoing.pop('values',None)
        if case=='additive-sources':extra[source].append(B('second source bonus','outgoing_heal_pct',25))
        if case=='stacked-source':outgoing.update(max_stack=3);outgoing['trigger']['timing']=['every:0.05s']
        if case=='expired':outgoing['duration']=.1
        if case=='lazy-target':outgoing['target']='allies_lowest_hp:2'
        if case=='conditional':outgoing['trigger']['condition']=['self_hp_below:80'];outgoing['trigger']['timing']=['passive']
        extra[source].append(outgoing)
        if case in ('separate-layers','negative-recipient'):extra[recipient].append(B('recipient incoming bonus','heal_received_pct',-150 if case=='negative-recipient' else 25))
        kw=dict(event='every:0.3s',max_trigger=1)
        if case=='periodic':kw=dict(tick_interval=.2,duration=1)
        if case=='caster-max':kw['scaling']='max_hp'
        target=[recipient,'all_allies',recipient] if case=='duplicates' else recipient
        if case.startswith('lifesteal'):
            extra[source].append(B('attack lifesteal','lifesteal_pct',1))
        elif case.endswith('-unaffected'):
            stat=case.split('-')[0];heal_stat=stat+'_heal_pct'
            if stat!='cover':extra[recipient].append(B('repair carrier','decoy' if stat=='decoy' else 'shield_from_max_hp_pct',10))
            extra[source].append(E('repair','instant',heal_stat,5,recipient,**kw))
        else:extra[source].append(E('body healing','instant','heal_hp_pct',2,target,**kw))
        if case=='registered-timer-source-down':
            extra[source][-1]=E('body healing timer','instant','heal_hp_pct',2,recipient,tick_interval=.3,duration=1)
            b['enemy']['patterns']=[v.s.lethal('slot:2',at=.15)]
        yield 'outgoing-'+case,b,extra

def real_fixtures(include_unsupported=False):
    for character in (('프리카','소라','백학','미사토') if include_unsupported else ('프리카','백학')):
        for case in ('incoming','owned-healing-cube'):
            names=[character,N[0],N[1],N[2],N[3]]
            # Each actual B1/B2 healer uses the other required burst-stage slot.
            names=list(dict.fromkeys(names));assert len(names)==5
            b=v.body(30,True,names);b['burst_gauge_mode']='accumulate'
            b['enemy']['patterns']=[dict(id='actual healing damage',kind='attack',delay=.2,until={'time':30},spec=dict(coeff=100,atk=100000,target='all',hits=50,interval=.5,pierce=True))]
            if case=='owned-healing-cube':
                p=b['profile']['chars'][character];p.update(skill_levels={'1':7,'2':5,'3':9},core_enhancement=2,breakthrough=3,affinity=20,collection_stage='SR15',cube={'name':'렐릭 힐링 큐브','level':4})
                b['stat_deltas']={character:{'atk':12000,'hp':100000,'def':250}}
            yield 'raw-outgoing-'+character+'-'+case,b,{}
