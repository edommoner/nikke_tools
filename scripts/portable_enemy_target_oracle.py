"""Run the pinned native target,attack and landing closures on authored stimuli."""
import copy,hashlib,importlib.util,types
from pathlib import Path
import engine_worker
from calculator import timeline
from calculator.boss_pattern import _target_rule
from calculator.buff_manager import BuffManager
from portable_protection_oracle import native_code,closure
from portable_weapon_oracle import authored_weapon,authored_weapon_state
from timer_registry_cases import NAMES
from portable_target_rng_oracle import Observer
from portable_enemy_target_specs import normalize_seed

class ObservedRNG(Observer):
 def sample(self,*a,**kw):self.samples+=1;return super().sample(*a,**kw)

def observe(case):
 effects=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))];allies=case.get('environment',{}).get('allies',[{} for _ in NAMES]);attack_base=case.get('base_atk',[1000]*5)
 chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(engine_worker.META[n])) for n in NAMES]
 trace=[];events=[];selection_context={}
 class BM(BuffManager):
  def _register_all(self):self._effects=effects;self._build_notify_index()
  def char_effects(self,name):return [e for e,n in effects if n==name]
  def taunters(self,t):
   value=super().taunters(t)
   if selection_context.get('active'):selection_context['taunters']=list(value)
   return value
  def has_live_stat(self,name,stat,t):
   value=super().has_live_stat(name,stat,t)
   if stat=='stealth' and selection_context.get('active'):selection_context['stealth'].append((name,value))
   return value
  def notify(self,event,t,caster,*a,**kw):
   if event in ('received_hit','event:cover_hit','event:self_down','event:ally_down'):events.append(dict(event=event,time=t,owner=NAMES.index(caster)))
   return super().notify(event,t,caster,*a,**kw)
 base={n:dict(atk=attack_base[i],hp=a.get('base_hp',1000000),**{'def':a.get('base_defense',0)}) for i,(n,a) in enumerate(zip(NAMES,allies))}
 state=dict(base_stats=base,hp={n:a.get('hp',base[n]['hp']) for n,a in zip(NAMES,allies)},hp_pct={n:a.get('hp',base[n]['hp'])/base[n]['hp']*100 for n,a in zip(NAMES,allies)},enemy={'def':case['combat']['targets'][0].get('defense',0),'core_px':0,'code':None,'optimal_range_weapons':[]},full_burst=False,rng_acc={},rng_expected=True,camera=set())
 for field,key in [('cover_base_hp','base_cover_hp'),('cover_max_hp','base_cover_hp'),('cover_hp','cover_hp')]:state[field]={n:a.get(key,a.get('base_cover_hp',2000000)) for n,a in zip(NAMES,allies)}
 bm=BM(chars,state=state);states={}
 for i,(c,w) in enumerate(zip(chars,case['combat']['weapons'])):
  authored_weapon(c,w);states[NAMES[i]]=authored_weapon_state(c,w,attack_base[i]);states[NAMES[i]].ammo=states[NAMES[i]]._full_ammo(bm,0)
 timeline._register_instant_handlers(bm,states,None)
 rng=ObservedRNG(normalize_seed(case.get('enemy_targeting',{}).get('seed',0))); result=types.SimpleNamespace(squad_hits=[]);boss=types.SimpleNamespace(log_squad=lambda *a:None,note_attack=lambda *a:None)
 target_code=native_code('_attack_targets');target=closure(target_code,dict(bm=bm,boss_rng=rng,squad_order=list(NAMES)))
 land_code=native_code('_land_squad');land=closure(land_code,dict(bm=bm,boss=boss,char_states=states,result=result,state=state))
 def tracked(spec,t):
  before=rng.draws;selection_context.clear();selection_context.update(active=True,taunters=[],stealth=[])
  selected=target(spec,t);selection_context['active']=False
  count=len(spec.slots) if spec.rule=='slot' else spec.n
  taunters=selection_context['taunters'][:count]
  candidates=selection_context['stealth'];pool=[n for n,hidden in candidates if not hidden] or [n for n,_ in candidates]
  packed=sum((NAMES.index(n)+1)<<(3*i) for i,n in enumerate(selected))
  trace.append(dict(step=current_step,mask=sum(1<<NAMES.index(n) for n in selected),order=packed,targets=[NAMES.index(n) for n in selected],taunt_mask=sum(1<<NAMES.index(n) for n in taunters),pool_mask=sum(1<<NAMES.index(n) for n in pool),draws_before=before,draws_after=rng.draws,rejects_after=rng.rejects,valid=1))
  return selected
 attack_code=native_code('_boss_attack');attack=closure(attack_code,dict(bm=bm,enm=state['enemy'],_land_squad=land,_attack_targets=tracked))
 def summary():return [dict(shield=bm.shield_amount(n),shield_capacity=bm.shield_capacity(n),decoy=sum(a.decoy_per_target.get(n,0) for a in bm._active if a.effect.get('stat')=='decoy'),decoy_capacity=bm.decoy_capacity(n),has_shield=bm.has_shield(n),has_decoy=bm.has_decoy(n)) for n in NAMES]
 queries=[];started=False;total=[0]*5;shots=[0]*5
 for current_step,cmd in enumerate(case['script']):
  t,op,event,who,arg,index,extra,extra2=cmd
  if op==4 and not started:
   for n in NAMES:bm.notify('battle_start',t,n)
   for n in NAMES:states[n].ammo=states[n]._full_ammo(bm,t)
   started=True
  bm.tick(t)
  if case.get('environment',{}).get('cover_sync',True):
   for n in NAMES:bm.sync_cover_hp(n,t)
  if op==4:
   for i,w in enumerate(case['combat']['weapons']):
    if w.get('enabled',False) and not bm.is_down(NAMES[i]):
     hits=states[NAMES[i]].tick(t,bm,state['enemy'],{'rng_mode':'expected'});total[i]+=sum(h.damage for h in hits);shots[i]+=int(bool(hits))
  elif op==0:bm.notify({0:'battle_start',7:'on_attack',8:'hit_count',17:'event:cover_healed',19:'event:full_reload',32:'received_hit'}[event],t,NAMES[who])
  elif op==32:
   assert who==0 and arg==0 and index==-1
   raw=case['enemy_targeting']['attacks'].get(str(current_step),case['enemy_targeting']['attacks'].get(current_step));rule=_target_rule(raw,'native-target-input',5)
   spec=types.SimpleNamespace(**{k:rule[k] for k in ('rule','n','slots','ignore_taunt')},atk=extra,coeff=extra2,pierce=bool(event),debuffs=[])
   attack(types.SimpleNamespace(spec=spec,pattern='authored',source=''),t)
  elif op==22:bm.drop_enemies(['__enemy__' if arg==0 else f'__enemy__:add#{arg}'],t)
  elif op==2:
   queries.append(dict(damage=list(total),allies=[dict(hp=state['hp'][n],max_hp=bm.effective_max_hp(n),hp_pct=state['hp_pct'][n],defense=bm._effective_def(n),down=bm.is_down(n),received_damage=sum(h.hp for h in result.squad_hits if h.target==n),received_hits=sum(h.target==n for h in result.squad_hits)) for n in NAMES],protection=summary(),covers=[dict(hp=state['cover_hp'][n],max_hp=state['cover_max_hp'][n],effective_max_hp=bm.cover_max_hp(n,t)) for n in NAMES]))
  else:raise ValueError('Unsupported native target stimulus')
 native_state=rng.getstate()[1]
 return dict(queries=queries,selection=trace,protection=summary(),events=events,hits=[dict(time=h.t,owner=NAMES.index(h.target),damage=h.damage,shield=h.shield,cover=h.cover,decoy=h.decoy,hp=h.hp,hp_after=h.hp_after,down=h.down,pierce=h.pierce) for h in result.squad_hits],rng=dict(index=native_state[-1],state=list(native_state[:-1]),draws=rng.draws,rejects=rng.rejects,samples=rng.samples),native_target_code_sha256=hashlib.sha256(target_code.co_code).hexdigest(),native_attack_code_sha256=hashlib.sha256(attack_code.co_code).hexdigest(),native_landing_code_sha256=hashlib.sha256(land_code.co_code).hexdigest())

def compare(case,gpu,contains):
 native=observe(case)
 assert len(gpu['queries'])==len(native['queries']),case['name']
 contains(gpu['queries'],native['queries'],case['name']+'.native-victim-state')
 assert len(gpu['protection_hits'])==len(native['hits']),case['name']
 contains(gpu['protection_hits'],native['hits'],case['name']+'.native-hit-order')
 assert gpu['enemy_selection']==native['selection'],(case['name'],'victim order/consumption')
 assert gpu['enemy_rng']==native['rng'],(case['name'],'full RNG state')
 if case['name'].startswith('enemy-long-rng-'):assert native['rng']['draws']==627 and native['rng']['index']==3
 if case['name']=='enemy-source-time-between-frames':assert [row['targets'] for row in native['selection']]==[[0],[1]]
 return native
