"""Observe full native simulate, including its actual boss/weapon/frame ordering."""
import copy,sys,struct
from unittest.mock import patch
import engine_worker
from calculator import timeline,buff_manager
from enemy_target_native import ObservedRNG
from timer_registry_cases import NAMES

def authored_metadata(case):
 """Literal weapon normalization only;does not tick a character or a battle."""
 metadata={}
 for n,w in zip(NAMES,case['combat']['weapons']):
  rate=w.get('rate',1/w['interval']);maximum=w.get('rate_max',rate)
  metadata[n]=dict(timeline._NIKKE[n],weapon_type=w.get('base_weapon_type','MG' if w.get('mode')=='auto_warmup' else 'AR'),is_charge=w.get('mode')=='charge',input_type='DOWN_Charge' if w.get('mode')=='charge' else 'DOWN',burst_stage=str(w.get('stage',0)),fire_rate=rate,fire_rate_max=maximum,damage_coeff=w.get('coefficient',100),max_ammo=w['capacity'],reload_time=w['reload'],burst_energy=w.get('gauge',0),muzzles=w.get('muzzles',1),pellets=w.get('pellets',1),core_dmg_mult=200)
  if 'warmup' in w:metadata[n]['fire_rate_change_pershot']=(maximum-rate)/w['warmup']
  if w.get('mode')=='charge':metadata[n].update(charge_time=w.get('charge',.2),full_charge_mult=w.get('full_charge_mult',100),fire_stance_hold=None)
 for n in NAMES:metadata[n].update(copy.deepcopy(case.get('weapon_metadata',{})))
 if case.get('element_codes'):
  for n,code in zip(NAMES,case['element_codes']):metadata[n]['element_code']=code
 return metadata

def observe(case):
 capture={};ends=[];counts={n:0 for n in NAMES};effects=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case['owners'])]
 bits=lambda v:list(struct.unpack('<II',struct.pack('<d',float(v))))
 original_char=timeline.CharState;original_burst=timeline.BurstController;original_boss=timeline.BossScript
 class Character(original_char):
  def tick(self,*args,**kwargs):
   hits=super().tick(*args,**kwargs);counts[self.name]+=int(bool(hits));capture.setdefault('characters',{})[self.name]=self;return hits
 class Controller(original_burst):
  def tick(self,t,bm,state):capture.update(bm=bm,state=state,time=t);return super().tick(t,bm,state)
 class Boss(original_boss):
  def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);capture['boss']=self
  def _close(self,run,t,outcome,events):
   super()._close(run,t,outcome,events);ends.append([run.p.idx,{'cleared':1,'expired':2,'followed':3,'end':4}[outcome],*bits(t)])
 def register(bm):bm._effects=copy.deepcopy(effects);bm._build_notify_index()
 metadata=authored_metadata(case)
 def stats(char):
  i=NAMES.index(char['name']);a=case['environment']['allies'][i]
  return {'atk':case['base_atk'][i],'hp':a['base_hp'],'def':a['base_defense']}
 enemy={'def':0,'code':None,'core_px':0,'optimal_range_weapons':[],'patterns':copy.deepcopy(case['patterns'])}
 enemy.update(copy.deepcopy(case.get('enemy',{})))
 with patch.dict(timeline._NIKKE,metadata),patch.dict(buff_manager._NIKKE,metadata),patch.object(timeline,'calc_base_stats',stats),patch.object(buff_manager.BuffManager,'_register_all',register),patch.object(timeline,'CharState',Character),patch.object(timeline,'BurstController',Controller),patch.object(timeline,'BossScript',Boss),patch.object(timeline.random,'Random',ObservedRNG),patch.dict(timeline._DELAYS['_exceptions'],{},clear=True),patch.dict(timeline._DELAYS['_defaults_by_weapon_type'],{'AR':{'post_reload_delay':0}},clear=True):
  result=timeline.simulate([dict(name=n,skill_levels={'1':10,'2':10,'3':10}) for n in NAMES],config=dict(duration=case['duration'],rng_mode='expected',burst_gauge_mode='accumulate',cover_hp=1000,camera_mode=case.get('camera_mode','single'),camera=case.get('camera',[])),enemy=enemy,seed=19)
 state=capture['state'];bm=capture['bm'];rng=capture['boss']._rng
 hits=[dict(time=h.t,pattern=h.pattern,owner=NAMES.index(h.target),damage=h.damage,pierce=h.pierce,shield=h.shield,cover=h.cover,decoy=h.decoy,hp=h.hp,hp_after=h.hp_after,down=h.down) for h in result.squad_hits]
 graph_states=[[int(r.active),r.opens,*bits(r.start_t),r.fired,0,0,0,*r.consumed_after,*([0]*(8-len(r.consumed_after))),*r.consumed_until,*([0]*(8-len(r.consumed_until)))] for r in capture['boss']._runs];graph_states.extend([[0]*24 for _ in range(32-len(graph_states))])
 answer=dict(graph_states=graph_states,graph_history=[[32,0,*bits(capture['boss']._ends['start'][0][0])],*ends],damage=[result.char_total.get(n,0) for n in NAMES],allies=[dict(hp=state['hp'][n],max_hp=bm.effective_max_hp(n),hp_pct=state['hp_pct'][n],defense=bm._effective_def(n),down=n in state['down'],received_damage=sum(h['hp'] for h in hits if h['owner']==i),received_hits=sum(h['owner']==i for h in hits)) for i,n in enumerate(NAMES)],covers=[dict(hp=state['cover_hp'][n],max_hp=state['cover_max_hp'][n],effective_max_hp=bm.cover_max_hp(n,capture['time'])) for n in NAMES],shots=[counts[n] for n in NAMES],ammo=[capture['characters'][n].ammo for n in NAMES],hits=hits,boss_log=[dict(time=x.t,pattern=x.pattern,event=x.event,outcome=x.outcome) for x in result.boss_log],rng=dict(index=rng.getstate()[1][-1],state=list(rng.getstate()[1][:-1]),draws=rng.draws,rejects=rng.rejects,samples=rng.samples),scope='Actual full native simulate;only authored effects,base stats and weapon metadata are replaced. Scheduler,target selector,layered landing,weapon tick and frame loop are native.')
 if case.get('observe_overlay'):
  answer.update(gauge=state.get('burst_gauge',0.0),world_nodes=[dict(blocked=r.blocked,opens=r.opens) for r in capture['boss']._runs])
 if case.get('observe_cleanse'):
  for out,run in zip(answer['world_nodes'],capture['boss']._runs):out.update(dispelled=run.dispelled,dispels=sum(x.event=='dispel' and x.pattern==run.p.id for x in result.boss_log))
 return answer
