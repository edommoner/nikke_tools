"""Autonomous boss shot scheduling and same-frame target reaction ordering."""
import hashlib,importlib.util,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('incoming_lifecycle',ROOT/'scripts/verify-incoming-detail.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)

def fixtures():
 for delay in (0,.1):
  b=v.body(2);b['enemy']['patterns']=[dict(id='cycle',kind='attack',delay=delay,until={'time':.2},after=['start','cycle'],repeat=0,spec=dict(coeff=100,atk=1,target='random:2',hits=4,interval=.07))]
  yield 'repeat-close-reopen-delay-'+str(delay),b,{}
 b=v.body(2);first={**v.attack('slot:4',hits=3,interval=.5),'id':'first'};second={**v.attack('random:1',hits=3,interval=.5),'id':'second'};b['enemy']['patterns']=[first,second]
 yield 'same-frame-cloak-changes-second-shot-pool',b,{v.NAMES[3]:[v.B('reactive cloak','stealth',event='received_hit',duration=.2)]}
 b=v.body(2);first={**v.attack('slot:1',hits=3,interval=.5),'id':'first'};second={**v.attack('slot:4',hits=3,interval=.5),'id':'second'};b['enemy']['patterns']=[first,second]
 yield 'same-frame-hidden-taunt-steals-second-slot-shot',b,{v.NAMES[0]:[v.B('reactive taunt','taunt',event='received_hit',duration=.2),v.B('reactive cloak','stealth',event='received_hit',duration=.2)]}
