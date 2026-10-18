"""Shared identity witnesses; numerical/formula tests remain in their own oracles."""
import copy,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace as NS
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker
from effect_runtime import state,pool
from protection_runtime import activate as protection,ProtectionPolicy
from healing_storage_compat import snapshot as storage
from heal_charge_compat import snapshot as charge
from damage_accum_runtime import activate as damage
from max_hp_snapshot_runtime import activate as maximum

OPERATIONS=(('shield','shield_from_max_hp_pct',None),('decoy','decoy',None),
 ('overheal_storage','heal_overcharge_store',storage),
 ('healing_charge','heal_overcharge_store_atk_pct',charge),
 ('damage_accumulation','dmg_accum_received_atk_pct',damage),
 ('max_hp_snapshot','max_hp_from_max_hp_pct',maximum))

def callback_identity_cases():
 rows=[]
 for kind,stat,callback in OPERATIONS:
  effect=dict(type='buff',stat=stat,name='same definition')
  old=NS(uid=1,effect=effect,caster='a',target_chars=['b'],expires_at=10,
         accum=17,heal_charge_current=17,heal_store_current={'b':17},heal_store_expiry=10)
  new=NS(uid=2,effect=effect,caster='a',target_chars=['c'],expires_at=10,accum=0)
  manager=NS(_active=[old,new],_get_value=lambda *args:20,
      effective_max_hp=lambda *args:1000,final_atk=lambda *args:1000,
      take_next_shield_amp=lambda *args:0,notify=lambda *args:None,
      squad_names=['a','b','c'],_accum_last={})
  previous=copy.deepcopy(vars(old));state(manager).activation_stack.append(new)
  try:
   if callback:callback(manager,effect,'a',1)
   else:protection(manager,effect,'a',1,['c'],ProtectionPolicy(kind,frozenset({stat}),'current','capacity',kind=='shield'))
  finally:state(manager).activation_stack.pop()
  registered=sorted(pool(manager,kind));untouched=previous==vars(old)
  rows.append(dict(operation=kind,registered=registered,expected_registered=[2],
    previous_carrier_unchanged=untouched,contract_satisfied=registered==[2] and untouched))
 return rows

def recipient_instance_cases():
 spec=importlib.util.spec_from_file_location('carrier_witness_helpers',ROOT/'scripts/verify-base-copy.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 rows=[]
 for kind,stat,callback in (*OPERATIONS,('damage_accumulation','dmg_accum_dealt_atk_pct',damage)):
  effect=m.B('recipient state',stat,20,'allies_burst_casted_burst3',event='on_attack',duration=2)
  class Manager(m.BuffManager):
   def _register_all(self):self._effects=[(effect,m.N[0])];self._build_notify_index()
  bs={n:dict(atk=1000,**{'def':0},hp=1000) for n in m.N}
  manager=Manager(m.v.characters(m.N),state=dict(base_stats=bs,hp={n:1000 for n in m.N},hp_pct={n:100 for n in m.N},burst_casted={m.N[2]:True},enemy={'def':0,'core_px':0},full_burst=False,rng_acc={},rng_expected=True,camera=set()))
  manager.notify('on_attack',.1,m.N[0]);old=next(ab for ab in manager._active if ab.effect is effect)
  # A different instance must not replenish the original recipient's resource.
  if kind=='shield':old.shield_per_target[m.N[2]]=37
  elif stat=='decoy':old.decoy_per_target[m.N[2]]=37
  elif kind=='overheal_storage':old.heal_store_current[m.N[2]]=37
  elif kind=='healing_charge':old.heal_charge_current=37
  elif kind=='damage_accumulation':old.accum=37
  prior=copy.deepcopy(vars(old));manager.state['burst_casted']={m.N[3]:True}
  manager.notify('on_attack',.2,m.N[0]);carriers=[ab for ab in manager._active if ab.effect is effect]
  new=carriers[-1];checks=dict(two_instances=len(carriers)==2,old_unchanged=vars(old)==prior,
    both_registered=set(pool(manager,kind))=={old.uid,new.uid},second_targets=new.target_chars==[m.N[3]])
  if kind=='shield':checks['new_quantity']=new.shield_per_target=={m.N[3]:200}
  elif stat=='decoy':checks['new_quantity']=new.decoy_per_target=={m.N[3]:200}
  elif kind=='overheal_storage':checks['new_quantity']=new.heal_store_capacity=={m.N[3]:200} and new.heal_store_current=={m.N[3]:0}
  elif kind=='healing_charge':checks['new_quantity']=new.heal_charge_base_cap==200 and new.heal_charge_current==0
  elif kind=='damage_accumulation':checks['new_quantity']=new.accum_cap==200 and new.accum==0
  else:checks['new_quantity']=new.hp_bonus_flat==200 and all((manager.state['hp'][n],manager.effective_max_hp(n))==(1200,1200) for n in m.N[2:4])
  rows.append(dict(operation=kind,stat=stat,checks=checks,passed=all(checks.values())))
 return rows
