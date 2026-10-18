"""Full GPU control ownership/hold/tap loop against independent CPU simulation."""
import sys,json,math,copy,hashlib,importlib.util
from pathlib import Path
from datetime import datetime,timezone
from contextlib import contextmanager
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from detail_gpu import evaluate_full,UnsupportedDetail
from gpu_selector import Cuda
spec=importlib.util.spec_from_file_location('control_periodic',ROOT/'scripts/verify-periodic-detail.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
NAMES=p.NAMES;E=p.effect

@contextmanager
def configured(controls=None,camera=None,mode='solo'):
 original=a.sim.prepare
 def prepare(request):
  prepared=original(request)
  for c in prepared.squad:
   if controls is not None:c['control']=copy.deepcopy(controls.get(c['name'],{}))
  if camera is not None:prepared.config['camera']=camera
  prepared.config['control_mode']=mode;return prepared
 with patch.object(a.sim,'prepare',prepare):yield

@contextmanager
def observe():
 from calculator.buff_manager import BuffManager
 from calculator.timeline import CharState
 init=CharState.__init__;notify=BuffManager.notify;bm_init=BuffManager.__init__;states={};manager={};events={'holds':[],'partial':0,'shots':{},'full':0}
 def char_init(self,*args,**kw):init(self,*args,**kw);states[self.name]=self
 def manager_init(self,*args,**kw):bm_init(self,*args,**kw);manager['bm']=self
 def event(self,ev,t,who,*args,**kw):
  if ev.startswith('charge_hold:'):events['holds'].append([who,ev,t])
  if ev=='non_full_charge_fire':events['partial']+=1
  if ev=='full_charge':events['full']+=1
  if ev=='on_attack':events['shots'][who]=events['shots'].get(who,0)+1
  return notify(self,ev,t,who,*args,**kw)
 with patch.object(CharState,'__init__',char_init),patch.object(BuffManager,'__init__',manager_init),patch.object(BuffManager,'notify',event):yield states,manager,events

def compare(device,label,body,backend='native'):
 compiled=a.evaluate({**body,'_compile_gpu_detail':True});gpu=evaluate_full(device,compiled,module_backend=backend)
 with observe() as (states,manager,events):cpu=a.evaluate(body)
 checks={key:cpu[key]==gpu[key] for key in ['total_damage','members','base_stats','burst_timeline','shooting_policy']};errors=[];bm=manager['bm'];names=body['squad'];camera=sum(1<<i for i,n in enumerate(names) if n in bm.state.get('camera',()))
 for name in names:
  cs=states[name];g=gpu['compute']['final_control'][name]
  expected={'charging':bool(bm.state.get('charging',{}).get(name)),'phase':{'ready':0,'charging':1,'post_delay':2}[cs._charge_phase],'full_at':cs._charge_full_t,'release_at':cs._hold_release_t if math.isfinite(cs._hold_release_t) else 1e30,'owner':bm.state.get('ctrl_owner') or '', 'camera_mask':camera,'shots':events['shots'].get(name,0),'sequence_index':cs._ctrl_seq_i,'preemptions':bm.state.get('ctrl_preempt',{}).get(name,0),'normal_landed':name in bm.state.get('normal_attack_landed',set())}
  for k,v in expected.items():
   if (not math.isclose(v,g[k],rel_tol=1e-12,abs_tol=1e-8)) if isinstance(v,float) else v!=g[k]:errors.append([name,k,v,g[k]])
 checks['control_state_equal']=not errors
 events['preempt']=sum(bm.state.get('ctrl_preempt',{}).values())
 return {'name':label,'passed':all(checks.values()),'checks':checks,'control_errors':errors,'cpu_total':cpu['total_damage'],'gpu_total':gpu['total_damage'],'observed':events,'backend':backend,'squad':names,'duration':body['duration'],'gpu_ms':gpu['compute']['elapsed_ms']}

def scenarios():
 owner=NAMES[2];other=NAMES[4]
 probes=[E('charging power','buff','atk_pct',17,event='passive',condition=['during_charge']),E('focus power','buff','atk_dmg_pct',13,event='passive',condition=['focusing']),E('held stack','buff','charge_dmg_pct',7,event='charge_hold:0.5',max_stack=5,duration=5),E('partial stack','buff','atk_pct',3,event='non_full_charge_fire',max_stack=5,duration=2)]
 yield 'auto-during-charge-and-static-camera',{owner:probes},{},None,12,{}
 for camera in [owner,'',NAMES[0]]:yield 'explicit-camera-'+str(camera),{owner:probes},{},camera,8,{}
 yield 'absolute-hold-multiple-threshold-spellings',{owner:probes+[E('same threshold distinct spelling','buff','atk_pct',9,event='charge_hold:0.50',max_stack=3),E('hold count','buff','charge_dmg_pct',11,event='charge_hold_count:0.5:2',max_stack=3)]},{owner:{'sequence':[{'t':0,'action':'hold','until':2.2},{'t':4,'action':'hold','until':7.5}]}},None,10,{'holds':True}
 yield 'hold-full-burst-retains-one-bullet',{owner:probes+[E('one round buff','buff','charge_dmg_pct',70,event='burst_cast',duration_bullets=1)]},{owner:{'hold':{'policy':'own_full_burst','lead':.1}}},None,30,{'holds':True}
 yield 'after-fb-judge-and-force-reload',{owner:probes+[E('judge interruption','instant','force_reload',0,event='charge_hold:0.5',condition=['not_during_full_burst'])]},{owner:{'hold':{'policy':'charge_hold_after_fb','lead':.1}}},None,30,{'holds':True}
 yield 'tap-with-periodic-full-charge',{owner:probes},{owner:{'tap_fire':{'rate':3.6,'release':.03,'full_charge_interval':5.5}}},None,12,{'partial':True,'full':True}
 yield 'tap-and-after-fb-judge',{owner:probes},{owner:{'tap_fire':{'rate':3.6,'release':.03,'full_charge_interval':5.5},'hold':{'policy':'charge_hold_after_fb','lead':.1}}},None,30,{'partial':True,'holds':True}
 yield 'full-charge-latch-survives-speed-expiry',{owner:probes+[E('fast initially','buff','charge_speed_pct',100,duration=.2)]},{owner:{'sequence':[{'t':0,'action':'hold','until':2.2}]}},None,6,{'holds':True}
 yield 'sequence-preempts-tapping-and-releases',{owner:probes,other:probes},{owner:{'tap_fire':{'rate':3.6,'release':.03}},other:{'sequence':[{'t':1,'action':'hold','until':3.5}]}},None,10,{'partial':True,'holds':True}
 yield 'burst-chain-close-releases-held-charge',{owner:probes},{owner:{'click':[{'window':'burst_chain','mode':'hold_until_close'},{'window':'always','mode':'tap','rate':3.6,'release':.03}]}},None,12,{'partial':True}
 yield 'equal-priority-new-request-preempts',{owner:probes,other:probes},{owner:{'click':[{'window':'always','mode':'tap','rate':3.6,'release':.03,'priority':20}]},other:{'click':[{'window':'burst_chain','mode':'hold_until_close','priority':20}]}},None,8,{'partial':True,'preempt':True}
 yield 'higher-priority-overrides-older-request',{owner:probes,other:probes},{owner:{'click':[{'window':'always','mode':'tap','rate':3.6,'release':.03,'priority':10}]},other:{'click':[{'window':'burst_chain','mode':'hold_until_close','priority':30}]}},None,8,{'partial':True,'preempt':True}
 def weapon(kind,**kw):return {'source':'스킬3','name':'held weapon mode','type':'weapon_change','target':'self','weapon_type':kind,'max_ammo':-1,'damage_coeff':{'10':251},'trigger':{'timing':['burst_cast'],'condition':[]},**kw}
 yield 'auto-mode-preserves-then-clears-charging-state',{owner:probes+[weapon('SMG',duration=3)]},{owner:{'sequence':[{'t':0,'action':'hold','until':6}]}},None,10,{'holds':True}
 yield 'charge-mode-entry-while-already-holding',{owner:probes+[weapon('SR',max_ammo=3,duration_bullets=3,charge_time=.3,full_charge_mult=250)]},{owner:{'sequence':[{'t':0,'action':'hold','until':5}]}},None,10,{'holds':True}
 yield 'held-mode-force-reload-interrupts-charge',{owner:probes+[weapon('SR',max_ammo=3,duration=4,charge_time=.3),E('interrupt held mode','instant','force_reload',0,event='charge_hold:0.5',condition=['during_full_burst'],max_trigger=1)]},{owner:{'hold':{'policy':'own_full_burst','lead':.1}}},None,14,{'holds':True}
 yield 'interrupted-auto-refill-survives-tap-resume',{owner:[weapon('SMG',duration=2),E('instant charge','buff','charge_speed_pct',100),E('instant reload','buff','reload_speed_pct',100),E('refill in full burst','buff','atk_pct',500,event='event:full_reload',condition=['during_full_burst'],duration=4)]},{owner:{'click':[{'window':'own_full_burst','mode':'tap','rate':3.6,'release':.03}]}},None,12,{}
 yield 'zero-hold-threshold-has-own-bullet-lifetime-rule',{owner:[E('zero hold one bullet','buff','charge_dmg_pct',15,event='charge_hold:0',duration_bullets=1),E('second spelling','buff','atk_pct',9,event='charge_hold:0.00',duration=1)]},{},None,6,{'holds':True}
 yield 'camera-switch-preserves-same-frame-buff-query',{owner:[E('focused team power','buff','atk_pct',100,'all_allies',event='passive',condition=['focusing'])]},{owner:{'click':[{'window':'burst_chain','mode':'hold_until_close','priority':30}]},other:{'tap_fire':{'rate':3.6,'release':.03}}},None,8,{'partial':True}

def verify(device,backend='native',include_references=True):
 cases=[];unsupported=[]
 for label,effects,controls,camera,seconds,requirements in scenarios():
  body=body_for(NAMES,seconds,True)
  try:
   with p.custom_effects(effects),configured(controls,camera):c=compare(device,label,body,backend)
   c['requirements']={k:bool(c['observed'][k]) for k in requirements};c['passed'] &= all(c['requirements'].values())
  except (Exception,SystemExit) as e:c={'name':label,'passed':False,'error':str(e),'backend':backend}
  cases.append(c);print(json.dumps(c,ensure_ascii=True),flush=True)
 if include_references:
  references=json.loads((ROOT/'research/detail-charge-control-cpu-references.json').read_text(encoding='utf-8'))
  for ref in references['cases']:
   subject,policy=ref['subject'],ref['policy'];label=subject+'-'+policy;body=copy.deepcopy(ref['input']);body['shooting_policy']='character' if policy=='engine-default' else 'auto'
   controls=None if policy in ('app-auto','engine-default') else {subject:ref['controls']};camera=ref['camera']
   try:
    with configured(controls,camera):c=compare(device,label,body,backend)
   except UnsupportedDetail as e:unsupported.append({'name':label,'issues':e.issues});continue
   except (Exception,SystemExit) as e:c={'name':label,'passed':False,'error':str(e),'backend':backend}
   cases.append(c);print(json.dumps(c,ensure_ascii=True),flush=True)
 return {'cases':cases,'unsupported_references':unsupported,'passed':all(c['passed'] for c in cases)}
if __name__=='__main__':
 d=Cuda()
 try:reports={backend:verify(d,backend) for backend in ['native','ptx']}
 finally:d.close()
 files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','scripts/verify-control-detail.py']
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(r['passed'] for r in reports.values()),'cpu_trace_used_as_gpu_input':False,'scope':'Explicit hold/tap/camera ownership and supported complete real controls; unrelated unsupported source effects remain rejected, not skipped in a simulated squad','backends':reports,'source_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}}
 (ROOT/'research/detail-control-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
