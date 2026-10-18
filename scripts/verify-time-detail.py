"""Independent CPU/GPU lifetime scaling and shared periodic-clock checks."""
import hashlib,importlib.util,json,math,sys
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from gpu_selector import Cuda
from detail_gpu import run
from detail_coverage import body_for
spec=importlib.util.spec_from_file_location('time_stack_oracle',ROOT/'scripts/verify-stackops-detail.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
E=base.E;NAMES=base.NAMES;oracle=base.oracle;periodic=base.periodic

def primitives():
 out=[]
 def build(name,effects,events,checks,clock=True):
  if clock:effects=[(i,E('counter view','buff','atk_pct',1,scaling='stack_count',scaling_ref='counter')) for i in range(5)]+effects
  p=oracle.program(oracle.characters(NAMES),[(e,NAMES[i]) for i,e in effects]);script=[[0,0,0,i,0,-1,0,0] for i in range(5)]
  commands=[(t,0,event,who,-1) for t,event,who in events]+[(t,2,0,who,i) for i,(t,who,atk,ref) in enumerate(checks)]
  for t,op,event,who,index in sorted(commands,key=lambda x:(x[0],x[1])):script.append([t,op,event,who,p['states']['counter' if clock else 'state'] if op==2 else 0,index,0,0])
  out.append((name,p,script,checks))
 def pulse(period=2):return E('pulse','instant','gauge_charge',1,event=f'every:{period}s',gauge_id='counter')
 def pct(value,event='battle_start',**kw):return E('percentage','buff','skill_cooldown_pct',value,event=event,**kw)
 def flat(name,value,stat='effect_interval',**kw):return E(name,'buff',stat,value,target_effect='pulse',**kw)
 build('percentage-permanent-false-runtime-still-affects-period',[(0,pulse()),(0,pct(-50,event='passive',condition=['during_full_burst']))],[],[(.99,0,0,0),(1.01,0,1,1),(2.01,0,2,2)])
 build('percentage-start-expiry-rescale-remaining-phase',[(0,pulse(4)),(0,pct(-50,event='burst_cast',duration=1))],[(1,3,0)],[(1,0,0,0),(2,0,0,0),(2.99,0,0,0),(3.01,0,1,1),(7.01,0,2,2)])
 build('both-flat-groups-before-percentage',[(0,pulse(4)),(0,flat('flat',-1)),(0,flat('cooldown',-1,'skill_cooldown')),(0,pct(-50))],[],[(.99,0,0,0),(1.01,0,1,1),(2.01,0,2,2)])
 gate=E('gate','buff','',0,event='burst_cast')
 remove=E('remove gate','instant','remove_named_buff',0,event='on_attack',target_effect='gate')
 build('named-flat-runtime-gates-rescale-phase',[(0,pulse(4)),(0,flat('conditional flat',-3,event='passive',condition=['self_state:gate'])),(0,gate),(0,remove)],[(1,3,0),(2,7,0)],[(1,0,0,0),(1.74,0,0,0),(1.76,0,1,1),(2,0,1,1),(4.99,0,1,1),(5.01,0,2,2)])
 build('minimum-five-percent-of-each-base-period',[(0,pulse()),(0,flat('oversized flat',-100)),(0,pct(-200))],[],[(.11,0,1,1),(.21,0,2,2),(.31,0,3,3)])
 reduce=E('one-off','instant','skill_cooldown_reduce_pct',50,event='burst_cast',target_effect='ignored by CPU')
 build('one-off-reduces-remaining-but-not-future-period',[(0,pulse(4)),(0,reduce)],[(1,3,0)],[(2.49,0,0,0),(2.51,0,1,1),(6.49,0,1,1),(6.51,0,2,2)])
 build('one-off-only-affects-selected-clock-owners',[(0,pulse(4)),(1,pulse(4)),(0,reduce)],[(1,3,0)],[(2.51,0,1,1),(2.51,1,0,0),(4.01,0,1,1),(4.01,1,1,1)])
 build('one-off-at-startup-after-standalone-clock-init',[(0,pulse(4)),(0,E('startup reduce','instant','skill_cooldown_reduce_pct',50))],[],[(1.99,0,0,0),(2.01,0,1,1),(6.01,0,2,2)])
 build('own-every-reduction-is-overwritten-by-post-fire-clock',[(0,pulse(3)),(0,E('reset clocks','instant','skill_cooldown_reduce_pct',100,event='every:1s'))],[],[(1.1,0,0,0),(1.2,0,1,1),(2.1,0,1,1),(2.2,0,2,2)])
 p=pulse(1);p['trigger']['timing']=['every:1s','every:2s']
 build('distinct-every-entries-share-one-clock',[(0,p)],[],[(1.9,0,0,0),(2,0,1,1),(3.9,0,1,1),(4,0,2,2),(10,0,3,3)])
 p=pulse(1);p['trigger']['timing']=['every:1s','every:1s'];p['max_trigger']=3
 build('duplicate-every-late-ticks-share-clock-and-budget',[(0,p)],[],[(3.1,0,2,2),(3.2,0,3,3),(6.1,0,3,3)])
 build('flat-sum-preserves-small-terms-under-cancellation',[(0,pulse()),(0,flat('positive first',1e16,'skill_cooldown')),(0,flat('negative second',-1e16)),(0,flat('unit third',1))],[],[(2.01,0,0,0),(3.01,0,1,1)])
 build('percentage-sum-preserves-small-terms-under-cancellation',[(0,pulse(1)),(0,E('pct A','buff','skill_cooldown_pct',-1e16)),(0,E('pct B','buff','skill_cooldown_pct',1)),(0,E('pct C','buff','skill_cooldown_pct',1e16))],[],[(1.005,0,0,0),(1.015,0,1,1)])
 build('critical-sums-and-rate-clamp-follow-python-runtime',[(0,E('dmg A','buff','crit_dmg',-1e16)),(0,E('dmg B','buff','crit_dmg',1)),(0,E('dmg C','buff','crit_dmg',1e16)),(0,E('rate A','buff','crit_rate',-1e18)),(0,E('rate B','buff','crit_rate',100)),(0,E('rate C','buff','crit_rate',1e18)),(0,E('negative rate','buff','crit_rate',-1000,event='burst_cast'))],[(.2,3,0)],[(.1,0,0,0),(.3,0,0,0)])
 fuel=E('fuel load','instant','gauge_charge',2,gauge_id='fuel')
 source=E('state','buff','atk_pct',10,duration=1,duration_scaling='stack_count',duration_scaling_ref='fuel')
 source['trigger']['timing']=['battle_start','burst_cast']
 build('duration-sampled-on-refresh-not-on-later-fuel-change',[(0,fuel),(0,E('more fuel','instant','gauge_charge',1,event='burst_cast',gauge_id='fuel')),(0,source),(0,E('drain','instant','gauge_consume',-1,event='on_attack',gauge_id='fuel'))],[(.5,3,0),(.7,7,0)],[(1.5,0,10,1),(3.49,0,10,1),(3.51,0,0,0)],False)
 first=E('state','buff','atk_pct',10,duration=2)
 second=E('state','buff','atk_pct',99,event='burst_cast',duration=1,duration_scaling='stack_count',duration_scaling_ref='fuel')
 build('alias-retains-values-but-incoming-scaled-expiry',[(0,E('fuel','instant','gauge_charge',3,gauge_id='fuel')),(0,first),(0,second)],[(.5,3,0)],[(2.6,0,10,1),(3.49,0,10,1),(3.51,0,0,0)],False)
 build('named-stack-add-refreshes-raw-unscaled-duration',[(0,E('fuel','instant','gauge_charge',3,gauge_id='fuel')),(0,source),(0,E('add stack','instant','buff_stack_add',1,event='on_attack',target_effect='state'))],[(.5,7,0)],[(1.49,0,10,1),(1.51,0,0,0)],False)
 inactive=E('state','buff','atk_pct',10,event='on_attack',max_trigger=0,max_stack=3,duration=1,duration_scaling='stack_count',duration_scaling_ref='fuel')
 build('stack-init-uses-raw-unscaled-duration',[(0,E('fuel','instant','gauge_charge',3,gauge_id='fuel')),(0,inactive),(0,E('init','instant','buff_stack_init',2,event='burst_cast',target_effect='state'))],[(.1,3,0)],[(1.09,0,20,2),(1.11,0,0,0)],False)
 gate=E('gate','buff','',0,duration=.5)
 passive=E('state','buff','atk_pct',10,event='passive',duration=1,duration_scaling='stack_count',duration_scaling_ref='fuel',condition=['self_state:gate'])
 build('finite-passive-duration-resamples-while-condition-holds',[(0,fuel),(0,gate),(0,passive),(0,E('more fuel','instant','gauge_charge',1,event='burst_cast',gauge_id='fuel'))],[(.2,3,0)],[(.25,0,10,1),(.5,0,10,1),(3.24,0,10,1),(3.26,0,0,0)],False)
 dynamic=E('state','buff','atk_pct',10,duration=None,duration_values={'10':2},duration_scaling='stack_count',duration_scaling_ref='fuel',scaling='stack_count',scaling_ref='fuel')
 build('level-duration-value-remains-dynamic-but-expiry-is-sampled',[(0,fuel),(0,dynamic),(0,E('more fuel','instant','gauge_charge',1,event='burst_cast',gauge_id='fuel'))],[(.5,3,0)],[(.1,0,20,1),(1,0,30,1),(4.01,0,0,0)],False)
 build('zero-duration-reference-still-emits-synchronous-name',[(0,E('state','buff','atk_pct',10,duration=1,duration_scaling='stack_count',duration_scaling_ref='missing')),(0,E('witness','buff','crit_dmg',7,event='event:state',condition=['self_state:state'],duration=1))],[],[(.1,0,0,0)],False)
 return out

def full_scenarios():
 n=periodic.NAMES
 pulse=E('pulse','buff','atk_pct',2,'all_allies',event='every:2s',duration=3,max_stack=20)
 yield 'full-flat-percent-and-one-off-phase',{n[0]:[pulse,E('reduce all','instant','skill_cooldown_reduce_pct',25,'all_allies',event='on_attack_count:5')],n[1]:[E('flat','buff','effect_interval',-.5,n[0],event='burst_cast',duration=3,target_effect='pulse'),E('percent','buff','skill_cooldown_pct',-35,n[0],event='full_burst_start',duration=3)]},12
 p=E('pulse','buff','atk_pct',2,'all_allies',event='every:1s',duration=3,max_stack=30);p['trigger']['timing'].append('every:2s')
 yield 'full-shared-multiple-every-with-recursive-reduction',{n[0]:[p,E('reduce','instant','skill_cooldown_reduce_pct',100,event='every:1.5s')]},8
 yield 'full-startup-before-clock-initialization',{n[0]:[pulse,E('startup reduce','instant','skill_cooldown_reduce_pct',100)],n[1]:[E('lazy pct','buff','skill_cooldown_pct',-50,'allies_top_atk:1')]},8
 yield 'full-duration-scaling-conditional-and-value-snapshots',{n[0]:[E('fuel','instant','gauge_charge',1,gauge_id='fuel'),E('fuel on attacks','instant','gauge_charge',1,event='on_attack_count:3',gauge_id='fuel'),E('scaled duration','buff','atk_pct',10,'all_allies',event='on_attack_count:4',duration=.2,duration_scaling='stack_count',duration_scaling_ref='fuel'),E('level dynamic','buff','crit_dmg',2,'all_allies',event='burst_cast',duration=None,duration_values={'3':1,'10':1},scaling='stack_count',scaling_ref='fuel')]},10
 yield 'full-burst-recipient-targets-outside-boundaries',{n[0]:[E('all casts','buff','atk_pct',7,'all_allies_burst_casted',event='on_attack_count:3',duration=25,max_stack=3),E('b3 casts','buff','crit_dmg',11,'allies_burst_casted_burst3',event='on_attack_count:5',duration=25,max_stack=2)]},30

# Independent CPU observations verify effective periodic changes, never GPU input.
def compare(device,name,body,backend,effects=None,require_change=False,require_owner=None):
 from calculator.buff_manager import BuffManager
 tick=BuffManager.tick;seen=defaultdict(set)
 def tracked(manager,t):
  result=tick(manager,t)
  for eff,owner in manager._effects:
   current=manager._next_fire.get(id(eff))
   if current:seen[owner+' / '+eff.get('name','')].add(round(current[1],9))
  return result
 if effects is None:
  with patch.object(BuffManager,'tick',tracked):c=periodic.full.compare(device,name,body,module_backend=backend)
 else:
  with periodic.custom_effects(effects),patch.object(BuffManager,'tick',tracked):c=periodic.full.compare(device,name,body,module_backend=backend)
 c['cpu_observed_periods']={k:sorted(v) for k,v in seen.items()};c['backend']=backend
 if require_change:c['passed'] &= any(len(v)>1 for k,v in seen.items() if require_owner is None or k.startswith(require_owner+' / '))
 return c

def verify(device,backend='auto',include_real=True):
 cases=[]
 for name,p,script,checks in primitives():
  bs={n:{'atk':100000+i*10000,'hp':1000000,'def':1000} for i,n in enumerate(NAMES)};cpu,totals=oracle.oracle(p,script,[31784,50],bs);gpu=run(device,[p],script,[[31784,50]],[bs],module_backend=backend);errors=[]
  for i,(x,y,expected) in enumerate(zip(cpu,gpu['queries'][0],checks)):
   for key,value in [(0,expected[2]),(37,expected[3])]:
    if x[key]!=value or y[key]!=value:errors.append([i,'expected',key,value,x[key],y[key]])
   for key in list(range(32))+[36,37]:
    if not math.isclose(x[key],y[key],rel_tol=1e-12,abs_tol=1e-8):errors.append([i,key,x[key],y[key]])
  c={'name':name,'passed':not errors and totals==gpu['totals'][0],'errors':errors,'backend':backend};cases.append(c);print(json.dumps(c),flush=True)
 for name,effects,seconds in full_scenarios():
  c=compare(device,name,body_for(periodic.NAMES,seconds,True),backend,effects,require_change='phase' in name);cases.append(c);print(json.dumps({'name':name,'passed':c['passed'],'cpu':c['cpu_total'],'gpu':c['gpu_total']}),flush=True)
 if include_real:
  old=json.loads((ROOT/'research/detail-coverage-stackops.json').read_text(encoding='utf-8'));now=json.loads((ROOT/'research/detail-coverage-time.json').read_text(encoding='utf-8'));was={r['character'] for r in old['results'] if r['supported']}
  for r in now['results']:
   name=r['character']
   if not r['supported'] or name in was:continue
   names=[name]+[n for n in NAMES if n!=name][:4];c=compare(device,'real-'+name,body_for(names,60,True),backend,require_change=name=='에이다');cases.append(c);print(json.dumps({'name':name,'passed':c['passed'],'cpu':c['cpu_total'],'gpu':c['gpu_total']},ensure_ascii=True),flush=True)
  names=['아르카나','이사벨','루주','마스트 : 로망틱 메이드','도라'];c=compare(device,'real-arcana-isabel-effective-period',body_for(names,60,True),backend,require_change=True,require_owner='이사벨');cases.append(c);print(json.dumps({'name':c['name'],'passed':c['passed'],'cpu':c['cpu_total'],'gpu':c['gpu_total']}),flush=True)
 return cases

if __name__=='__main__':
 d=Cuda()
 try:cases=verify(d,'native')+verify(d,'ptx')
 finally:d.close()
 files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','scripts/verify-time-detail.py']
 r={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in cases),'cpu_trace_used_as_gpu_input':False,'scope':'authored lifetimes/clocks, independent full squads, and newly accepted real squads in static-boss mode; not all effects/characters/combinations','cases':cases,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
 (ROOT/'research/detail-time-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
