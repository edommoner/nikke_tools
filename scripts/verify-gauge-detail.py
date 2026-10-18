"""Independent gauge state, nested boundary, finite-passive and full-squad oracle."""
import sys,json,copy,hashlib,math,importlib.util
from pathlib import Path
from datetime import datetime,timezone
from contextlib import contextmanager
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import compile_effects,run,EW
from gpu_selector import Cuda
from detail_coverage import a,body_for
from calculator.buff_manager import BuffManager
spec=importlib.util.spec_from_file_location('gauge_full_oracle',ROOT/'scripts/verify-extended-detail.py');full=importlib.util.module_from_spec(spec);spec.loader.exec_module(full)
NAMES=['리타','크라운','앨리스','모더니아','N102']
def effect(name,kind,stat,value,target='self',event='battle_start',condition=None,**kw):
 e={'name':name,'source':'스킬1','type':kind,'stat':stat,'fixed_value':value,'target':target,'trigger':{'timing':[event],'condition':condition or []}}
 if kind=='buff':e['duration']=-1
 return {**e,**kw}
def primitives():
 es=[effect('fuel start','instant','gauge_charge',7.5,gauge_id='fuel',gauge_max=10),effect('cap boost','buff','gauge_max_add',5,gauge_id='fuel',duration=2),effect('fuel recharge','instant','gauge_charge',6,event='on_attack',gauge_id='fuel'),effect('every two','buff','atk_pct',1,event='every_stack:fuel:2',max_stack=100),effect('every three','buff','crit_dmg',1,event='every_stack:fuel:3',max_stack=100),effect('boundary drain','instant','gauge_consume',1,event='every_stack:fuel:2',gauge_id='fuel'),effect('partial drain','instant','gauge_consume',4.25,event='burst_cast',gauge_id='fuel'),effect('all drain','instant','gauge_consume',-1,event='full_burst_end',gauge_id='fuel')]
 events=[(0,0,0),(0.5,7,0),(1,3,0),(2.1,7,0),(3,2,0)]
 yield 'fractional-cap-unique-boundaries-nested-drain',[(e,NAMES[0]) for e in es],events,[0,.5,1,2.1,3],['fuel']
 es=[effect('initial ammo gauge','instant','gauge_charge',4.8,gauge_id='ammo'),effect('consume as ammo','instant','gauge_consume_as_ammo',3.2,event='on_attack',gauge_id='ammo'),effect('consume remainder','instant','gauge_consume_as_ammo',-1,event='burst_cast',gauge_id='ammo')]
 observer=effect('team notification','buff','atk_pct',10,event='squad_ammo_consume:1',max_stack=100)
 yield 'consume-as-ammo-floors-each-actual-consumption',[(e,NAMES[0]) for e in es]+[(observer,NAMES[1])],[(0,0,0),(.5,7,0),(1,3,0)],[0,.5,1],['ammo']
 es=[effect('negative gauge','instant','gauge_charge',-1,gauge_id='n'),effect('up','instant','gauge_charge',3,event='on_attack',gauge_id='n'),effect('above','buff','atk_pct',10,event='passive',condition=['gauge_above:n:1']),effect('below','buff','atk_pct',20,event='passive',condition=['gauge_below:n:1']),effect('mod negative','buff','crit_dmg',30,event='burst_cast',condition=['gauge_mod:n:3:2'],duration=1),effect('equal','buff','atk_dmg_pct',40,event='full_burst_start',condition=['gauge_eq:n:2'],duration=1)]
 yield 'gauge-runtime-above-below-and-discrete-eq-mod',[(e,NAMES[0]) for e in es],[(0,0,0),(.1,3,0),(.2,7,0),(.3,1,0)],[0,.1,.2,.3,1.3],['n']
 es=[effect('private gauge','instant','gauge_charge',5,gauge_id='shared',gauge_max=5),effect('private recharge','instant','gauge_charge',2,event='on_attack',gauge_id='shared'),effect('private consume','instant','gauge_consume',-1,event='burst_cast',gauge_id='shared')]
 yield 'same-gauge-name-independent-owners',[(e,n) for n in NAMES[:2] for e in es],[(0,0,0),(0,0,1),(.5,3,0),(1,7,1)],[0,.5,1],['shared']
 es=[effect('window','buff','crit_dmg',0,event='full_burst_start'),effect('close window','instant','remove_named_buff',0,event='full_burst_end',target_effect='window'),effect('finite conditional','buff','atk_pct',50,event='passive',condition=['self_state:window'],duration=.5),effect('expired','buff','crit_dmg',10,event='event:state_end:finite conditional',max_stack=100)]
 yield 'finite-passive-state-false-start-refresh-tail-and-reactivation',[(e,NAMES[0]) for e in es],[(0,0,0),(.25,1,0),(1,2,0),(2,1,0),(3,2,0)],[0,.25,.5,.75,1,1.25,1.5,1.75,2,2.25,2.5,2.75,3,3.5,4],[]


 # Different timing families share one effect identity and activation budget.
 es=[effect('mixed counters','buff','atk_pct',3,max_stack=100,max_trigger=3)]
 es[0]['trigger']['timing']=['on_attack_count:3','burst_cast_count:2']
 yield 'multiple-timings-independent-counters-shared-budget',[(e,NAMES[0]) for e in es],[(0,0,0),(.1,7,0),(.2,7,0),(.3,3,0),(.4,7,0),(.5,3,0),(.6,3,0),(.7,7,0),(.8,7,0),(.9,7,0)],[0,.1,.2,.3,.4,.5,.6,.7,.8,.9],[]
 es=[effect('ref','buff','crit_dmg',0,max_stack=10),effect('gauge start','instant','gauge_charge',2.8,gauge_id='ref'),effect('scaled','buff','atk_pct',10,event='passive',scaling='stack_count',scaling_ref='ref'),effect('captured','buff','atk_dmg_pct',10,event='burst_cast',scaling='stack_count',scaling_ref='ref',duration=2),effect('drain','instant','gauge_consume',-1,event='full_burst_start',gauge_id='ref')]
 yield 'gauge-ref-truncation-capture-and-zero-shadows-named-stack',[(e,NAMES[0]) for e in es],[(0,0,0),(.5,3,0),(1,1,0)],[0,.5,1,2.5],['ref']


 es=[effect('periodic fuel','instant','gauge_charge',1.25,gauge_id='timer',tick_interval=.5,duration=2),effect('timer bonus','buff','atk_pct',10,event='passive',condition=['gauge_above:timer:2'])]
 yield 'periodic-gauge-fractional-values-final-tick-excluded',[(e,NAMES[0]) for e in es],[(0,0,0)],[0,.5,1,1.5,2,2.5],['timer']


 es=[effect('large gauge','instant','gauge_charge',1e16,gauge_id='large'),effect('consume exactly one','instant','gauge_consume_as_ammo',1,event='on_attack',gauge_id='large')]
 observer=effect('one notification','buff','atk_pct',10,event='squad_ammo_consume:1',max_stack=100)
 yield 'consume-amount-survives-floating-point-cancellation',[(e,NAMES[0]) for e in es]+[(observer,NAMES[1])],[(0,0,0),(.5,7,0)],[0,.5],['large']

def verify_primitives(device,module_backend='auto'):
 cases=[]
 for title,effects,events,times,gauges in primitives():
  chars=[{'name':n,'skill_levels':{'1':10,'2':10,'3':10},'_weapon':a.META[n]} for n in NAMES]
  p=compile_effects(chars,effects);bs={n:{'atk':100000,'def':1000,'hp':1000000} for n in NAMES}
  class BM(BuffManager):
   def _register_all(self):self._effects=copy.deepcopy(effects);self._build_notify_index()
  bm=BM(chars,state={'base_stats':bs,'enemy':{'def':31784,'core_px':50},'full_burst':False,'rng_acc':{},'hp':{n:1000000 for n in NAMES},'hp_pct':{n:100 for n in NAMES}})
  transcript=[];original=bm.notify
  def notify(event,t,caster,**ctx):
   if event.startswith('every_stack:'):transcript.append([event,caster,ctx['stack_value']])
   return original(event,t,caster,**ctx)
  bm.notify=notify
  script=[];expected=[];keys=['atk_pct','crit_dmg','atk_dmg_pct'];stat_indices=[0,6,10]
  for t in sorted(set(times+[row[0] for row in events])):
   bm.tick(t)
   for et,code,who in events:
    if et!=t:continue
    event={0:'battle_start',1:'full_burst_start',2:'full_burst_end',3:'burst_cast',7:'on_attack'}[code]
    if code in (1,2):bm.state['full_burst']=code==1
    bm.tick(t);bm.notify(event,t,NAMES[who]);script.append([t,0,code,who,0,-1,0,0])
   if t in times:
    for who,n in enumerate(NAMES[:2]):
     for g in gauges:
      script.append([t,2,102,who,p['states'][g],len(expected),0,0]);expected.append(([bm.state.get('gauges',{}).get(n,{}).get(g,0)], [0]))
     bm.tick(t);b=bm.get_buffs(n,'__enemy__',t);script.append([t,2,0,who,-1,len(expected),0,0]);expected.append(([b.get(k,0) for k in keys],stat_indices))
  result=run(device,[p],script,[[31784,50]],[bs],module_backend=module_backend);errors=[]
  for i,((values,indices),got) in enumerate(zip(expected,result['queries'][0])):
   for value,k in zip(values,indices):
    if not math.isclose(value,got[k],rel_tol=1e-12,abs_tol=1e-9):errors.append({'query':i,'field':k,'cpu':value,'gpu':got[k]})
  cases.append({'name':title,'passed':not errors,'queries':len(expected),'errors':errors[:20],'cpu_boundary_events':transcript,'module_backend':result['module_backend']})
  print(json.dumps({k:cases[-1][k] for k in ('name','passed','errors')},ensure_ascii=True),flush=True)
 return cases

@contextmanager
def custom_effects(effects):
 from calculator import buff_manager,timeline
 original=buff_manager.BuffManager
 class Custom(original):
  def char_effects(self,name):return copy.deepcopy(effects.get(name,[]))
 buff_manager.BuffManager=timeline.BuffManager=Custom
 try:yield
 finally:buff_manager.BuffManager=timeline.BuffManager=original

def full_scenarios():
 es=[effect('periodic gauge','instant','gauge_charge',1.25,gauge_id='heat',tick_interval=.5,duration=5),effect('gauge each attack','instant','gauge_charge',3.5,event='on_attack',gauge_id='heat',gauge_max=30),effect('cap','buff','gauge_max_add',10,gauge_id='heat',event='burst_cast',duration=3),effect('damage every ten','damage','damage',200,'target',event='every_stack:heat:10'),effect('heat bonus','buff','atk_dmg_pct',30,event='passive',condition=['gauge_above:heat:20']),effect('heat cooldown','instant','gauge_consume_as_ammo',-1,event='every:2s',gauge_id='heat')]
 yield 'autonomous-gauge-threshold-damage-consume-and-cap',{NAMES[0]:es}
 es=[effect('drain','instant','current_hp_reduce',50,event='full_burst_start'),effect('heal','instant','heal_hp_pct',100,event='full_burst_end'),effect('finite conditional','buff','atk_pct',50,event='passive',condition=['self_hp_below:90'],duration=2),effect('finite all allies','buff','atk_dmg_pct',30,'all_allies',event='passive',condition=['self_hp_below:90'],duration=1)]
 yield 'autonomous-finite-passive-hp-window',{NAMES[0]:es}
 es=[effect('small magazines','buff','max_ammo_flat',-1000,'all_allies'),effect('ammo refill','instant','ammo_charge_pct',100,'all_allies',event='every:0.5s'),effect('clear magazine','instant','ammo_charge_pct',-100,'all_allies',event='every:2s'),effect('partial refill','instant','ammo_charge_pct',50,'all_allies',event='every:0.75s'),effect('ammo callback','buff','atk_pct',10,event='event:ammo refill',max_stack=20),effect('flat refill','instant','ammo_charge_flat',2,'all_allies',event='every:1s')]
 yield 'autonomous-ammo-charges-during-reload-and-charge',{NAMES[0]:es}
 es=[effect('element bonus','buff','element_bonus_pct',30,'all_allies')]
 yield 'autonomous-element-bonus-matching-and-nonmatching',{NAMES[0]:es}
 es=[effect('short MG switch','weapon_change','',0,event='burst_cast',weapon_type='MG',damage_coeff={str(i):7 for i in range(1,11)},max_ammo=-1,duration=3)]
 yield 'autonomous-charge-to-MG-and-fresh-charge-on-return',{NAMES[2]:es}

def verify(device,module_backend='auto'):
 cases=verify_primitives(device,module_backend)
 for name,effects in full_scenarios():
  with custom_effects(effects):case=full.compare(device,name,body_for(NAMES,25),module_backend=module_backend)
  cases.append(case);print(json.dumps({'name':name,'passed':case['passed'],'cpu':case['cpu_total'],'gpu':case['gpu_total']},ensure_ascii=True),flush=True)
 sources=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','scripts/verify-gauge-detail.py']
 return {'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in cases),'device':device.name,'scope':'gauge, multi-timing, finite-passive primitives and independently simulated five-member squads','cpu_trace_used_as_gpu_input':False,'cases':cases,'source_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in sources}}
if __name__=='__main__':
 d=Cuda()
 try:r=verify(d)
 finally:d.close()
 (ROOT/'research/detail-gauge-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
