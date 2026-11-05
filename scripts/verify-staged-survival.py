"""Whole-squad staged GPU down/revive parity against the explicit CPU bridge.

No CPU trace is used as GPU input. The normal v33 application is untouched.
HP-edge trigger definitions are separately rejected until their own GPU port.
"""
import argparse,copy,hashlib,importlib.util,json,random,sys,ast,inspect,textwrap
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
loader=load('survival_staging_loader','scripts/staged-survival-runtime.py');g=loader.install()
v=load('survival_incoming_oracle','scripts/verify-incoming-detail.py')
from calculator import timeline
from calculator.timeline import CharState
from calculator.buff_manager import BuffManager
N=v.NAMES;B=v.B;E=v.E

def lethal(target='slot:1',at=.1,hits=1,interval=.3):return dict(id='lethal',kind='attack',delay=at,until={'time':.7},spec=dict(coeff=100,atk=100000000,target=target,hits=hits,interval=interval,pierce=True))

def fixtures(quick=False):
 for case in ('down','revive','preserve-marker','restore-passive-not-periodic','shared-passive-no-double-stack','once-only-revive','whole-squad-hit-order'):
  b=v.body(1);b['enemy']['patterns']=[lethal('all' if case=='whole-squad-hit-order' else 'slot:1',hits=2 if case=='once-only-revive' else 1)]
  extra={N[0]:[B('own permanent','atk_pct',10),B('shared permanent','atk_pct',10,'all_allies',max_stack=3)],N[1]:[]}
  if case!='down':extra[N[1]].append(E('revive ally','instant','revive',50,'allies_down_top_atk_excl:1',event='event:ally_down',max_trigger=1))
  if case=='preserve-marker':extra[N[0]].append(B('preserved','atk_pct',7,persist_on_revive=True))
  if case=='restore-passive-not-periodic':extra[N[0]]+=[B('passive hp','max_hp_pct',25),B('periodic permanent','atk_pct',5,event='every:0.03s')]
  yield case,b,extra
 for case in ('registered-dot','registered-heal','new-every-trigger','normal-shots-stop','global-ammo-counter','personal-attack-counter','persisted-dot-power'):
  b=v.body(2);b['enemy']['patterns']=[lethal(at=.35)];extra={N[0]:[],N[1]:[]}
  if case in ('registered-dot','persisted-dot-power'):extra[N[0]]=[E('observed dot','damage','dot_damage',100,'target',tick_interval=.2,duration=1)]
  if case=='persisted-dot-power':extra[N[0]].append(B('preserved power','atk_pct',77,persist_on_revive=True))
  if case=='registered-heal':extra[N[0]]=[B('room for healing','max_hp_only_pct',100,'all_allies'),E('observed heal','instant','heal_hp_pct',1,'all_allies',tick_interval=.2,duration=1)]
  if case=='new-every-trigger':extra[N[0]]=[B('observed every','atk_pct',5,'all_allies',event='every:0.2s',duration=.4)]
  if case.endswith('counter'):
   extra[N[0]]=[B('observed counter','atk_pct',1,'all_allies',event='squad_ammo_consume:10' if case.startswith('global') else 'on_attack_count:10',max_stack=100)]
   extra[N[1]]=[E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:0.8s',max_trigger=1)]
  if quick and case not in ('registered-dot','global-ammo-counter','persisted-dot-power'):continue
  yield case,b,extra
 if quick:return
 for character in ('모더니아','맥스웰'):
  for restore in (False,True):
   names=[N[0],N[1],character,N[3],N[4]];b=v.body(8,True,names);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[lethal('slot:3',3.8)]
   extra={names[-1]:[E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:5.5s',max_trigger=1)]} if restore else {}
   yield 'raw-mode-'+character+'-'+str(restore),b,extra
 for character in ('앨리스','솔린','크라운'):
  names=[character]+[n for n in N if n!=character][:4];b=v.body(4,True,names);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[lethal(at=.35)]
  yield 'raw-hp-passive-'+character,b,{names[-1]:[E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:0.8s',max_trigger=1)]}
 for pct in (50,100):
  b=v.body(1);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[lethal(at=.35)]
  yield 'hp-predicate-'+str(pct),b,{N[0]:[B('larger maximum','max_hp_pct',25),B('healthy','atk_pct',50,event='passive',condition=['self_hp_above:80'])],N[1]:[E('late revive','instant','revive',pct,'allies_down_top_atk_excl:1',event='every:0.8s',max_trigger=1)]}
 for rule in ('all','slot:1','slot:2,4','random:2','top_atk:2'):
  b=v.body(2);b['enemy']['patterns']=[lethal(),dict(id='selection',kind='attack',delay=.2,until={'time':1.6},spec=dict(coeff=100,atk=1,target=rule,hits=7,interval=.2))]
  yield 'targets-after-down-'+rule,b,{}
 b=v.body(1);b['enemy']['patterns']=[lethal(at=.1),{**lethal('slot:5',.2),'id':'other-down'}]
 role=v.v.a.META[N[0]]['class']
 yield 'revive-class-random',b,{N[1]:[E('class revive','instant','revive',50,'allies_down_class_random:'+role+':1',event='every:0.8s',max_trigger=1)]}
 names=[N[0],N[1],N[2],N[3],'맥스웰'];b=v.body(8,False,names);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[lethal(at=2.8)]
 yield 'waiting-burst-resumes-after-only-b1-revives',b,{N[1]:[E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:5.5s',max_trigger=1)]}
 b=v.body(4);b['enemy']['patterns']=[lethal()]
 yield 'count-limited-class-does-not-refill',b,{N[1]:[B('support power','atk_pct',100,'allies_class:'+role+':1',event='every:0.6s')]}
 b=v.body(4);b['enemy']['patterns']=[lethal(at=100)]
 yield 'count-limited-class-first-alive',b,{N[1]:[B('support power','atk_pct',100,'allies_class:'+role+':1',event='every:0.6s')]}
 charged=[n for n in N if (v.v.a.META[n].get('charge_time') or 0)>0];charged.sort(key=lambda n:-v.v.a.META[n]['charge_time']);assert len(charged)>=2
 b=v.body(4);b['enemy']['patterns']=[lethal('slot:'+str(N.index(charged[0])+1))]
 yield 'charge-prefix-does-not-refill',b,{N[1]:[B('charge prefix power','atk_pct',100,'allies_top_base_charge_time:1',event='every:0.6s')]}
 names=[N[0],N[1],'라푼젤','라플라스',N[2]];b=v.body(4,False,names);b['enemy']['patterns']=[lethal('slot:3')]
 code=v.v.a.META[names[2]]['element_code'];weapon=v.v.a.META[names[2]]['weapon_type'];assert (code,weapon)==(v.v.a.META[names[3]]['element_code'],v.v.a.META[names[3]]['weapon_type'])
 yield 'leftmost-living-refills',b,{N[1]:[B('leftmost living power','atk_pct',100,'allies_code_weapon_leftmost:'+code+':'+weapon+':1',event='every:0.6s')]}
 for restore in (False,True):
  b=v.body(8);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[lethal(at=2.8)]
  extra={N[1]:[E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:5.5s',max_trigger=1)]} if restore else {}
  yield 'dead-first-b1-keeps-backup-priority-'+str(restore),b,extra
 b=v.body(8);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[lethal('slot:2',2.8)]
 yield 'dead-b2-waits-for-revival',b,{N[4]:[E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:5.5s',max_trigger=1)]}
 for predicate in ('has_burst1_ally','no_burst1_ally'):
  for restore in (False,True):
   names=[*N[:4],'맥스웰'];b=v.body(4,False,names);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[lethal(at=.1)]
   extra={names[1]:[B('B1 predicate power','atk_pct',100,'all_allies',event='every:0.3s',condition=[predicate])]}
   if restore:extra[names[2]]=[E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:2.0s',max_trigger=1)]
   yield 'dead-b1-ally-'+predicate+'-'+str(restore),b,extra
 for character in ('디젤 : 윈터 스위츠','앤 : 미라클 페어리','라푼젤','마나'):
  names=[character]+[n for n in N if n!=character][:4]
  for attacked in (False,True):
   b=v.body(30,True,names);b['burst_gauge_mode']='fixed';target='slot:1' if character.startswith('디젤') else 'slot:5'
   b['enemy']['patterns']=[lethal(target,2.8 if attacked else 100)]
   yield 'raw-new-'+character+('-death' if attacked else '-no-shot'),b,{}
