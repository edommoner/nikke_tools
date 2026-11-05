"""Whole-squad incoming combat oracle; GPU inputs are authored definitions only."""
import argparse,copy,hashlib,importlib.util,json,random,sys,math,ast,inspect,textwrap
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('incoming_oracle',ROOT/'scripts/verify-boss-buffs-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from calculator import timeline
NAMES=v.v.NAMES;E=v.E

def body(duration=4,raw=False,names=None):
 b=v.v.body_for(names or NAMES,duration,raw);b.update(seed=12345,shooting_policy='character',burst_gauge_mode='accumulate',_debug_random_state=True,_debug_boss_random_state=True,_debug_incoming_frames=True)
 for c in b['profile']['chars'].values():c.update(equip_skills={k:0 for k in v.a.spec.DEFAULT_CHAR['equip_skills']},collection_stage='없음',favorite_stage=0,cube={'name':'__none__','level':0})
 return b
def attack(rule='slot:1',atk=1,**kw):return dict(id='incoming',kind='attack',until={'time':4},spec=dict(coeff=100,atk=atk,target=rule,**kw))
def B(name,stat,value=1,target='self',**kw):return E(name,'buff',stat,value,target,**kw)
def context(name,extra):
 return v.v.t.raw.injected_effects(extra) if name.startswith('raw-') else v.v.t.p.custom_effects(extra)

def fixtures(quick=False):
 for rule in ('all','slot:2,4','random:2','top_atk:2'):
  for scenario in ('visible','one_hidden','all_hidden','hidden_taunter','ignore_taunt'):
   if rule=='all' and scenario=='ignore_taunt':continue
   if quick and scenario not in ('hidden_taunter','visible'):continue
   b=body();p=attack(rule,hits=8,interval=.5);extra=[]
   if scenario=='ignore_taunt':p['spec']['ignore_taunt']=True
   if scenario in ('one_hidden','hidden_taunter','ignore_taunt'):extra.append(B('hidden','stealth'))
   if scenario=='all_hidden':extra.append(B('all hidden','stealth',target='all_allies'))
   if scenario in ('hidden_taunter','ignore_taunt'):extra.append(B('taunt','taunt'))
   b['enemy']['patterns']=[p];yield 'targets-'+rule+'-'+scenario,b,{NAMES[0]:extra}
 # Reuse the independent, previously recorded layer fixtures as authored
 # definitions. The old CPU traces/selected targets/damage are never read.
 path=ROOT/'scripts/audit-incoming-damage.py';tree=ast.parse(path.read_text(encoding='utf-8'));nodes=[]
 for node in tree.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='rows' for t in node.targets):break
  nodes.append(node)
 namespace={'__file__':str(path),'__name__':'incoming_layer_definitions'};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)
 for name,atk,pierce,effects,_ in namespace['cases']:
  if name in ('down','literal-legacy-reduction'):continue
  if quick and name not in ('body','shield-and-cover-pierce','decoy','shared','lethal-trigger-undying'):continue
  b=body(1);effects=copy.deepcopy(effects)
  # The lethal transition itself remains fail-closed in this stage. Strong
  # shield/cover/decoy witnesses retain the complete incoming hit using undying.
  if atk>=10000000 and name not in ('undying','lethal-trigger-undying'):effects.append(B('survive layer probe','undying'))
  b['enemy']['patterns']=[dict(id='incoming',kind='attack',delay=.1,until={'time':.2},spec=dict(coeff=100,atk=atk,target='slot:1',pierce=pierce))]
  yield 'layers-'+name,b,{NAMES[0]:effects}
 transitions=[
  ('hidden-expires','random:2',[B('cloak','stealth',duration=.6)]),
  ('all-hidden-fallback','random:2',[B('team cloak','stealth',target='all_allies',duration=.6),B('long cloak','stealth',duration=1.2)]),
  ('periodic-taunt','random:2',[B('cloak','stealth'),B('taunt','taunt',event='every:0.4s',duration=.2)]),
  ('enemy-taunt','top_atk:2',[B('cloak','stealth'),B('taunt','taunt',target='target',duration=.6)]),
  ('group-taunt-first','slot:2,4',[B('taunt','taunt',target='all_allies',duration=.6)]),
  ('recipient-runtime-cloak','random:2',[B('gate','',duration=.6),B('cloak','stealth',condition=['self_state:gate'])]),
  ('lazy-recipient-cloak','random:2',[B('cloak','stealth',target='allies_top_atk:2')]),
  ('atk-ranking-changes','top_atk:2',[B('power','atk_pct',1000,event='every:0.4s',duration=.2)]),
 ]
 for name,rule,effects in transitions:
  if quick and name not in ('all-hidden-fallback','recipient-runtime-cloak'):continue
  b=body(2);b['enemy']['patterns']=[dict(id='incoming',kind='attack',delay=.2,until={'time':1.6},spec=dict(coeff=1,atk=1,target=rule,hits=7,interval=.2))]
  yield 'transitions-'+name,b,{NAMES[0]:effects}
 for gauge in ('fixed','accumulate'):
  b=body(30,True);b['burst_gauge_mode']=gauge
  b['enemy']['patterns']=[attack('random:2',200000,hits=100,interval=.3),dict(id='range',kind='move',delay=2,until={'time':5},distance=5),v.buff('armor',at=1,duration=3,enemy={'def_mult':1.3,'received_dmg_pct':-20})]
  extra={NAMES[0]:[B('survival','undying',target='all_allies')]}
  yield 'raw-five-members-'+gauge,b,extra
 if not quick:
  b=body(1);p=attack();p['spec'].pop('atk');b['enemy']['patterns']=[p]
  yield 'default-enemy-attack',b,{NAMES[0]:[B('survival','undying')]}
  for name,effects,patterns in [
   ('cover-max-expiry',[E('reload','instant','force_reload',0),B('cover capacity','cover_hp_pct',50,duration=.2)],[attack(atk=1500000,hits=4,interval=.1)]),
   ('cover-max-after-boss-event',[E('reload','instant','force_reload',0),B('cover capacity','cover_hp_pct',50,event='event:target_spawn')],[dict(id='signal',kind='idle',delay=.1,until={'time':.1},emit=['event:target_spawn']),dict(id='incoming',kind='attack',delay=.1,until={'time':.2},spec=dict(coeff=100,atk=2500000,target='slot:1'))]),
   ('cover-heal',[E('reload','instant','force_reload',0),E('repair','instant','cover_heal_pct',10,event='received_hit')],[attack(atk=500000,hits=4,interval=.1)]),
   ('cover-heal-caster-max-hp',[E('reload','instant','force_reload',0),E('repair','instant','cover_heal_pct',10,event='received_hit',scaling='max_hp')],[attack(atk=500000,hits=4,interval=.1)]),
   ('cover-heal-stack-scaling',[E('reload','instant','force_reload',0),B('repair count','',event='every:0.1s',max_stack=3),E('repair','instant','cover_heal_pct',10,event='received_hit',scaling='stack_count',scaling_ref='repair count')],[dict(id='incoming',kind='attack',delay=.15,until={'time':.6},spec=dict(coeff=100,atk=500000,target='slot:1',hits=4,interval=.1))]),
   ('decoy-consumed-state-end',[B('decoy','decoy',1),B('after decoy','atk_pct',12,event='event:state_end:decoy')],[attack(atk=500000,hits=3,interval=.1)]),
   ('received-hit-reaction',[B('damage reaction','atk_pct',10,event='received_hit',max_stack=10),E('heal reaction','instant','heal_hp_pct',1,event='received_hit')],[attack(atk=500000,hits=3,interval=.1)]),
   ('enemy-caster-attack-debuff',[B('enemy power','atk_caster_based_pct',-17.23,target='target')],[attack(atk=500000,hits=3,interval=.1)]),
   ('lazy-invincible-and-split',[B('blocker','invincible',target='allies_top_atk:2'),B('split','received_dmg_split_even',target=['self','allies_lowest_hp_excl:2'])],[attack(atk=500000,hits=3,interval=.1)]),
  ]:
   b=body(2);b['enemy']['patterns']=patterns;effects=[B('survival','undying',target='all_allies')]+effects
   yield name,b,{NAMES[0]:effects}
  for name,broken,list_target in [('lowest-cover-fraction',False,False),('lowest-cover-excludes-broken',True,False),('lowest-cover-in-ordered-list',False,True)]:
   b=body(1)
   b['enemy']['patterns']=[dict(id='left',kind='attack',delay=.1,until={'time':.1},spec=dict(coeff=100,atk=1500000,target='slot:1')),dict(id='right',kind='attack',delay=.1,until={'time':.1},spec=dict(coeff=100,atk=3000000 if broken else 750000,target='slot:5'))]
   effects=[E('reload everyone','instant','force_reload',0,target='all_allies'),B('left cover capacity','cover_hp_pct',50),B('survival','undying',target='all_allies'),E('repair weakest cover','instant','cover_heal_pct',10,['self','allies_lowest_cover_hp:1'] if list_target else 'allies_lowest_cover_hp:1',event='every:0.5s')]
   yield name,b,{NAMES[0]:effects}
  for character in ['아니스','폴리','벨로타 : 펌킨 위치','은화 : 택티컬 업','라플라스','자칼','바이퍼','블랑','로산나','레이블']:
   names=[character]+[n for n in NAMES if n!=character][:4]
   for attacked in (False,True):
    b=body(30,True,names);b['enemy']['patterns']=[v.buff('armor',duration=10,enemy={'def_mult':1.3,'received_dmg_pct':-20})]
    if attacked:b['enemy']['patterns'].append(dict(id='incoming',kind='attack',until={'time':30},spec=dict(coeff=100,atk=200000,target='random:2',hits=60,interval=.5)))
    else:b['enemy']['patterns'].append(dict(id='incoming',kind='attack',delay=100,until={'time':1},spec=dict(coeff=1,atk=1,target='all')))
    yield 'raw-'+character+('-incoming' if attacked else '-no-shots'),b,{names[-1]:[B('survival','undying',target='all_allies')]}

def close(a,b):
 if isinstance(a,dict) and isinstance(b,dict):return a.keys()==b.keys() and all(close(a[k],b[k]) for k in a)
 if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(close(x,y) for x,y in zip(a,b))
 if type(a) in (float,int) and type(b) in (float,int):return math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-6)
 return a==b

def long_fixtures():
 for name,b,extra in fixtures():
  if name not in ('raw-로산나-incoming','raw-자칼-incoming','raw-블랑-incoming','raw-라플라스-incoming'):continue
  b['duration']=180
  for p in b['enemy']['patterns']:
   if p['kind']=='attack':p['until']={'time':180};p['spec'].update(hits=360,interval=.5)
  yield name+'-180',b,extra
