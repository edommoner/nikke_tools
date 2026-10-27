"""Observe full native simulate, including its actual boss/weapon/frame ordering."""
import copy,sys,struct
from contextlib import nullcontext,ExitStack
from unittest.mock import patch
import engine_worker
from calculator import timeline,buff_manager
from enemy_target_native import ObservedRNG
from timer_registry_cases import NAMES
from world_schedule_native import cleared_run
from world_authored_roster import skill_levels

def roster_names(case):
 names=case.get('names',NAMES)
 if not isinstance(names,(list,tuple)) or len(names)!=5 or len(set(names))!=5 or any(n not in timeline._NIKKE for n in names):raise ValueError('Five distinct native roster names required')
 return list(names)

def authored_metadata(case):
 """Literal weapon normalization only;does not tick a character or a battle."""
 names=roster_names(case);metadata={}
 for n,w in zip(names,case['combat']['weapons']):
  rate=w.get('rate',1/w['interval']);maximum=w.get('rate_max',rate)
  metadata[n]=dict(timeline._NIKKE[n],weapon_type=w.get('base_weapon_type','MG' if w.get('mode')=='auto_warmup' else 'AR'),is_charge=w.get('mode')=='charge',input_type='DOWN_Charge' if w.get('mode')=='charge' else 'DOWN',burst_stage=str(w.get('stage',0)),fire_rate=rate,fire_rate_max=maximum,damage_coeff=w.get('coefficient',100),max_ammo=w['capacity'],reload_time=w['reload'],burst_energy=w.get('gauge',0),muzzles=w.get('muzzles',1),pellets=w.get('pellets',1),core_dmg_mult=200)
  if 'warmup' in w:metadata[n]['fire_rate_change_pershot']=(maximum-rate)/w['warmup']
  if case.get('burst_controls') and w.get('stage')==4:metadata[n]['burst_stage']='A'
  if w.get('mode')=='charge':metadata[n].update(charge_time=w.get('charge',.2),full_charge_mult=w.get('full_charge_mult',100),fire_stance_hold=None)
 for n in names:metadata[n].update(copy.deepcopy(case.get('weapon_metadata',{})))
 if case.get('element_codes'):
  for n,code in zip(names,case['element_codes']):metadata[n]['element_code']=code
 return metadata

def observe(case):
 NAMES=roster_names(case);levels=skill_levels(case)
 capture={};ends=[];counts={n:0 for n in NAMES};effects=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case['owners'])]
 bits=lambda v:list(struct.unpack('<II',struct.pack('<d',float(v))))
 original_char=timeline.CharState;original_burst=timeline.BurstController;original_boss=timeline.BossScript
 class Character(original_char):
  def tick(self,*args,**kwargs):
   hits=super().tick(*args,**kwargs);counts[self.name]+=int(bool(hits));capture.setdefault('characters',{})[self.name]=self;return hits
 class PendingList(list):
  def append(self,value):
   capture['pending_enqueued']=capture.get('pending_enqueued',0)+1;return super().append(value)
 class Controller(original_burst):
  def __init__(self,*args,**kwargs):
   super().__init__(*args,**kwargs)
   if case.get('observe_pending_skills'):
    capture['burst_controller']=self;self._pending_burst_dmg=PendingList(self._pending_burst_dmg)
  def _fire_pending_burst_dmg(self,t,bm):
   if case.get('observe_pending_skills'):capture['pending_fired']=capture.get('pending_fired',0)+len(self._pending_burst_dmg)
   return super()._fire_pending_burst_dmg(t,bm)
  def tick(self,t,bm,state):capture.update(bm=bm,state=state,time=t);return super().tick(t,bm,state)
 class Boss(original_boss):
  def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);capture['boss']=self;capture['actor_notices']=[0]*4;capture['actor_deaths']=0
  def begin_frame(self,t,enemy):
   if case.get('observe_actor_pools') and getattr(self,'_nikke_world_frame_time',None)!=t:
    from calculator.boss_pattern import BOSS_EVENTS
    for event in self._carry:capture['actor_notices'][BOSS_EVENTS.index(event)]+=1
   return super().begin_frame(t,enemy)
  def _destroy(self,run,target,t):
   if case.get('observe_actor_pools'):capture['actor_deaths']+=1
   return super()._destroy(run,target,t)
  def _retire(self,run,add,why,t,events,log=True):
   if case.get('observe_actor_pools') and why!='퇴장':capture['actor_deaths']+=1
   return super()._retire(run,add,why,t,events,log)
  def finish(self,t):
   if case.get('observe_fractional_hits'):
    from world_fraction_native import accumulators
    capture['fractional_accumulators']=accumulators(capture['bm'],NAMES)
   if case.get('observe_periodic_skills'):
    from world_periodic_native import before_finish as periodic_before_finish
    capture['periodic_runtime']=periodic_before_finish(self,capture['bm'],NAMES)
   if case.get('observe_target_counters'):
    from world_target_counter_battle_native import before_finish as counter_before_finish
    capture['target_counters']=counter_before_finish(capture['bm'],capture,NAMES)
   if case.get('observe_enemy_attack_fields'):
    from world_actor_pool_native import actor_bindings
    capture['enemy_attack_fields']=[dict(kind=int(b.kind),identity=b.identity,flat=0 if int(b.kind)==6 else capture['bm'].enemy_atk_down_flat('__enemy__' if int(b.kind)==1 else b.label,t)) for b in actor_bindings(self)]
   if case.get('observe_enemy_fields'):
    from world_actor_fields_native import observe_before_finish
    capture['enemy_fields']=observe_before_finish(case,self,capture['bm'],NAMES,t)
   if case.get('observe_named_state'):
    from world_actor_state_native import before_finish
    capture['named_state']=before_finish(case,self,capture['bm'],NAMES,t)
   if case.get('observe_healing_storage'):
    from world_healing_storage_native import before_finish
    capture['healing_storage']=before_finish(capture['bm'],NAMES)
   if case.get('observe_base_copies'):
    from world_base_copy_native import before_finish
    capture['base_copies']=before_finish(capture['bm'],NAMES)
   if case.get('observe_skill_critical'):
    from world_skill_critical_native import before_finish
    capture['skill_critical']=before_finish(capture['bm'],NAMES)
   if case.get('observe_skill_clocks'):
    manager=capture['bm']
    capture['skill_clocks']=[dict(row=effect['_portable_observer_row'],due=manager._next_fire[id(effect)][0],interval=manager._next_fire[id(effect)][1])
      for effect,_ in manager._effects if id(effect) in manager._next_fire]
   return super().finish(t)
  def _close(self,run,t,outcome,events):
   super()._close(run,t,outcome,events);ends.append([run.p.idx,{'cleared':1,'expired':2,'followed':3,'end':4}[outcome],*bits(t)])
 def register(bm):
  bm._effects=copy.deepcopy(effects);bm._build_notify_index()
  if case.get('observe_periodic_skills') or case.get('observe_healing_storage') or case.get('observe_skill_clocks') or case.get('source_effect_identity'):
   for index,(effect,_) in enumerate(bm._effects):effect['_portable_observer_row']=index
  if case.get('observe_authored_effect_lookup'):
   # The authored roster replaces registration, so native ordered lookups
   # must see that same literal catalog rather than original character data.
   bm._char_effects_cache={name:[e for e,owner in bm._effects if owner==name] for name in NAMES}
  if case.get('observe_target_counters'):
   from world_target_counter_battle_native import initialize
   initialize(bm,capture)
 original_run=case.get('original_run')
 metadata={} if original_run is not None else authored_metadata(case)
 def stats(char):
  i=NAMES.index(char['name']);a=case['environment']['allies'][i]
  return {'atk':case['base_atk'][i],'hp':a['base_hp'],'def':a['base_defense']}
 enemy={'def':0,'code':None,'core_px':0,'optimal_range_weapons':[],'patterns':copy.deepcopy(case['patterns'])}
 enemy.update(copy.deepcopy(case.get('enemy',{})))
 counter_observer=nullcontext()
 if case.get('observe_target_counters'):
  from world_target_counter_battle_native import observe_events
  counter_observer=observe_events(capture,NAMES)
 spawn_observer=nullcontext()
 if case.get('observe_enemy_spawn'):
  from world_spawn_native import observe_notifications
  spawn_observer=observe_notifications(capture,NAMES)
 fractional_observer=nullcontext()
 if case.get('observe_fractional_hits'):
  from world_fraction_native import observe_fractional
  fractional_observer=observe_fractional(capture,NAMES)
 previous_profile=sys.getprofile()
 def periodic_profile(frame,event,arg):
  if previous_profile is not None:previous_profile(frame,event,arg)
  if event!='return' or frame.f_code.co_name!='__init__':return
  carrier=frame.f_locals.get('self');ids=capture.get('counter_uid_order')
  if ids is None or not isinstance(carrier,buff_manager.ActiveBuff):return
  effect=getattr(carrier,'effect',{})
  if effect.get('_portable_observer_row') is not None and effect.get('type')=='damage' and effect.get('tick_interval'):
   uid=carrier.uid
   if uid not in ids:ids[uid]=len(ids)+1
 with counter_observer,spawn_observer,fractional_observer,patch.object(timeline,'CharState',Character),patch.object(timeline,'BurstController',Controller),patch.object(timeline,'BossScript',Boss),patch.object(timeline.random,'Random',ObservedRNG),ExitStack() as context:
  if original_run is None:
   for item in (patch.dict(timeline._NIKKE,metadata),patch.dict(buff_manager._NIKKE,metadata),patch.object(timeline,'calc_base_stats',stats),patch.object(buff_manager.BuffManager,'_register_all',register),patch.dict(timeline._DELAYS['_exceptions'],{},clear=True),patch.dict(timeline._DELAYS['_defaults_by_weapon_type'],{'AR':{'post_reload_delay':0}},clear=True)):context.enter_context(item)
  if case.get('observe_periodic_skills'):sys.setprofile(periodic_profile)
  squad=[dict(name=n,skill_levels=level) for n,level in zip(NAMES,levels)]
  if 'controls' in case:
   if len(case['controls'])!=5:raise ValueError('Five authored controls required')
   for char,control in zip(squad,case['controls']):char['control']=copy.deepcopy(control)
  config=dict(duration=case['duration'],rng_mode='expected',burst_gauge_mode='accumulate',cover_hp=1000,camera_mode=case.get('camera_mode','single'),camera=case.get('camera',[]))
  if 'focus_aim_layer2' in case:config['aim_interrupt']=case['focus_aim_layer2']
  for key in ('control_mode','sequence'):
   if key in case:config[key]=copy.deepcopy(case[key])
  if case.get('burst_controls'):
   from world_burst_control_native import resolve
   config.update(resolve(case,NAMES)[0])
   for char,weapon in zip(squad,case['combat']['weapons']):
    if weapon.get('explicit_burst_stage'):char['burst_stage']=str(weapon['stage'])
  try:
   if original_run is None:result=timeline.simulate(squad,config=config,enemy=enemy,seed=case.get('seed',19),verbose=case.get('native_snapshot_logging',False))
   else:
    expected=original_run['prepared'];original_register=buff_manager.BuffManager._register_all
    def registered(manager):
     result=original_register(manager)
     actual=[dict(effect=copy.deepcopy(e),owner=n) for e,n in manager._effects]
     if actual!=expected['effects']:raise ValueError('Original registered definitions/owners/order changed')
     capture['original_definitions_verified']=len(actual)
     if case.get('coordinate_typed_probe'):
      additions=case.get('declared_effects',[])
      if len(additions)!=1 or case.get('probe_source')!=len(actual):raise ValueError('One explicit typed probe after unchanged original definitions required')
      manager._effects.append((copy.deepcopy(additions[0]),case.get('probe_owner',NAMES[0])))
     if case.get('declared_owner_counter'):
      from portable_typed_owner_declarations import declarations
      additions=declarations(case,expected['effects'])
      if case.get('coordinate_typed_probe') or case['effects'][len(actual):]!=[e for e,_ in additions] or case['owners'][len(actual):]!=[0]*len(additions):raise ValueError('Declared owner audit must follow unchanged original definitions')
      manager._effects.extend(additions)
     # Registration retains module-global parsed definitions. Keep observer
     # annotations local, preserving aliases between ordered lookup and dispatch.
     memo={}
     manager._effects=copy.deepcopy(manager._effects,memo)
     manager._char_effects_cache=copy.deepcopy(manager._char_effects_cache,memo)
     manager._build_notify_index()
     for i,(e,_) in enumerate(manager._effects):e['_portable_observer_row']=i
     if case.get('observe_target_counters'):
      from world_target_counter_battle_native import initialize
      initialize(manager,capture)
     return result
    def execute(run):
     chars=[{k:v for k,v in c.items() if k!='_weapon'} for c in expected['chars']]
     changed=[k for k,a,b in [('roster',run.squad,chars),('config',run.config,expected['policies']['config']),('seed',run.seed,expected['policies']['seed']),('enemy',{**timeline.DEFAULT_ENEMY,**(run.enemy or {})},original_run['scalar_enemy'])] if a!=b]
     if changed:raise ValueError('Original input identity changed: '+','.join(changed))
     for c in expected['chars']:
      if timeline._NIKKE[c['name']]!=c['_weapon']:raise ValueError('Original weapon metadata changed')
     from native_python_profile import python_observers_only
     squad=run.squad
     config=run.config
     if case.get('declared_aim_controls'):
      from portable_declared_aim_controls import apply
      squad=apply(squad,case['declared_aim_controls'])
     if case.get('declared_manual_sequences'):
      from portable_declared_manual_sequences import apply
      squad=apply(squad,case['declared_manual_sequences'])
     if case.get('declared_burst_sequence'):
      from portable_declared_burst_sequence import apply
      config=apply(config,expected['chars'],case['declared_burst_sequence'])
     with python_observers_only(case.get('python_observers_only',False)):
      capture['original_result']=timeline.simulate(squad,config=config,enemy=copy.deepcopy(case['enemy']),seed=run.seed,verbose=True)
     return capture['original_result']
    context.enter_context(patch.object(buff_manager.BuffManager,'_register_all',registered));context.enter_context(patch.object(engine_worker.sim,'execute',execute))
    engine_worker.evaluate(copy.deepcopy(original_run['body']));result=capture['original_result']
  finally:
   if case.get('observe_periodic_skills'):sys.setprofile(previous_profile)
 state=capture['state'];bm=capture['bm'];rng=capture['boss']._rng
 hits=[dict(time=h.t,pattern=h.pattern,owner=NAMES.index(h.target),damage=h.damage,pierce=h.pierce,shield=h.shield,cover=h.cover,decoy=h.decoy,hp=h.hp,hp_after=h.hp_after,down=h.down) for h in result.squad_hits]
 graph_states=[[int(r.active),r.opens,*bits(r.start_t),r.fired,0,int(cleared_run(r)),0,*r.consumed_after,*([0]*(8-len(r.consumed_after))),*r.consumed_until,*([0]*(8-len(r.consumed_until)))] for r in capture['boss']._runs];graph_states.extend([[0]*24 for _ in range(32-len(graph_states))])
 answer=dict(graph_states=graph_states,graph_history=[[32,0,*bits(capture['boss']._ends['start'][0][0])],*ends],damage=[result.char_total.get(n,0) for n in NAMES],allies=[dict(hp=state['hp'][n],max_hp=bm.effective_max_hp(n),hp_pct=state['hp_pct'][n],defense=bm._effective_def(n),down=n in state['down'],received_damage=sum(h['hp'] for h in hits if h['owner']==i),received_hits=sum(h['owner']==i for h in hits)) for i,n in enumerate(NAMES)],covers=[dict(hp=state['cover_hp'][n],max_hp=state['cover_max_hp'][n],effective_max_hp=bm.cover_max_hp(n,capture['time'])) for n in NAMES],shots=[counts[n] for n in NAMES],ammo=[capture['characters'][n].ammo for n in NAMES],hits=hits,boss_log=[dict(time=x.t,pattern=x.pattern,event=x.event,outcome=x.outcome) for x in result.boss_log],rng=dict(index=rng.getstate()[1][-1],state=list(rng.getstate()[1][:-1]),draws=rng.draws,rejects=rng.rejects,samples=rng.samples),scope='Actual full native simulate;only authored effects,base stats and weapon metadata are replaced. Scheduler,target selector,layered landing,weapon tick and frame loop are native.')
 if case.get('observe_fractional_hits'):answer.update(fractional_hits=capture['fractional_hits'],fractional_accumulators=capture['fractional_accumulators'])
 if case.get('observe_enemy_spawn'):answer['enemy_spawn_notifications']=capture['enemy_spawn_notifications']
 if case.get('observe_periodic_skills'):answer['periodic_runtime']=capture['periodic_runtime']
 if case.get('observe_skill_clocks'):answer['skill_clocks']=capture['skill_clocks']
 if case.get('observe_skill_critical'):answer['skill_critical']=capture['skill_critical']
 if case.get('observe_base_copies'):answer['base_copies']=capture['base_copies']
 if case.get('observe_healing_storage'):answer['healing_storage']=capture['healing_storage']
 if original_run is not None:
  answer['original_input_identity']=dict(definitions=capture['original_definitions_verified'],chars_config_seed_weapon_verified=True,authored_metadata_overrides=False,authored_delays_overrides=False)
  if case.get('declared_aim_controls'):answer['original_input_identity'].update(original_controls_preserved=False,declared_aim_controls_applied_after_identity_check=True)
  if case.get('declared_manual_sequences'):answer['original_input_identity'].update(original_controls_preserved=False,declared_manual_sequences_applied_after_identity_check=True)
  if case.get('declared_burst_sequence'):answer['original_input_identity'].update(original_controls_preserved=False,declared_burst_sequence_applied_after_identity_check=True)
  answer['scope']='Actual original prepared roster, original effects/weapon/config/base-stat hooks; declared coordinate world and scoped numeric policy only'
  if case.get('declared_burst_sequence'):answer['scope']+='; declared burst sequence applied after original identity verification'
 if case.get('observe_pending_skills'):
  answer['pending_burst']=dict(count=len(capture['burst_controller']._pending_burst_dmg),enqueued=capture.get('pending_enqueued',0),fired=capture.get('pending_fired',0))
 if case.get('observe_overlay'):
  answer.update(gauge=state.get('burst_gauge',0.0),world_nodes=[dict(blocked=r.blocked,opens=r.opens) for r in capture['boss']._runs])
 if case.get('observe_cleanse'):
  for out,run in zip(answer['world_nodes'],capture['boss']._runs):out.update(dispelled=run.dispelled,dispels=sum(x.event=='dispel' and x.pattern==run.p.id for x in result.boss_log))
 if case.get('observe_charge_hold'):
  answer['charge_hold']=[dict(owner=i,charging=capture['characters'][n]._charge_phase=='charging',full_time=capture['characters'][n]._charge_full_t,deadline=capture['characters'][n]._vanish_charge_hold_until) for i,n in enumerate(NAMES) if n=='스노우 화이트 : 헤비암즈']
 if case.get('observe_enemy_attack_fields'):answer['enemy_attack_fields']=capture['enemy_attack_fields']
 if case.get('observe_enemy_fields'):answer['enemy_fields']=capture['enemy_fields']
 if case.get('observe_target_counters'):answer['target_counters']=capture['target_counters']
 if case.get('observe_named_state'):
  from world_actor_state_native import after_finish
  answer['named_state']=dict(capture['named_state'],pending_gone=after_finish(capture['boss']))
 if case.get('observe_actor_pools'):
  from world_actor_pool_native import summary
  body_hits=[h for h in result.hits if not (h.target or h.part)]
  answer['actor_pools']=summary(capture['boss'],body_hits,capture['actor_notices'],capture['actor_deaths'])
  answer['actor_add_damage']=[result.add_char_total.get(n,0) for n in NAMES]
 return answer
