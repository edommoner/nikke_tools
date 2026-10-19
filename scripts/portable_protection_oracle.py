"""Invoke the actual pinned timeline landing closures after GPU readback only."""
import copy,types
import engine_worker
from calculator import timeline
from calculator.buff_manager import BuffManager
from timer_registry_cases import NAMES

def native_code(name):
 found=[]
 def walk(code):
  for x in code.co_consts:
   if isinstance(x,types.CodeType):
    if x.co_name==name:found.append(x)
    walk(x)
 walk(timeline.simulate.__code__);assert len(found)==1;return found[0]
def closure(code,values):
 def cell(x):return (lambda:x).__closure__[0]
 assert set(code.co_freevars)<=set(values),code.co_freevars
 return types.FunctionType(code,timeline.simulate.__globals__,code.co_name,None,tuple(cell(values[n]) for n in code.co_freevars))

def observe(case):
 raw=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))];allies=case.get('environment',{}).get('allies',[dict(base_hp=1000) for _ in NAMES])
 chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=dict(engine_worker.META[n])) for n in NAMES]
 events=[]
 class BM(BuffManager):
  def _register_all(self):self._effects=raw;self._build_notify_index()
  def char_effects(self,name):return [e for e,n in raw if n==name]
  def notify(self,event,t,caster,*args,**kwargs):
   if event in ('event:shield_applied','event:shield_consumed','received_hit','event:cover_hit') or event.startswith('event:state_end:'):events.append(dict(event=event,time=t,owner=NAMES.index(caster)))
   return super().notify(event,t,caster,*args,**kwargs)
 base={n:dict(atk=case.get('base_atk',[1000]*5)[i],hp=a.get('base_hp',1000),**{'def':a.get('base_defense',0)}) for i,(n,a) in enumerate(zip(NAMES,allies))}
 state=dict(base_stats=base,hp={n:a.get('hp',base[n]['hp']) for n,a in zip(NAMES,allies)},hp_pct={n:a.get('hp',base[n]['hp'])/base[n]['hp']*100 for n,a in zip(NAMES,allies)},enemy={'def':0},full_burst=False,rng_acc={},rng_expected=True)
 for field,key,default in (('cover_base_hp','base_cover_hp',2000000),('cover_max_hp','base_cover_hp',2000000),('cover_hp','cover_hp',None)):
  state[field]={n:a.get(key,a.get('base_cover_hp',2000000) if default is None else default) for n,a in zip(NAMES,allies)}
 bm=BM(chars,state=state);covered=0;selected=0
 class CS:
  def __init__(self,i):self.i=i
  def in_cover(self,t):return bool(covered&(1<<self.i))
  def cover_blocked(self,t,manager):return manager.has_live_stat(NAMES[self.i],'cover_disabled',t)
  def on_down(self,t,manager):pass
 char_states={n:CS(i) for i,n in enumerate(NAMES)}
 timeline._register_instant_handlers(bm,char_states,None)
 result=types.SimpleNamespace(squad_hits=[]);boss=types.SimpleNamespace(log_squad=lambda *a:None,note_attack=lambda *a:None)
 land_code=native_code('_land_squad');attack_code=native_code('_boss_attack')
 land=closure(land_code,dict(bm=bm,boss=boss,char_states=char_states,result=result,state=state))
 attack=closure(attack_code,dict(bm=bm,enm=state['enemy'],_land_squad=land,_attack_targets=lambda spec,t:[n for i,n in enumerate(NAMES) if selected&(1<<i)]))
 timings={0:'battle_start',7:'on_attack',8:'hit_count',18:'event:shield_applied',19:'event:full_reload',43:'event:shield_consumed',36:'event:cover_hit',32:'received_hit'}
 def summary():return [dict(shield=bm.shield_amount(n),shield_capacity=bm.shield_capacity(n),decoy=sum(ab.decoy_per_target.get(n,0) for ab in bm._active if ab.effect.get('stat')=='decoy'),decoy_capacity=bm.decoy_capacity(n),has_shield=bm.has_shield(n),has_decoy=bm.has_decoy(n)) for n in NAMES]
 queries=[]
 for t,op,event,who,arg,index,extra,extra2 in case['script']:
  bm.tick(t)
  if case.get('environment',{}).get('cover_sync',True):
   for n in NAMES:bm.sync_cover_hp(n,t)
  if op==0:bm.notify(timings[event],t,NAMES[who])
  elif op==31:
   covered=who;selected=arg;hit=types.SimpleNamespace(spec=types.SimpleNamespace(atk=extra,coeff=extra2,pierce=bool(event),debuffs=[]),pattern='authored',source='');attack(hit,t)
  elif op==2:
   queries.append(dict(protection=summary(),allies=[dict(hp=state['hp'][n],max_hp=bm.effective_max_hp(n),hp_pct=state['hp_pct'][n],defense=bm._effective_def(n),down=bm.is_down(n),received_damage=sum(hit.hp for hit in result.squad_hits if hit.target==n),received_hits=sum(hit.target==n for hit in result.squad_hits)) for n in NAMES],attack_buffs=[bm.get_buffs(n,'__enemy__',t)['atk_pct'] for n in NAMES],covers=[dict(hp=state['cover_hp'][n],max_hp=state['cover_max_hp'][n],effective_max_hp=bm.cover_max_hp(n,t)) for n in NAMES]))
  else:raise ValueError('Unsupported protection stimulus')
 carriers=[]
 for ab in bm._active:
  definition=next(i for i,(e,_) in enumerate(raw) if e is ab.effect);kind=1 if ab.effect.get('stat') in ('shield_from_max_hp_pct','shared_shield_from_max_hp_pct') else 2 if ab.effect.get('stat')=='decoy' else 0
  current=ab.shield_per_target if kind==1 else ab.decoy_per_target if kind==2 else {};capacity=ab.shield_max_per_target if kind==1 else ab.decoy_max_per_target if kind==2 else {}
  protection=dict(kind=kind,current={str(NAMES.index(n)):v for n,v in current.items()},capacity={str(NAMES.index(n)):v for n,v in capacity.items()}) if current or capacity else {}
  carriers.append(dict(definition=definition,effect=ab.effect['name'],recipients=sum(1<<NAMES.index(n) for n in set(ab.target_chars or [])),stacks=ab.stack,lazy_pending=ab.target_chars is None,activated=ab.activated_at,end=1e30 if ab.expires_at==float('inf') else ab.expires_at,protection=protection))
  if any(isinstance(e.get('target'),list) for e in case['effects']):carriers[-1]['recipient_order']=[NAMES.index(n) for n in ab.target_chars or []]
 return dict(queries=queries,carriers=carriers,protection=summary(),events=events,hits=[dict(time=h.t,owner=NAMES.index(h.target),damage=h.damage,shield=h.shield,cover=h.cover,decoy=h.decoy,hp=h.hp,hp_after=h.hp_after,down=h.down,pierce=h.pierce) for h in result.squad_hits],native_landing_code_sha256=__import__('hashlib').sha256(land_code.co_code).hexdigest())

def compare(case,gpu,contains):
 cpu=observe(case);contains(gpu['queries'],cpu['queries'],case['name']+'.native');contains(gpu['protection'],cpu['protection'],case['name']+'.final')
 active=[c for c in gpu['carriers'] if c['active']];assert len(active)==len(cpu['carriers']),(case['name'],'carrier count',len(active),len(cpu['carriers']));contains(active,cpu['carriers'],case['name']+'.carriers')
 if 'protection_hits' in gpu:
  assert len(gpu['protection_hits'])==len(cpu['hits']),(case['name'],'hit count')
  contains(gpu['protection_hits'],cpu['hits'],case['name']+'.hits')
 return cpu
