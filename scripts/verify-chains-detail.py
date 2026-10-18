"""Synchronous named application/refresh chains against independent CPU state."""
import copy,hashlib,importlib.util,json,math,sys
from pathlib import Path
from datetime import datetime,timezone
from contextlib import contextmanager
from collections import Counter
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import run
from detail_coverage import a,body_for
from gpu_selector import Cuda

def load(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
oracle=load('chain_state_oracle','verify-detail.py');periodic=load('chain_full_oracle','verify-periodic-detail.py');E=periodic.effect
NAMES=['모더니아','루주','마스트 : 로망틱 메이드','도라','얀']

def primitives():
 out=[]
 def build(name,by_owner,events,queries):
  p=oracle.program(oracle.characters(NAMES),[(e,NAMES[i]) for i,es in by_owner.items() for e in es]);script=[[0,0,0,i,0,-1,0,0] for i in range(5)]
  commands=[(t,0,code,who,-1) for t,code,who in events]+[(t,2,0,who,j) for j,(t,who,value) in enumerate(queries)]
  for t,op,code,who,j in sorted(commands,key=lambda x:(x[0],x[1])):script.append([t,op,code,who,-1 if op==2 else 0,j,0,0])
  out.append((name,p,script,[v for t,who,v in queries]))
 def marker(name='A',event='battle_start',**kw):return E(name,'buff','',0,event=event,**kw)
 def observe(name='seen',event='event:A',value=10,**kw):return E(name,'buff','atk_pct',value,event=event,max_stack=100,**kw)
 build('marker-default-broadcast',{0:[marker()],**{i:[observe()] for i in range(1,5)}},[],[(.1,i,0 if i==0 else 10) for i in range(5)])
 build('recipient-adjacent-audience',{2:[marker(target='allies_adjacent:2',event_scope='recipients')],**{i:[observe()] for i in (0,1,3,4)}},[],[(.1,i,10 if i in (1,3) else 0) for i in range(5)])
 for scope,limited in [('recipients',False),('squad',False),('recipients',True)]:
  es={0:[marker(target='N102',event_scope=scope,**({'max_trigger':1} if limited else {})),observe()]}
  build('empty-target-'+scope+'-limited-'+str(limited),es,[],[(.1,0,10 if scope=='squad' else 0)])
 src=marker(duration=.25);src['trigger']['timing']=['battle_start','burst_cast']
 build('single-stack-refresh-silent-expiry-is-new',{0:[src,observe(value=1)]},[(.1,3,0),(.5,3,0)],[(.2,0,1),(.6,0,2)])
 build('new-generic-precedes-stack-one',{0:[marker(),marker('gate','event:A'),observe(event='stack_reach:A:1',condition=['self_state:gate'])]},[],[(.1,0,10)])
 src=marker(max_stack=2);src['trigger']['timing']=['battle_start','on_attack']
 build('refresh-stack-before-generic-and-cap-still-notifies',{0:[src,marker('gate','stack_reach:A:1'),E('remove gate','instant','remove_named_buff',0,event='stack_reach:A:2',target_effect='gate'),observe(condition=['not_self_state:gate'])]},[(.1,7,0),(.2,7,0)],[(.1,0,20),(.2,0,30)])
 src=E('A','buff','atk_pct',0,target='allies_top_atk:1',event_scope='recipients',max_stack=2);src['trigger']['timing']=['battle_start','burst_cast']
 build('lazy-first-caster-then-resolved-recipient',{0:[src,observe()],4:[observe()]},[(.5,3,0)],[(.1,0,10),(.1,4,0),(.6,0,10),(.6,4,10)])
 src=marker(target='allies_top_atk:1',event_scope='recipients',max_stack=2);src['trigger']['timing']=['battle_start','burst_cast']
 build('lazy-marker-stays-unresolved-on-stat-query',{0:[src,observe()],4:[observe()]},[(.5,3,0)],[(.1,0,10),(.1,4,0),(.6,0,20),(.6,4,0)])
 typed=E('typed','buff','split_dmg_pct',5,duration=3);typed['trigger']['timing']=['battle_start','burst_cast']
 build('typed-notification-after-generic-and-stack',{0:[typed,marker('g1','event:typed'),E('remove g1','instant','remove_named_buff',0,event='stack_reach:typed:1',target_effect='g1'),marker('g2','stack_reach:typed:1'),observe(event='event:stat_applied:split_dmg_pct',condition=['self_state:g2','not_self_state:g1'])]},[(.5,3,0)],[(.1,0,10),(.6,0,20)])
 build('same-name-paths-merge-and-use-incoming-expiry',{0:[E('A','buff','atk_pct',10,duration=2),E('A','buff','atk_pct',20,event='burst_cast',duration=5),observe(value=1)]},[(.1,3,0)],[(.05,0,11),(.2,0,11),(2.5,0,11),(5.2,0,1)])
 build('same-name-different-stat-remain-independent',{0:[E('A','buff','crit_dmg',0),E('A','buff','atk_pct',20,event='burst_cast'),observe(value=1)]},[(.1,3,0)],[(.2,0,22)])
 src=marker();src['trigger']['timing']=['battle_start','event:state_end:A']
 build('remove-recreate-retains-latched-stack-one',{0:[src,E('remove once','instant','remove_named_buff',0,event='event:A',target_effect='A',max_trigger=1),observe(event='stack_reach:A:1',value=1)]},[],[(.1,0,2)])
 cap=E('A','buff','atk_pct',10,scaling='stack_count',scaling_ref='fuel',max_stack=2,duration=3);cap['trigger']['timing']=['battle_start','burst_cast']
 build('refresh-recaptures-scaling-after-name-callback',{0:[E('fuel start','instant','gauge_charge',1,gauge_id='fuel',gauge_max=10),cap,E('name charges fuel','instant','gauge_charge',1,event='event:A',gauge_id='fuel')]},[(.5,3,0)],[(.1,0,10),(.6,0,30)])
 build('false-passive-still-emits-cpu-named-events',{0:[marker(event='passive',condition=['during_full_burst']),observe()]},[],[(.1,0,10)])
 base=[E('fuel start','instant','gauge_charge',1,gauge_id='fuel'),E('shield','buff','shield_from_max_hp_pct',50,scaling='stack_count',scaling_ref='fuel'),observe(event='event:shield_applied',value=1),E('positive shield','buff','atk_pct',50,event='passive',condition=['during_shield'])]
 build('zero-shield-snapshot-does-not-follow-later-gauge',{0:base+[E('shield name drains','instant','gauge_consume',-1,event='event:shield',gauge_id='fuel'),E('later fuel','instant','gauge_charge',2,event='burst_cast',gauge_id='fuel')]},[(.5,3,0)],[(.1,0,1),(.6,0,1)])
 build('positive-shield-remains-after-scaling-ref-drained',{0:base+[E('later drain','instant','gauge_consume',-1,event='burst_cast',gauge_id='fuel')]},[(.5,3,0)],[(.1,0,51),(.6,0,51)])
 return out

@contextmanager
def notifications():
 from calculator.buff_manager import BuffManager
 original=BuffManager._notify;counts=Counter()
 def track(self,event,t,caster):counts[event]+=1;return original(self,event,t,caster)
 with patch.object(BuffManager,'_notify',track):yield counts

def full_scenarios():
 n=periodic.NAMES
 src=E('A','buff','',0,event='on_attack',max_stack=2,duration=2,max_trigger=5,event_scope='recipients')
 yield 'full-carrier-refresh-and-cap',{n[0]:[src,E('named damage','damage','damage',100,'target',event='event:A')]},8,['event:A']
 yield 'full-name-before-health-post',{n[0]:[E('room','buff','max_hp_only_pct',100),E('A','buff','max_hp_pct',100,event='burst_cast',duration=2),E('before hp','buff','atk_dmg_pct',70,event='event:A',condition=['self_hp_below:90'],duration=3)]},8,['event:A']
 yield 'full-stat-applied-and-shield-order',{n[0]:[E('typed','buff','dot_dmg_pct',20,event='burst_cast',duration=4),E('shield','buff','shield_from_max_hp_pct',50,event='event:stat_applied:dot_dmg_pct',duration=3),E('from shield','buff','atk_pct',50,event='event:shield_applied',duration=3)]},8,['event:stat_applied:dot_dmg_pct','event:shield_applied']
 cap=E('captured','buff','atk_pct',10,event='on_attack_count:5',duration=3,max_stack=3,scaling='stack_count',scaling_ref='fuel')
 yield 'full-refresh-scaling-and-bullet-lifetimes',{n[0]:[E('fuel init','instant','gauge_charge',1,gauge_id='fuel',gauge_max=10),cap,E('fuel on capture','instant','gauge_charge',1,event='event:captured',gauge_id='fuel'),E('one shot','buff','atk_dmg_pct',30,event='event:captured',duration_bullets=1)]},8,['event:captured']
 from calculator.buff_manager import char_effects
 modes=[copy.deepcopy(e) for e in char_effects('모더니아') if e.get('type')=='weapon_change'];mode_name=modes[0]['name']
 yield 'full-weapon-mode-named-broadcast',{'모더니아':modes,n[0]:[E('mode witness','buff','atk_pct',100,event='event:'+mode_name,duration=8)]},25,['event:'+mode_name]

def verify(device,backend='auto',include_real=True):
 cases=[]
 for name,p,script,expected in primitives():
  bs={n:{'atk':100000+i*10000,'hp':1000000,'def':1000} for i,n in enumerate(NAMES)};cpu,totals=oracle.oracle(p,script,[31784,50],bs);gpu=run(device,[p],script,[[31784,50]],[bs],module_backend=backend);errors=[]
  for i,(x,y) in enumerate(zip(cpu,gpu['queries'][0])):
   if x[0]!=expected[i] or y[0]!=expected[i]:errors.append([i,'expected ATK',expected[i],x[0],y[0]])
   for k in (0,6,27,28,37):
    if not math.isclose(x[k],y[k],rel_tol=1e-12,abs_tol=1e-8):errors.append([i,k,x[k],y[k]])
  case={'name':name,'passed':not errors,'errors':errors,'backend':gpu['module_backend']};cases.append(case);print(json.dumps(case),flush=True)
 for name,es,seconds,required in full_scenarios():
  squad=['리타','크라운','모더니아','도라','얀'] if name=='full-weapon-mode-named-broadcast' else periodic.NAMES
  with periodic.custom_effects(es),notifications() as observed:case=periodic.full.compare(device,name,body_for(squad,seconds,True),module_backend=backend)
  case['required_notifications']={event:observed[event] for event in required};case['passed'] &= all(case['required_notifications'].values());case['backend']=backend;cases.append(case);print(json.dumps({'name':name,'passed':case['passed'],'cpu':case['cpu_total'],'gpu':case['gpu_total'],'notifications':case['required_notifications']},ensure_ascii=True),flush=True)
 old=json.loads((ROOT/'research/detail-coverage-events.json').read_text(encoding='utf-8'));new=json.loads((ROOT/'research/detail-coverage-chains.json').read_text(encoding='utf-8'));was={r['character'] for r in old['results'] if r['supported']}
 for record in (new['results'] if include_real else []):
  name=record['character']
  if record['supported'] and name not in was:
   squad=[name]+[n for n in NAMES if n!=name][:4]
   try:
    with notifications() as observed:case=periodic.full.compare(device,'real-'+name,body_for(squad,60,True),module_backend=backend)
    case['named_notification_count']=sum(value for event,value in observed.items() if event.startswith('event:'));case['backend']=backend
   except (Exception,SystemExit) as error:case={'name':name,'passed':False,'error':str(error)}
   cases.append(case);print(json.dumps({'name':name,'passed':case['passed'],**({'error':case['error']} if 'error' in case else {'cpu':case['cpu_total'],'gpu':case['gpu_total'],'named_events':case['named_notification_count']})},ensure_ascii=True),flush=True)
 return cases

if __name__=='__main__':
 d=Cuda()
 try:cases=verify(d,'native')+verify(d,'ptx')
 finally:d.close()
 sources=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','scripts/verify-chains-detail.py']
 r={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in cases),'cpu_trace_used_as_gpu_input':False,'scope':'named application/refresh chains in authored notifications and independent static five-member combat; not every live-state instance combination','cases':cases,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}}
 (ROOT/'research/detail-chains-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
