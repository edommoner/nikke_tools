import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
from effect_runtime import RuntimeState,state
from lifecycle_specs import LifecycleSpec,ordered_specs
spec=importlib.util.spec_from_file_location('accum_cpu_helpers',ROOT/'scripts/verify-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from calculator.buff_manager import BuffManager
class DamageAccumRuntimeTests(unittest.TestCase):
 def test_archive_is_battle_and_family_scoped(self):
  a=RuntimeState();b=RuntimeState();ledger={'pool':4}
  self.assertIs(a.archive('damage',ledger),ledger);self.assertEqual(b.archive('damage'),{});self.assertEqual(a.archive('healing'),{})
 def test_related_stats_share_one_validated_operation(self):
  self.assertEqual(len(ordered_specs((LifecycleSpec('damage',activation_stat=81,additional_stats=(82,),gpu_activate='build_damage'),))),1)
  with self.assertRaises(ValueError):ordered_specs((LifecycleSpec('damage',activation_stat=81,additional_stats=(81,)),))
  with self.assertRaises(ValueError):ordered_specs((LifecycleSpec('damage',activation_stat=81,additional_stats=[82]),))
 def test_refresh_then_expiry_without_hits_cannot_release_old_lifetime(self):
  names=['리타','크라운','모더니아','앨리스','N102'];chars=v.characters(names)
  effect={'name':'pool','source':'스킬1','type':'buff','stat':'dmg_accum_received_atk_pct','target':'target','fixed_value':100,'duration':.3,'trigger':{'timing':['on_attack'],'condition':[]}}
  class Manager(BuffManager):
   def _register_all(self):self._effects=[(effect,names[0])];self._build_notify_index()
  manager=Manager(chars,state={'base_stats':{n:{'atk':1000,'def':0,'hp':100000} for n in names},'enemy':{'def':0,'core_px':0},'full_burst':False,'rng_acc':{},'rng_expected':True,'camera':set()})
  manager.notify('on_attack',0,names[0]);manager.accumulate_damage(names[1],700,.1)
  self.assertEqual(manager._accum_last['pool'],700)
  manager.notify('on_attack',.2,names[0]);self.assertEqual(manager._accum_last['pool'],0)
  self.assertIs(state(manager).archive('damage_accumulation'),manager._accum_last)
  manager.tick(.6);self.assertEqual(manager.accum_discharge('pool',.6),0)
if __name__=='__main__':unittest.main()
