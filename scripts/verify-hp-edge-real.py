"""Full actual A2 squads: mode drain/exit, healing, incoming and owned growth."""
import argparse,copy,hashlib,importlib.util,json
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('hp_real_verifier',ROOT/'scripts/verify-hp-edge.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
g=v.g;s=v.s;N=v.N;B=v.B;E=v.E

def fixtures():
    for variant in ('dry-fixed','regular-heal','incoming','start-low','accumulate','mixed-growth','rapunzel-heal','rapunzel-revive'):
        names=[N[0],N[1],'A2',N[3],N[4]]
        if variant.startswith('rapunzel-'):names=['라푼젤',N[0],N[1],'A2',N[3]]
        b=s.v.body(60,True,names);b.update(burst_gauge_mode='fixed',_debug_hp_events=True)
        b['enemy']['patterns']=[s.lethal(at=100)];extra={n:[] for n in names}
        if variant=='regular-heal':extra[names[0]].append(E('periodic support','instant','heal_hp_pct',100,'all_allies',event='every:10s'))
        if variant=='incoming':
            b['enemy']['patterns']=[dict(id='damage',kind='attack',delay=2,until={'time':30},spec=dict(coeff=100,atk=500000,target='slot:3',hits=10,interval=2,pierce=True))]
            extra[names[0]].append(B('survival test support','undying',1,'all_allies'))
        if variant=='start-low':extra['A2'].append(E('test initial HP','instant','current_hp_reduce',75,event='battle_start'))
        if variant=='accumulate':b['burst_gauge_mode']='accumulate';b['seed']=7654321
        if variant=='mixed-growth':
            for i,n in enumerate(names):
                c=b['profile']['chars'][n];c.update(skill_levels={'1':3+i,'2':9-i,'3':10-i},affinity=1+6*i,core_enhancement=i,breakthrough=3)
                c['equip_skills']['atk_pct']=1+i
            b['stat_deltas']={'A2':{'atk':12000,'hp':100000,'def':250}}
        if variant=='rapunzel-revive':b['enemy']['patterns']=[s.lethal('slot:4',at=2.8)]
        yield 'raw-A2-'+variant,b,extra
    for character,variant in [('솔린 : 프로스트 티켓','counted-crossings'),('플로라','center'),('플로라','left'),('플로라','right')]:
        names=[N[0],N[1],character,N[3],N[4]]
        if variant=='left':names=[character,N[0],N[1],N[3],N[4]]
        if variant=='right':names=[N[0],N[1],N[3],N[4],character]
        b=s.v.body(30,True,names);b.update(burst_gauge_mode='fixed',_debug_hp_events=True);b['enemy']['patterns']=[s.lethal(at=100)]
        extra={n:[] for n in names}
        extra[names[0]]+=[E('controlled decrease','instant','current_hp_reduce',95 if variant=='counted-crossings' else 50,'all_allies',event='every:3s',max_trigger=3),E('controlled recovery','instant','heal_hp_pct',100,'all_allies',event='every:4s',max_trigger=3)]
        yield 'raw-'+character+'-'+variant,b,extra
