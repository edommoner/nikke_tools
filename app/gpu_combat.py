"""CUDA combat prefilter. Independent approximate timeline, never a final damage score.
CPU prepares growth/effect bytecode only; no upstream execute()/simulate() is used.
Unsupported effects are returned individually. The CPU engine rechecks the shortlist.
"""
from __future__ import annotations
import array,ctypes as C,math,re,time
from pathlib import Path
CS,ES,NS,ME=44,12,24,160
from effect_spec import COARSE_STAT as STAT
ELEMENT={'전격':'수냉','수냉':'작열','작열':'풍압','풍압':'철갑','철갑':'전격'}
EVENT={'passive':0,'battle_start':0,'event:enemy_spawn':0,'full_burst_start':1,'full_burst_end':2,'burst_cast':3,'last_bullet':7,'reload_end':8,'full_charge_fire':9,'full_charge_hit':9}
DAMAGE={'bonus_damage':0,'burst_damage':1,'projectile_attachment_damage':4,'projectile_explosion_damage':8,'damage':0}

def compile_run(run,stats,body):
 from calculator.buff_manager import BuffManager
 from calculator.timeline import CharState,DEFAULT_ENEMY
 enemy={**DEFAULT_ENEMY,**(run.enemy or {})};chars=[];issues=[];rows=[]
 names=[c['name'] for c in run.squad];by_name={c['name']:c for c in run.squad}
 attacks=[stats(c)['atk'] for c in run.squad]
 for i,c in enumerate(run.squad):
  st=CharState(c,attacks[i],enemy['code']);w=st.weapon
  lo,hi=w.get('optimal_range',[0,0]);distance=enemy.get('distance')
  optimal=float(lo<=distance<=hi) if distance is not None else float(st.weapon_type in enemy.get('optimal_range_weapons',[]))
  try:stage=int(st.burst_stage)
  except (ValueError,TypeError):stage=0;issues.append({'character':c['name'],'effect':'burst_stage','reason':'複数段階・特殊バーストは概算未対応'})
  chars.extend([attacks[i],w['damage_coeff'],w['max_ammo'],w['reload_time']*st.clip_count,st.fire_rate,st.fire_rate_max or st.fire_rate,st.warmup_bullets,st.charge_time_base,st.post_fire_delay,w.get('full_charge_mult',100),st.pellets,st.muzzles,w.get('core_dmg_mult',200),st.spread_end,optimal,float(ELEMENT.get(w.get('element_code'))==enemy['code']),stage,w['burst_cooldown'],c.get('burst_regen_time',2),st._min_fire_cycle])
 bm=BuffManager(run.squad)
 def fail(c,e,reason):issues.append({'character':c,'effect':e.get('name',e.get('stat','?')),'reason':reason})
 for effect,owner in bm._effects:
  e=effect;i=names.index(owner);c=by_name[owner];stat=e.get('stat','');kind=e.get('type');trigger=e.get('trigger',{});cond=trigger.get('condition',[])
  # Fail closed: omit the whole effect if any semantics would be lost.
  allowed_keys={'source','type','name','trigger','target','stat','polarity','values','fixed_value','duration','duration_values','max_stack','favorite','note','trigger_values','_source_tag','_quant_group'}
  if set(e)-allowed_keys:fail(owner,e,'特殊な効果指定: '+', '.join(sorted(set(e)-allowed_keys)));continue
  if any(x not in ('during_full_burst','not_during_full_burst') for x in cond):fail(owner,e,'未対応条件: '+', '.join(cond));continue
  if len(set(cond))>1:fail(owner,e,'複合条件');continue
  target=e.get('target');mask=0
  if stat in ('received_dmg_pct','enemy_def_down_pct','enemy_def_down_flat') and target!='target':
   fail(owner,e,'味方への被ダメージ・防御効果は概算の攻撃ダメージに算入しません');continue
  if target=='self':mask=1<<i
  elif target=='all_allies':mask=31
  elif re.fullmatch(r'allies_top_atk:[1-5]',target or ''):
   count=int(target.rsplit(':',1)[1]);mask=sum(1<<j for j in sorted(range(5),key=lambda j:(-attacks[j],j))[:count])
   fail(owner,e,'対象の攻撃力順位は戦闘開始時に固定する概算')
  elif target=='target' or (target or '').startswith('enemies_'):
   if kind=='buff' and stat not in ('received_dmg_pct','enemy_def_down_pct','enemy_def_down_flat'):fail(owner,e,'敵対象バフ');continue
   mask=31
  else:fail(owner,e,'未対応対象: '+str(target));continue
  lv=str(c.get('skill_levels',{}).get(e.get('source','')[-1:],c.get('skill_level',10)))
  value=e.get('fixed_value',e.get('values',{}).get(lv,0))
  duration=e.get('duration_values',{}).get(lv,e.get('duration',-1));duration=-1 if duration is None else duration;max_stack=e.get('max_stack',1)
  if kind=='buff' and stat in STAT and value==0:continue
  flags=0;nhits=1
  if kind=='buff' and stat in STAT:sk=STAT[stat];kt=0
  elif kind=='damage' and (stat in DAMAGE or re.fullmatch(r'sequential_damage:\d+',stat)):
   sk=0;kt=1;flags=DAMAGE.get(stat,2)
   if stat.startswith('sequential_damage:'):nhits=int(stat.rsplit(':',1)[1])
  elif kind=='instant' and stat=='burst_cooldown_reduce' and not cond and all(t in ('full_burst_start','burst_cast') for t in trigger.get('timing',[])):sk=0;kt=2
  else:fail(owner,e,'未対応の効果種別: '+str(kind)+' / '+stat);continue
  timings=trigger.get('timing',[]);compiled=[];bad=False
  for timing in timings:
   ev=EVENT.get(timing);arg=0
   pattern=re.fullmatch(r'(every|on_attack_count|hit_count|squad_ammo_consume):(.+)',timing)
   if pattern:
    typ,v=pattern.groups();v=v.replace('{0}',str(e.get('trigger_values',{}).get(lv,0)))
    try:arg=float(v.removesuffix('s'))
    except ValueError:bad=True;break
    ev={'every':4,'on_attack_count':5,'hit_count':6,'squad_ammo_consume':10}[typ]
    if arg<=0 or ev!=4 and not arg.is_integer():bad=True;break
   if ev is None or ev==0 and cond:bad=True;break
   compiled.append([i,mask,sk,kt,ev,arg,value,duration,max(1,max_stack),1 if 'during_full_burst' in cond else 2 if cond else 0,flags,nhits])
  if bad or not compiled:fail(owner,e,'未対応タイミング: '+', '.join(timings));continue
  if len({r[4] for r in compiled})>1:fail(owner,e,'複数タイミングを共有する効果状態は未対応');continue
  # OR aliases for battle-start/passive must not duplicate an effect.
  unique=[]
  for row in compiled:
   if row not in unique:unique.append(row)
  rows.extend(unique)
 # Fold unconditional, permanent single-stack buffs once, avoiding per-shot scans.
 base=[[0.0]*NS for _ in range(5)];dynamic=[]
 for row in rows:
  if row[3]==0 and row[4]==0 and row[7]<0 and row[8]==1 and row[9]==0:
   for i in range(5):
    if int(row[1])&(1<<i):base[i][int(row[2])]+=row[6]
  else:dynamic.append(row)
 rows=dynamic
 chars=[v for i in range(5) for v in chars[i*20:(i+1)*20]+base[i]]
 if len(rows)>ME:raise ValueError('GPU概算の効果数上限を超えました。CPUを選択してください。')
 if body.get('burst_policy','auto')=='rules':issues.append({'character':'部隊','effect':'バースト運用','reason':'キャラ別ルールは詳細計算で適用。概算は通常オート'})
 if body.get('burst_gauge_mode','fixed')=='accumulate':issues.append({'character':'部隊','effect':'バーストゲージ','reason':'実蓄積ゲージは詳細計算で適用。探索の概算には反映されません。'})
 if body.get('shooting_policy','auto')=='character':issues.append({'character':'部隊','effect':'射撃運用','reason':'保持・短押し等の既定操作は詳細計算で適用。探索の概算は完全オート'})
 mast=names.index('마스트 : 로망틱 메이드')+1 if body.get('burst_policy')=='mast3' and '마스트 : 로망틱 메이드' in names else 0
 return {'chars':chars,'effects':rows,'enemy':[body.get('duration',180),enemy['def'],enemy.get('core_px',0),enemy.get('distance',0) or 0,mast],'issues':issues,'names':names}

class Combat:
 def __init__(self,device):
  self.device=device;self.module=C.c_void_p();self.function=C.c_void_p()
  ptx=(Path(__file__).parent/'combat.ptx').read_bytes()+b'\0'
  device.call('cuModuleLoadData',C.byref(self.module),C.cast(C.c_char_p(ptx),C.c_void_p))
  device.call('cuModuleGetFunction',C.byref(self.function),self.module,b'combat')
 def run(self,models):
  if not 1<=len(models)<=2048:raise ValueError('GPU combat batch must contain 1..2048 squads')
  # Prepared models are internal, but validate before allowing indexed GPU reads.
  for m in models:
   if len(m['chars'])!=5*CS or len(m['enemy'])!=5 or len(m['effects'])>ME:raise ValueError('Invalid GPU combat layout')
   if any(len(row)!=ES or not 0<=row[0]<5 or not 0<=row[2]<NS or row[4] in (5,6,10) and row[5]<1 for row in m['effects']):raise ValueError('Invalid GPU combat effect')
   if not all(math.isfinite(x) for x in m['chars']+m['enemy']+[v for row in m['effects'] for v in row]):raise ValueError('Non-finite GPU input')
  d=self.device;before=len(d.buffers);started=time.perf_counter()
  try:
   inputs=[array.array('d',(x for m in models for x in m['chars'])),array.array('d',(x for m in models for row in (m['effects']+[[0]*ES]*(ME-len(m['effects']))) for x in row)),array.array('i',(len(m['effects']) for m in models)),array.array('d',(x for m in models for x in m['enemy']))]
   output=array.array('d',[0])*(len(models)*7);ptrs=[d.upload(a) for a in inputs]+[d.upload(output)];args=[*ptrs,C.c_int(len(models))]
   params=(C.c_void_p*len(args))(*(C.cast(C.byref(a),C.c_void_p) for a in args))
   launch=time.perf_counter();d.call('cuLaunchKernel',self.function,(len(models)+63)//64,1,1,64,1,1,0,None,params,None);d.call('cuCtxSynchronize');kernel_ms=(time.perf_counter()-launch)*1000
   target=(C.c_char*(len(output)*8)).from_buffer(output);d.call('cuMemcpyDtoH_v2',C.cast(target,C.c_void_p),ptrs[-1],len(output)*8)
   results=[]
   for i,m in enumerate(models):
    values=output[i*7:i*7+7]
    if not all(math.isfinite(v) and 0<=v<=2**53 for v in values):raise RuntimeError('GPU combat produced invalid output')
    results.append({'squad':m['names'],'damage':int(sum(values[:5])),'members':[int(v) for v in values[:5]],'shots':int(values[5]),'cycles':int(values[6])})
   return {'scores':results,'backend':'cuda','model':'combat-prefilter-v1','approximate':True,'device':d.name,'kernel_ms':round(kernel_ms,3),'transfer_compute_ms':round((time.perf_counter()-started)*1000,3)}
  finally:
   for ptr in d.buffers[before:]:d.call('cuMemFree_v2',ptr)
   del d.buffers[before:]

def prefilter(body,device,combat=None):
 from engine_worker import evaluate
 started=time.perf_counter();squads=body.get('squads',[])
 if not isinstance(squads,list) or not 1<=len(squads)<=2048:raise ValueError('GPU概算は1〜2048候補です。')
 models=[];indices=[];errors=[];issues={}
 for i,squad in enumerate(squads):
  evaluation={**body['evaluation'],'squad':squad,'_compile_gpu':True}
  evaluation['stat_deltas']={k:v for k,v in evaluation.get('stat_deltas',{}).items() if k in squad}
  try:m=evaluate(evaluation)
  except (Exception,SystemExit) as error:errors.append({'index':i,'error':str(error)});continue
  models.append(m);indices.append(i)
  for issue in m['issues']:issues[(issue['character'],issue['effect'],issue['reason'])]=issue
 if not models:raise ValueError('GPU概算で計算できる候補がありません。')
 prepare_ms=(time.perf_counter()-started)*1000
 result=(combat or Combat(device)).run(models)
 for score,i in zip(result['scores'],indices):score['index']=i
 result.update(issues=list(issues.values()),errors=errors,prepare_ms=round(prepare_ms,3),elapsed_ms=round((time.perf_counter()-started)*1000,3),candidates=len(squads),frames=sum(int(m['enemy'][0]*60)*5 for m in models))
 return result
