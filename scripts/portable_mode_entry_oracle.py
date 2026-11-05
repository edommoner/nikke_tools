"""Native data context and actual firing observer;no engine handler replacements."""
import copy,math
from contextlib import contextmanager
from unittest.mock import patch
import engine_worker
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_weapon_oracle import authored_weapon,authored_weapon_state,observed_next_fire
from timer_registry_cases import NAMES
@contextmanager
def data_context(case):
 who=case['mode_entry_context']['owner'];old=timeline._DELAYS.get('_weapon_change',{});replacement=dict(old)
 updates=dict(old.get(NAMES[who],{}))
 for name,delay in case['mode_entry_context']['delays'].items():
  if type(delay) not in (float,int) or not math.isfinite(delay) or not 0<=delay<=180:raise ValueError('Invalid authored entry delay')
  updates[name]=dict(updates.get(name,{}),entry_delay=delay)
 replacement[NAMES[who]]=updates
 with patch.dict(timeline._DELAYS,{'_weapon_change':replacement}):yield

def observe(case):
 who=case['mode_entry_context']['owner'];w=case['combat']['weapons'][who]
 chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(engine_worker.META[n])) for n in NAMES];authored_weapon(chars[who],w)
 effects=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case['owners'])]
 class BM(BuffManager):
  def _register_all(self):self._effects=effects;self._build_notify_index()
 enemy={'def':0,'core_px':0,'code':None,'optimal_range_weapons':[]}
 bm=BM(chars,state=dict(base_stats={n:dict(atk=1000,hp=1000000,**{'def':0}) for n in NAMES},enemy=enemy,full_burst=False,rng_acc={},rng_expected=True,camera=set()))
 st=authored_weapon_state(chars[who],w);st.ammo=st._full_ammo(bm,0)
 timeline._register_instant_handlers(bm,{n:st if i==who else object() for i,n in enumerate(NAMES)},None)
 total=0;shots=0;frame=0;queries=[];diagnostics=[];started=False
 with data_context(case):
  for t,op,event,owner,arg,index,extra,extra2 in case['script']:
   if op==0:
    bm.tick(t);bm.notify({0:'battle_start',7:'on_attack',17:'event:cover_healed',19:'event:full_reload'}[event],t,NAMES[owner])
   elif op==24:
    while frame/60<=t:
     now=frame/60
     if not started:
      for n in NAMES:bm.notify('battle_start',now,n)
      st.ammo=st._full_ammo(bm,now);started=True
     bm.tick(now);hits=st.tick(now,bm,enemy,{'rng_mode':'expected'});total+=sum(h.damage for h in hits);shots+=bool(hits);frame+=1
   elif op==2:
    mode=bm.get_weapon_change(NAMES[who]);mode_index=next((j for j,(e,n) in enumerate(effects) if e is mode and n==NAMES[who]),-1)
    weapons=[{} for _ in range(5)];weapons[who]=dict(ammo=st.ammo,shots=shots,next=observed_next_fire(st,bm),reload_until=st.reloading_until,mode_index=mode_index,mode_shots=st._wc_shots)
    damage=[0]*5;damage[who]=total;queries.append(dict(damage=damage,combat=dict(weapons=weapons)))
    diagnostics.append(dict(time=t,entry_until=st._wc_entry_reload_until,mode_new_session=st._wc_new_session,physical_mode_active=st._in_weapon_change,charge_phase=st._charge_phase,base_post_reload=st._post_reload_end_t))
   else:raise ValueError('Unknown mode entry oracle stimulus')
 extras=[{} for _ in range(5)];extras[who]=dict(charge_started_at=st._charge_start_t,post_reload_until=st._post_reload_end_t,pending_auto_reload=st._pending_auto_reload)
 return dict(queries=queries,weapons=extras,mode_entry_wait_until=[st._wc_entry_reload_until if i==who else -1 for i in range(5)],diagnostics=diagnostics)
