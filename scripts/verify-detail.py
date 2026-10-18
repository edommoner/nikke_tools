"""Differential oracle: real pinned effects, independent CPU BuffManager state.
Event scripts are authored stimuli, not traces captured from a CPU combat run.
The tests deliberately do not certify the unfinished autonomous full-squad GPU loop.
"""
import copy,json,sys,math,hashlib
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import engine_worker as adapter
from calculator.buff_manager import BuffManager,char_effects
from calculator.damage import calc_damage,default_hit_type
from calculator.timeline import _core_hit_prob,CharState
from detail_gpu import STAT,EVENT,compile_effects,run


def characters(names,level=10):
 return [{'name':n,'skill_levels':{'1':level,'2':level,'3':level},'_weapon':adapter.META[n]} for n in names]

def oracle(program,script,enemy,base_stats,startup_full=False,timeline_handlers=False):
 chars=program['chars'];names=[c['name'] for c in chars];effects=program['_raw_effects'];states=program['states']
 class BM(BuffManager):
  def _register_all(self):self._effects=copy.deepcopy(effects);self._build_notify_index()
 bm=BM(chars,state={'base_stats':base_stats,'enemy':{'def':enemy[0],'core_px':enemy[1]},'full_burst':False,'rng_acc':{},'rng_expected':True,'camera':set()})
 totals=[0]*5;shooters=[CharState(c,base_stats[c['name']]['atk'],None) for c in chars];shot_counts=[0]*5;auto_started=[False]*5
 if timeline_handlers:
  from calculator.timeline import _register_instant_handlers
  _register_instant_handlers(bm,dict(zip(names,shooters)),None)
 def skill(eff,owner,t):
  i=names.index(owner);b=bm.get_buffs(owner,'__enemy__',t);b['is_element_match']=chars[i].get('_element_match',False)
  lv=str(chars[i]['skill_levels'][eff['source'][-1]]);value=eff.get('fixed_value',eff.get('values',{}).get(lv,0))
  if eff.get('scaling_ref'):value*=bm.ref_count(owner,eff['scaling_ref'])
  ht=default_hit_type(coeff=value,is_normal_atk=False,is_full_burst=bm.state.get('full_burst',False),is_burst_damage=eff['stat']=='burst_damage',is_split=eff['stat']=='split_damage')
  totals[i]+=calc_damage(base_stats[owner]['atk'],b,chars[i]['_weapon'],ht,enemy_def=enemy[0],expected=True)['damage']
 bm.register_damage_handler(skill)
 out=[]
 for row in script:
  t,op,code,who,arg,index,_,_=row;who=int(who);name=names[who]
  bm.tick(t)
  if op==1:bm.tick(t)
  elif op==0:
   event=next(k for k,v in EVENT.items() if v==code)
   if event=='burst_enter':event+=':'+str(int(arg))
   elif event=='stack_reach':event+=':'+next(k for k,v in states.items() if v==arg)+':'+str(int(bm.ref_count(name,next(k for k,v in states.items() if v==arg))))
   if code==1:bm.state['full_burst']=True
   if code==2:bm.state['full_burst']=False
   bm.notify(event,t,name,core_frac=row[6],hit_crit=bool(row[7]))
  elif op==3:
   # timeline.simulate initializes each magazine after battle-start skills (line 5558).
   if startup_full and not auto_started[who]:shooters[who].ammo=shooters[who]._full_ammo(bm,t)
   auto_started[who]=True
   hits=shooters[who].tick(t,bm,{'def':enemy[0],'core_px':enemy[1],'code':None},{'rng_mode':'expected'})
   totals[who]+=sum(hit.damage for hit in hits);shot_counts[who]+=len(hits)
  elif op==2:
   if code==107:out.append([shooters[who]._reload_duration(bm,t)]+[0]*47);continue
   if code==106:
    eff,owner=bm._effects[int(arg)];acc=bm.state['rng_acc'];out.append([acc.get(('prob',id(eff),owner),0),acc.get(('not_core',id(eff),owner),0)]+[0]*46);continue
   b=bm.get_buffs(name,'__enemy__',t);values=[b.get(k,0) for k in STAT]
   values[26]=0;values[28]=float(bm.is_stunned(name));values[29]=sum(bm._get_value(ab.effect,ab,name) or 0 for ab in bm._active if ab.effect.get('stat')=='fullburst_duration' and t<ab.expires_at and name in (ab.target_chars or []))
   w=chars[who]['_weapon'];mode=bm.get_weapon_change(name)
   coeff=w['damage_coeff'];rate=w['fire_rate'];ammo=w['max_ammo']
   if mode:
    from calculator.timeline import _MECHANICS,_DELAYS,_pick
    dc=mode.get('damage_coeff',{});lv=str(chars[who]['skill_levels'][mode['source'][-1]]);coeff=dc.get(lv,dc.get('10',0)) if isinstance(dc,dict) else dc
    defaults=_MECHANICS['weapon_type_defaults'][mode.get('weapon_type','SR')];over=_DELAYS.get('_weapon_change',{}).get(name,{}).get(mode.get('name'),{});cdn_rate=(w.get('weapon_change_fire_rate') or {}).get(mode.get('source'));cdn={'fire_rate':cdn_rate} if cdn_rate else {}
    rate=float(_pick('fire_rate',over,mode,cdn,defaults,default=defaults.get('fire_rate_min',1)));ammo=mode.get('max_ammo',1)
   buff={**b,'is_element_match':chars[who].get('_element_match',False)}
   spread=shooters[who]._current_spread(buff) if auto_started[who] else w.get('spread_end',10)*(1-.00908*buff.get('accuracy_pct',0));ht=default_hit_type(coeff=coeff,is_normal_atk=True,is_full_burst=bm.state.get('full_burst',False),is_optimal_range=chars[who].get('_optimal',False),core_prob=_core_hit_prob(spread,enemy[1]) if enemy[1]>0 else 0)
   damage=calc_damage(base_stats[name]['atk'],buff,w,ht,enemy_def=enemy[0],expected=True)['damage']
   ref=next((k for k,v in states.items() if v==arg),None)
   out.append(values+[coeff,rate,ammo,float(mode is not None),damage,bm.ref_count(name,ref) or 0 if ref else 0,*totals,shot_counts[who],shooters[who].ammo,shooters[who].warmup_shots,shooters[who].next_fire_time,shooters[who].reloading_until])
 return out,totals


def program(chars,effects):
 result=compile_effects(chars,effects);result['_raw_effects']=effects;return result

def cases():
 # Full real Mast skill set: permanent condition, 3 stacks, capture, stun, removal.
 mast='마스트 : 로망틱 메이드';modernia='모더니아';others=['리타','크라운','앨리스']
 names=[mast,modernia,*others]
 output=[]
 for lv in (1,7,10):
  cs=characters(names,lv);p=program(cs,[(e,mast) for e in char_effects(mast)])
  script=[];qi=0
  def notify(t,code,who=0,arg=0):script.append([t,0,code,who,arg,-1,0,0])
  def query(t,who=0,ref=-1):
   nonlocal qi
   script.append([t,2,0,who,ref,qi,0,0]);qi+=1
  notify(0,0);query(0,ref=p['states']['취기'])
  for cycle in range(3):
   t=1+cycle*20;notify(t,4,arg=1);query(t,ref=p['states']['취기']);notify(t+.1,4,arg=3);notify(t+.2,3);query(t+.2,1)
   if cycle<2:notify(t+10,2)
  notify(42,2);query(42);query(42,1);script.append([52,1,0,0,0,-1,0,0]);query(52)
  output.append((f'mast-real-skills-lv{lv}',p,script))
 # Full real Modernia skills: hit counters, refresh/expiry, condition, weapon switch.
 for lv in (1,10):
  cs=characters([modernia,mast,*others],lv);p=program(cs,[(e,modernia) for e in char_effects(modernia)]);script=[];qi=0
  def q(t):
   nonlocal qi
   script.append([t,2,0,0,-1,qi,0,0]);qi+=1
  script.append([0,0,0,0,0,-1,0,0]);q(0)
  for hit in range(1,1002):
   t=hit/100
   if hit==100:script.append([t,0,1,0,0,-1,0,0]);script.append([t,0,3,0,0,-1,0,0]);q(t)
   script.append([t,0,8,0,0,-1,0,0])
   if hit%200==0:q(t)
  for t in (15.999,16,20.0,20.001,20.01,20.010001):script.append([t,1,0,0,0,-1,0,0]);q(t)
  output.append((f'modernia-real-skills-lv{lv}',p,script))
 # Test each actual position in squad order using the original position effects.
 for owner in ('루주','벨로타 : 펌킨 위치'):
  for pos in range(5):
   ns=[modernia,mast,*others];ns[pos]=owner;cs=characters(ns)
   eff=[e for e in char_effects(owner) if e.get('target','').startswith(('allies_adjacent:','allies_right:')) and e.get('stat') in ('atk_dmg_pct','atk_caster_based_pct')]
   p=program(cs,[(e,owner) for e in eff]);script=[[0,0,0,pos,0,-1,0,0],[1,0,1,pos,0,-1,0,0],[1,0,3,pos,0,-1,0,0]]
   for i in range(5):script.append([1,2,0,i,-1,i,0,0])
   script.append([11,1,0,0,0,-1,0,0])
   for i in range(5):script.append([11,2,0,i,-1,i+5,0,0])
   output.append((f'position-{owner}-{pos+1}',p,script))
 # Autonomous GPU shot clocks: original pinned CharState is the CPU oracle.
 for core in (0,50):
  cs=characters([modernia,mast,*others]);es=[(e,n) for n in (modernia,mast) for e in char_effects(n)];p=program(cs,es);script=[];qi=0
  for who in (0,1):script.append([0,0,0,who,0,-1,0,0])
  for frame in range(180*60):
   t=frame/60
   if frame>=3*60 and (frame-3*60)%(22*60)==0:
    for who in (0,1):script.append([t,0,4,who,1,-1,0,0]);script.append([t,0,4,who,3,-1,0,0])
    script.append([t,0,1,0,0,-1,0,0])
    if (frame-3*60)%(44*60)==0:script.append([t,0,3,0,0,-1,0,0])
    if ((frame-3*60)//(22*60)+1)%3==0:script.append([t,0,3,1,0,-1,0,0])
   if frame in {int((3+22*i+(15 if i%2==0 else 10))*60) for i in range(9)}:
    for who in (0,1):script.append([t,0,2,who,0,-1,0,0])
   for who in (0,1):script.append([t,3,0,who,0,-1,0,0])
   if True: # Compare every frame, including expiry and reload boundaries.
    for who in (0,1):script.append([t,2,0,who,-1,qi,0,0]);qi+=1
  p['_core']=core;output.append((f'autonomous-modernia-mast-180s-core{core}',p,script))
 return output

def verify(device):
 reports=[]
 for name,p,script in cases():
  bs={c['name']:{'atk':100000+i*1234,'def':1000,'hp':1000000} for i,c in enumerate(p['chars'])};enemy=[31784,p.get('_core',50)]
  expected,totals=oracle(p,script,enemy,bs);gpu=run(device,[p],script,[enemy],[bs]);actual=gpu['queries'][0]
  mismatches=[];maxerr=0
  for qi,(left,right) in enumerate(zip(expected,actual)):
   for k,(a,b) in enumerate(zip(left,right)):
    if k==26:continue # caster-based raw percent is internal; atk_flat is compared.
    err=abs(a-b);maxerr=max(maxerr,err)
    if (a!=b if k in (34,35,36,37,38,39,40,41,42,43,44) else not math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-8)):mismatches.append({'query':qi,'field':k,'cpu':a,'gpu':b})
  reports.append({'case':name,'queries':len(expected),'matched':not mismatches,'max_abs_error':maxerr,'mismatches':mismatches[:8],'total_damage_equal':gpu['totals'][0]==totals,'cpu_total_damage':totals,'gpu_total_damage':gpu['totals'][0],'gpu_ms':gpu['elapsed_ms'],'per_frame_checked':name.startswith('autonomous-'),'individual_hit_damage_exact':all(a[36]==b[36] for a,b in zip(expected,actual)),'shot_counts_exact':all(a[43]==b[43] for a,b in zip(expected,actual))})
 signature_files=['calculator/buff_manager.py','calculator/timeline.py','calculator/damage.py','data/parsed_skills.json','data/parsed_nikke.json','data/weapon_mechanics.json','data/weapon_delays.json']
 return {'scope':'real effect state, autonomous MG shooting and per-frame damage; fixed external burst commands, not autonomous full-squad burst scheduling',
  'generated_at':datetime.now(timezone.utc).isoformat(),'device':device.name,'cpu_revision':adapter.REVISION,
  'engine_files':{f:hashlib.sha256((adapter.ENGINE/f).read_bytes()).hexdigest() for f in signature_files},
  'gpu_build':json.loads((Path(__file__).resolve().parents[1]/'app/detail_effects-build.json').read_text()),
  'oracle_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  'full_squad_verified':False,'profile_growth_verified':False,'automatic_burst_scheduler_verified':False,
  'passed':all(r['matched'] and r['total_damage_equal'] for r in reports),'cases':reports}

if __name__=='__main__':
 from gpu_selector import Cuda
 device=Cuda()
 try:
  result=verify(device);print(json.dumps(result,ensure_ascii=True,indent=2));sys.exit(0 if result['passed'] else 1)
 finally:device.close()
