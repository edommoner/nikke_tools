import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('base_copy_boundaries',ROOT/'scripts/verify-base-copy.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from effect_runtime import CATALOG,Catalog,Handler
from lifecycle_specs import LifecycleSpec,ordered_specs
class BaseCopyRuntimeTests(unittest.TestCase):
 def test_distinct_recipient_sets_initialize_distinct_carriers(self):
  for stat,policy in m.POLICIES.items():
   with self.subTest(stat=stat):
    effect=m.B('recipient copies',stat,20,'allies_burst_casted_burst3',event='on_attack',duration=2,copy_from=policy.selector)
    class Manager(m.BuffManager):
     def _register_all(self):self._effects=[(effect,m.N[0])];self._build_notify_index()
    bs={n:dict(atk=1000,**{'def':0},hp=1000) for n in m.N}
    manager=Manager(m.v.characters(m.N),state=dict(base_stats=bs,hp={n:1000 for n in m.N},hp_pct={n:100 for n in m.N},burst_casted={m.N[2]:True},enemy={'def':0,'core_px':0},full_burst=False,rng_acc={},rng_expected=True,camera=set()))
    manager.notify('on_attack',.1,m.N[0]);manager.state['burst_casted']={m.N[3]:True};manager.notify('on_attack',.2,m.N[0])
    carriers=[ab for ab in manager._active if ab.effect is effect]
    self.assertEqual(len(carriers),2);self.assertEqual([ab.copy_basis for ab in carriers],[1000,1000])
    self.assertEqual([ab.target_chars for ab in carriers],[[m.N[2]],[m.N[3]]])
    for recipient in m.N[2:4]:
     if stat=='hp_copy':self.assertEqual((manager.state['hp'][recipient],manager.effective_max_hp(recipient)),(1200,1200))
     else:self.assertEqual(manager.get_buffs(recipient,'enemy',.2)['atk_flat'],200)
 def test_independent_base_selection_stack_refresh_and_child_order(self):
  self.assertTrue(all(row['passed'] for row in m.independent(None,'native',True)))
  self.assertTrue(callable(CATALOG.handlers['base_stat_copy'].prepare_activation))
 def test_prepare_phase_registration_is_validated(self):
  with self.assertRaises(ValueError):ordered_specs((LifecycleSpec('bad',activation_stat=85,gpu_prepare='not;a;function'),))
  with self.assertRaises(ValueError):ordered_specs((LifecycleSpec('bad',current_instance=True),))
  with self.assertRaises(ValueError):ordered_specs((LifecycleSpec('bad',activation_stat=85,current_instance=1),))
  with self.assertRaises(ValueError):ordered_specs((LifecycleSpec('bad',activation_stat=85,initial_hp_stats=(86,)),))
  with self.assertRaises(ValueError):ordered_specs((LifecycleSpec('bad',activation_stat=85,initial_hp_stats=[85]),))
  catalog=Catalog((LifecycleSpec('copy',cpu_phase='prepare_activation'),))
  with self.assertRaises(ValueError):catalog.register('copy',Handler())
 def test_unknown_selector_and_unsupported_value_shapes_reject(self):
  chars=m.v.characters(m.N)
  for stat,policy in m.POLICIES.items():
   for fields in ({'copy_from':'allies_top_atk:2'},{'copy_from':None},{'copy_from':policy.selector,'scaling':'lost_hp_pct'},{'copy_from':policy.selector,'duration_bullets':2}):
    with self.subTest(stat=stat,fields=fields),self.assertRaises(m.g.UnsupportedDetail):m.g.compile_effects(chars,[(m.B('copy',stat,20,**fields),m.N[0])])
 def test_forged_copy_instruction_and_query_reject_before_cuda(self):
  for stat,policy in m.POLICIES.items():
   program=m.g.compile_effects(m.v.characters(m.N),[(m.B('copy',stat,20,copy_from=policy.selector),m.N[0])])
   for field,value in ((0,.5),(1,4),(258,1),(4,4),(4,99),(36,2),(10,0),(62,1)):
    bad=copy.deepcopy(program);bad['effects'][0][field]=value
    with self.subTest(stat=stat,field=field),self.assertRaisesRegex(ValueError,'copy instruction|compiled detailed'):m.g.run(None,[bad],[[0,2,125,0,-1,0,0,0]],[[0,0]],[{}])
   for key in (-2,m.g.NE,.5):
    with self.subTest(key=key),self.assertRaisesRegex(ValueError,'copy query'):m.g.run(None,[program],[[0,2,125,0,key,0,0,0]],[[0,0]],[{}])
if __name__=='__main__':unittest.main()
