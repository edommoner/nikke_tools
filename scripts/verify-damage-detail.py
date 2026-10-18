"""Independent CPU / GPU checks for typed damage, hit references and fixed charge."""
import sys,json,copy,math,hashlib,importlib.util
from pathlib import Path
from datetime import datetime,timezone
from contextlib import contextmanager
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_gpu import compile_effects,run
from gpu_selector import Cuda
from detail_coverage import a,body_for
from calculator.buff_manager import BuffManager
from calculator.timeline import CharState
spec=importlib.util.spec_from_file_location('damage_full_oracle',ROOT/'scripts/verify-extended-detail.py');full=importlib.util.module_from_spec(spec);spec.loader.exec_module(full)
NAMES=['리타','크라운','앨리스','모더니아','N102']
def effect(name,kind,stat,value,target='self',event='battle_start',condition=None,**kw):
 e={'name':name,'source':'스킬1','type':kind,'stat':stat,'fixed_value':value,'target':target,'trigger':{'timing':[event],'condition':condition or []}}
 if kind=='buff':e['duration']=-1
 return {**e,**kw}
def primitive_scenarios():
 owner=NAMES[2]
 es=[effect('earlier entry','buff','charge_time_fixed',.2),effect('newer entry','buff','charge_time_fixed',.8,duration=.75),effect('speed ignored','buff','charge_speed_pct',95),effect('flat ignored','buff','charge_time_flat',-.9)]
 es[0]['trigger']['timing']=['battle_start','every:0.5s']
 yield 'fixed-latest-activation-then-uid-priority',[(e,owner) for e in es],[0,.25,.5,.75,1],[(2,104,0),(2,103,20),(2,103,53)]
 missing=effect('no numeric fixed','buff','charge_time_fixed',0);missing.pop('fixed_value')
 es=[(effect('foreign lock','buff','charge_time_fixed',.01,'all_allies'),NAMES[0]),(missing,owner),(effect('speed ignored','buff','charge_speed_pct',95),owner)]
 yield 'foreign-lock-and-nonnumeric-own-lock-use-own-base',es,[0,1],[(2,104,0),(2,103,20),(0,104,0)]
 yield 'zero-fixed-is-active',[(effect('instant charge','buff','charge_time_fixed',0),owner)], [0,1],[(2,104,0),(2,103,53)]
 keys=[('armor_break_dmg_pct',51,30),('armor_break_enabled',52,0),('part_dmg_pct',54,40),('intercept_dmg_pct',55,50),('burst_dmg_aoe_pct',56,60),('burst_dmg_single_pct',57,70)]
 es=[(effect(key,'buff',key,value),owner) for key,_,value in keys]+[(effect('other armor flag','buff','armor_break_enabled',0),owner)]
 yield 'extra-stats-and-boolean-presence',es,[0,1],[(2,103,index) for _,index,_ in keys]

def verify_primitives(device,module_backend='auto'):
 results=[]
 for name,effects,times,queries in primitive_scenarios():
  chars=[{'name':n,'skill_levels':{'1':10,'2':10,'3':10},'_weapon':a.META[n]} for n in NAMES];bs={n:{'atk':100000,'def':1000,'hp':1000000} for n in NAMES};p=compile_effects(chars,effects)
  class BM(BuffManager):
   def _register_all(self):self._effects=copy.deepcopy(effects);self._build_notify_index()
  bm=BM(chars,state={'base_stats':bs,'enemy':{'def':31784,'core_px':50},'full_burst':False,'rng_acc':{}});cs=[CharState(c,100000,None) for c in chars]
  script=[];expected=[]
  for who in range(5):bm.tick(0);bm.notify('battle_start',0,NAMES[who]);script.append([0,0,0,who,0,-1,0,0])
  mapping={20:'charge_speed_pct',51:'armor_break_dmg_pct',52:'armor_break_enabled',53:'charge_time_fixed',54:'part_dmg_pct',55:'intercept_dmg_pct',56:'burst_dmg_aoe_pct',57:'burst_dmg_single_pct'}
  for t in times:
   for who,event,key in queries:
    bm.tick(t);value=cs[who]._effective_charge_time(bm,t) if event==104 else float(bm.get_buffs(NAMES[who],'__enemy__',t).get(mapping[key],0))
    expected.append(value);script.append([t,2,event,who,key,len(expected)-1,0,0])
  gpu=run(device,[p],script,[[31784,50]],[bs],module_backend=module_backend);actual=[q[0] for q in gpu['queries'][0]];errors=[{'query':i,'cpu':x,'gpu':y} for i,(x,y) in enumerate(zip(expected,actual)) if not math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-9)]
  results.append({'name':name,'passed':not errors,'cpu':expected,'gpu':actual,'errors':errors,'module_backend':gpu['module_backend']});print(json.dumps({'name':name,'passed':not errors,'errors':errors},ensure_ascii=True),flush=True)
 return results

def full_scenarios():
 es=[effect('armor flag','buff','armor_break_enabled',0,'all_allies',duration=2),effect('armor amplifier','buff','armor_break_dmg_pct',80,'all_allies'),effect('def ignore','buff','def_ignore_pct',30,'all_allies'),effect('ordinary skill','damage','damage:2',100,'target',event='every:1s'),effect('armor skill','damage','armor_break_damage:2',100,'target',event='every:1s')]
 yield 'armor-normal-and-charge-toggle-versus-ordinary-skills',{NAMES[0]:es},{'def':10000000},['armor_break_damage:2','damage:2'],True
 es=[effect('armor amplifier','buff','armor_break_dmg_pct',50),effect('burst amplifier','buff','burst_dmg_pct',30),effect('aoe amplifier','buff','burst_dmg_aoe_pct',100),effect('single amplifier','buff','burst_dmg_single_pct',200)]
 for i,t in enumerate(['all_enemies','enemies_lowest_def:1','target']):es.append(effect('burst shape '+str(i),'damage','armor_break_burst_damage',100,t,event='every:1s'))
 yield 'armor-burst-combines-only-matching-shape-modifiers',{NAMES[0]:es},{'def':10000000},['armor_break_burst_damage'],False
 for parts in (False,True):
  es=[effect('all modifiers','buff','atk_dmg_pct',10),effect('sequential amplifier','buff','sequential_dmg_pct',20),effect('attachment amplifier','buff','projectile_attachment_dmg_pct',30),effect('explosion amplifier','buff','projectile_explosion_dmg_pct',40),effect('pierce amplifier','buff','pierce_dmg_pct',50),effect('part amplifier','buff','part_dmg_pct',60)]
  stats=['sequential_damage:5','projectile_attachment_damage:2','projectile_explosion_damage','pierce_damage','damage']
  for i,stat in enumerate(stats):es.append(effect('typed '+str(i),'damage',stat,100,'target',event='every:1s',hits_parts=True))
  yield 'typed-skills-parts-'+str(parts),{NAMES[0]:es},{'has_parts':parts},stats,False
 es=[effect('named fallback','buff','crit_dmg',0,max_stack=9),effect('initial gauge','instant','gauge_charge',3.8,gauge_id='shots'),effect('drain','instant','gauge_consume',-1,event='every:2s',gauge_id='shots'),effect('recharge','instant','gauge_charge',1.5,event='every:3s',gauge_id='shots'),effect('named count','damage','sequential_damage:shots',100,'target',event='on_attack_count:10'),effect('scaled count','damage','damage',100,'target',event='on_attack_count:11',scaling='stack_count',scaling_ref='shots'),effect('direct gauge count','damage','damage',100,'target',event='on_attack_count:12',hit_count_gauge_ref='shots'),effect('missing ref','damage','damage:unregistered',100,'target',event='on_attack_count:13'),effect('absent gauge','damage','damage',100,'target',event='on_attack_count:14',hit_count_gauge_ref='unregistered')]
 yield 'dynamic-hit-counts-zero-missing-and-fractional-refs',{NAMES[0]:es},{},['sequential_damage:shots','damage','damage:unregistered'],False
 es=[effect('large ref','instant','gauge_charge',5,gauge_id='shots'),effect('explicit count wins','damage','damage:2',100,'target',event='on_attack_count:10',scaling='stack_count',scaling_ref='shots')]
 yield 'numeric-hit-count-overrides-scaling-reference',{NAMES[0]:es},{},['damage:2'],False
 for final in (0,2):
  es=[effect('initial gauge','instant','gauge_charge',3,gauge_id='shots'),effect('deferred bonus','damage','bonus_damage',100,'target',event='burst_cast',scaling='stack_count',scaling_ref='shots'),effect('drain before landing','instant','gauge_consume',-1,event='burst_cast',gauge_id='shots'),effect('final gauge','instant','gauge_charge',final,event='burst_cast',gauge_id='shots'),effect('exclude later buff','buff','atk_pct',500,event='burst_cast',duration=3)]
  yield 'deferred-b3-coefficient-reference-at-landing-'+str(final),{NAMES[2]:es},{},['bonus_damage'],False
 es=[effect('permanent fixed','buff','charge_time_fixed',.2),effect('temporary fixed','buff','charge_time_fixed',.8,event='burst_cast',duration=2),effect('ignored speed','buff','charge_speed_pct',95),effect('ignored flat','buff','charge_time_flat',-.5)]
 yield 'live-fixed-charge-order-expiry-and-speed-suppression',{NAMES[2]:es},{},[],False
 for core in (0,50):
  es=[effect('core skill','damage','core_damage',100,'target',event='every:1s'),effect('core amplification','buff','core_dmg_pct',100)]
  yield 'forced-core-skill-'+str(core),{NAMES[0]:es},{'core_px':core},['core_damage'],False


 ns=[NAMES[0],'센티',NAMES[1],NAMES[3],NAMES[2]]
 es=[effect('one defender','buff','atk_pct',100,'allies_class:방어형:1'),effect('one attacker','buff','atk_dmg_pct',50,'allies_class:화력형:1'),effect('same squad','buff','crit_dmg',50,'allies_squad'),effect('named present','buff','normal_atk_dmg_pct',20,NAMES[2]),effect('named absent','buff','atk_pct',100,'하란',max_trigger=1),effect('innate burst three','buff','element_bonus_pct',20,'allies_burst3'),effect('first two','buff','core_dmg_pct',30,'allies:2')]
 yield 'static-class-limit-squad-and-named-targets',{NAMES[0]:es},{'_squad':ns},[],False
 es=[effect('code exclusion','buff','atk_pct',50,'allies_code_excl_self:철갑'),effect('weapon exclusion','buff','crit_dmg',30,'allies_weapon_excl_self:SMG'),effect('code and weapon','buff','atk_dmg_pct',40,'allies_code_weapon:철갑:MG'),effect('leftmost filtered','buff','normal_atk_dmg_pct',50,'allies_code_weapon_leftmost:철갑:MG:1')]
 yield 'static-code-weapon-intersections-and-self-exclusion',{NAMES[0]:es},{'_squad':ns},[],False
 es=[effect('heal room','buff','max_hp_only_pct',100,'all_allies'),effect('ordered heal','instant','heal_hp_pct',1,'allies_top_base_charge_time:2',event='every:1s',scaling='max_hp')]
 recipient=effect('first heal changes next base','buff','max_hp_only_pct',20,NAMES[0],event='event:heal_received',max_stack=100)
 yield 'base-charge-rank-order-preserves-synchronous-healing',{NAMES[0]:es,NAMES[2]:[recipient]},{'_squad':ns},[],False


 es=[effect('enemy attack modifier','buff','atk_caster_based_pct',-500,'target'),effect('ally attack modifier','buff','atk_caster_based_pct',20,'all_allies')]
 yield 'enemy-caster-atk-is-separated-from-outgoing-ally-atk',{NAMES[0]:es},{},[],False

@contextmanager
def custom_effects(effects):
 from calculator import buff_manager,timeline
 original=buff_manager.BuffManager;observed={'damage_stats':{},'armor_on':False,'armor_off':False,'dispatch_refs':[]}
 class Custom(original):
  def char_effects(self,name):return copy.deepcopy(effects.get(name,[]))
  def get_buffs(self,*args,**kw):
   value=super().get_buffs(*args,**kw);observed['armor_on']|=bool(value.get('armor_break_enabled'));observed['armor_off']|=not value.get('armor_break_enabled',False);return value
  def register_damage_handler(self,fn):
   def handler(eff,caster,t):
    stat=eff.get('stat');observed['damage_stats'][stat]=observed['damage_stats'].get(stat,0)+1
    if eff.get('scaling_ref'):observed['dispatch_refs'].append([round(t,6),self.ref_count(caster,eff['scaling_ref'])])
    return fn(eff,caster,t)
   return super().register_damage_handler(handler)
 buff_manager.BuffManager=timeline.BuffManager=Custom
 try:yield observed
 finally:buff_manager.BuffManager=timeline.BuffManager=original


def verify_formula_matrix(device,module_backend='auto'):
 import random
 from calculator.damage import calc_damage,default_hit_type
 from calculator.timeline import _core_hit_prob
 rng=random.Random(321604);programs=[];enemies=[];stats=[];managers=[]
 numeric=['atk_pct','atk_caster_based_pct','def_ignore_pct','crit_rate','crit_dmg','normal_atk_crit_rate','normal_atk_crit_dmg','core_dmg_pct','atk_dmg_pct','normal_atk_dmg_pct','charge_dmg_pct','charge_dmg_mag_pct','burst_dmg_pct','burst_dmg_aoe_pct','burst_dmg_single_pct','pierce_dmg_pct','armor_break_dmg_pct','dot_dmg_pct','part_dmg_pct','intercept_dmg_pct','projectile_explosion_dmg_pct','projectile_attachment_dmg_pct','sequential_dmg_pct','split_dmg_pct','element_bonus_pct','accuracy_pct']
 ns=[NAMES[2],NAMES[1],NAMES[0],NAMES[3],NAMES[4]]
 for index in range(128):
  cs=[{'name':n,'skill_levels':{'1':10,'2':10,'3':10},'_weapon':copy.deepcopy(a.META[n])} for n in ns];cs[0]['_optimal']=bool(rng.getrandbits(1)) if index>1 else False;cs[0]['_element_match']=bool(rng.getrandbits(1)) if index>1 else False
  bs={n:{'atk':rng.randrange(50000,1000000),'def':5000,'hp':1000000} for n in ns};enemy=[rng.uniform(0,100000),rng.choice([0,2,10,50])]
  effects=[(effect('matrix '+key,'buff',key,rng.uniform(0,150)),ns[0]) for key in numeric]
  effects += [(effect('def percent','buff','def_pct',-rng.uniform(0,80),'target'),ns[0]),(effect('def flat','buff','def_caster_based_pct',-rng.uniform(0,100),'target'),ns[0]),(effect('received','buff','received_dmg_pct',rng.uniform(0,100),'target'),ns[0])]
  if index<2:bs[ns[0]]['atk']=100001+index*2;enemy=[0,0];effects=[(effect('cancel default crit','buff','crit_rate',-15),ns[0])]
  p=compile_effects(cs,effects)
  class BM(BuffManager):
   def _register_all(self):self._effects=copy.deepcopy(effects);self._build_notify_index()
  bm=BM(cs,state={'base_stats':bs,'enemy':{'def':enemy[0],'core_px':enemy[1]},'full_burst':False,'rng_acc':{}});bm.notify('battle_start',0,ns[0])
  programs.append(p);stats.append(bs);enemies.append(enemy);managers.append(bm)
 variants=[(512,False,{'is_armor_break_damage':True}),(1|512|4096,False,{'is_armor_break_damage':True,'is_burst_damage':True,'is_aoe_burst':True}),(1|8192,False,{'is_burst_damage':True,'is_single_burst':True}),(64|1024,False,{'is_pierce_damage':True,'is_part':True}),(2|2048,False,{'is_sequential':True,'is_intercept':True}),(4|8,False,{'is_projectile_attachment':True,'is_projectile_explosion':True}),(32|512,True,{'is_full_charge':True,'is_armor_break_damage':True}),(256|8,True,{'is_projectile_explosion':True}),(16384,False,{'is_core_damage':True}),(16,False,{'is_split':True}),(128,False,{'is_dot':True}),(0,False,{})]
 # A common coefficient of 50 includes deterministic exact half-integer ties.
 script=[[0,0,0,0,0,-1,0,0]]
 for phase in range(2):
  if phase:script.append([1,0,1,0,0,-1,0,0])
  for j,(flags,normal,_) in enumerate(variants):script.append([phase,2,105,0,flags,phase*len(variants)+j,50,int(normal)])
 gpu=run(device,programs,script,enemies,stats,module_backend=module_backend);errors=[];checks=0
 for index,(p,bm,enemy,bs) in enumerate(zip(programs,managers,enemies,stats)):
  c=p['chars'][0];name=c['name'];w=c['_weapon'];b=bm.get_buffs(name,'__enemy__',0);b['is_element_match']=c['_element_match']
  for phase in range(2):
   for j,(flags,normal,extra) in enumerate(variants):
    core_prob=_core_hit_prob(w.get('spread_end',10)*(1-.00908*b.get('accuracy_pct',0)),enemy[1]) if normal and enemy[1]>0 else 0
    ht=default_hit_type(coeff=50,is_normal_atk=normal,is_full_burst=bool(phase),is_optimal_range=normal and c['_optimal'],is_core=(bool(enemy[1]>0) if flags&256 else bool(flags&16384)),**extra)
    if normal and not flags&256:ht['core_prob']=core_prob
    expected=calc_damage(bs[name]['atk'],b,w,ht,enemy_def=enemy[0],expected=True)['damage'];actual=gpu['queries'][index][phase*len(variants)+j][0];checks+=1
    if expected!=actual:errors.append({'program':index,'phase':phase,'flags':flags,'cpu':expected,'gpu':actual})
 result={'name':'seeded-typed-damage-formula-matrix','passed':not errors,'programs':len(programs),'integer_damage_checks':checks,'errors':errors[:20],'module_backend':gpu['module_backend']};print(json.dumps(result,ensure_ascii=True),flush=True);return result

def verify(device,module_backend='auto'):
 cases=verify_primitives(device,module_backend);cases.append(verify_formula_matrix(device,module_backend))
 for name,effects,enemy,required,toggle in full_scenarios():
  b=body_for(enemy.get('_squad',NAMES),12);b['enemy'].update({k:v for k,v in enemy.items() if k!='_squad'})
  try:
   with custom_effects(effects) as observed:
    case=full.compare(device,name,b,module_backend=module_backend);checks={stat:observed['damage_stats'].get(stat,0)>0 for stat in required}
    if toggle:checks['armor_both_states']=observed['armor_on'] and observed['armor_off']
    case['mechanics_exercised']=checks;case['cpu_observations']=copy.deepcopy(observed);case['passed'] &= all(checks.values())
  except (Exception,SystemExit) as ex:case={'name':name,'passed':False,'error':str(ex)}
  cases.append(case);print(json.dumps({'name':name,'passed':case['passed'],**({'error':case['error']} if 'error' in case else {'cpu':case['cpu_total'],'gpu':case['gpu_total'],'checks':checks})},ensure_ascii=True),flush=True)
 sources=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','scripts/verify-damage-detail.py']
 return {'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in cases),'device':device.name,'scope':'fixed charge and extra stat snapshots plus independently simulated complete five-member damage fixtures','cpu_trace_used_as_gpu_input':False,'cases':cases,'source_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in sources}}
if __name__=='__main__':
 d=Cuda()
 try:r=verify(d)
 finally:d.close()
 (ROOT/'research/detail-damage-verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if r['passed'] else 1)
