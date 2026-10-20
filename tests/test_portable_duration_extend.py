"""Native named extension, independent enemy lifetimes and immutable masks."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import engine_worker
from portable_duration_extend_specs import plan,members
from portable_specs import ABI,LIMITS as L,FIELDS as F
from portable_removal_oracle import observe
sp=importlib.util.spec_from_file_location('duration_unit_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
CASES=json.loads((R/'tests/fixtures/portable-duration-extend.json').read_text())['cases']
def case(name):return copy.deepcopy(next(c for c in CASES if c['name']=='duration-extend-'+name))
class DurationTests(unittest.TestCase):
 def test_native_query_contracts(self):
  for c in CASES:
   with self.subTest(name=c['name']):
    native=observe(c)
    v.contains(native['queries'],[{k:x for k,x in q.items() if k in ('allies','attack_buffs','enemy_modifiers')} for q in c['expected_queries']],c['name'])
 def test_space_delimited_prefix_is_static_not_runtime_cpu_state(self):
  c=case('exact-space-prefix');before=copy.deepcopy(c);w,_=v.compile_case(c);row=len(c['effects'])-1;at=L['FORCE_BASE']+row*L['MASK_WORDS']
  self.assertEqual(w[at:at+L['MASK_WORDS']],[3]+[0]*7);self.assertEqual(c,before)
  self.assertEqual(members(c['effects'][-1],list(zip(c['effects'],c['owners']))),[0,1])
 def test_high_definition_membership_and_no_layout_growth(self):
  c=case('definition-255-mask-boundary');w,_=v.compile_case(c);at=L['FORCE_BASE']
  self.assertEqual(ABI,0x50455667);self.assertEqual((L['INPUT_WORDS'],L['OUTPUT_WORDS']),(86016,159744))
  self.assertEqual(w[at:at+L['MASK_WORDS']],[0]*7+[1<<31])
 def test_shared_ally_instance_extends_for_all_members(self):
  r=observe(case('shared-instance-whole-expiry'));self.assertEqual(len(r['carriers']),1)
  self.assertEqual((r['carriers'][0]['recipients'],r['carriers'][0]['expiry']),(31,1))
 def test_enemy_receivers_have_separate_deadlines_and_generations(self):
  r=observe(case('enemy-independent-boss'));states=[c for c in r['carriers'] if c['definition']==0]
  self.assertEqual([(c['recipients'],c['expiry'],c['enemy_generation']) for c in states],[(32,1,1)])
  self.assertEqual(len(r['endings']),2)
 def test_generation_change_does_not_extend_an_old_enemy_life(self):
  r=observe(case('enemy-new-life-does-not-extend-old-carrier'))
  self.assertEqual([(c['recipients'],c['expiry']) for c in r['carriers']],[(32,1.5),(64,1),(128,1.5)])
 def test_enemy_children_finish_before_next_receiver(self):
  r=observe(case('enemy-child-removes-before-next-receiver'))
  self.assertEqual([e['name'] for e in r['endings']],['State']*3)
  self.assertEqual(r['queries'][0]['attack_buffs'][0],3)
 def test_alias_refresh_lifetime_is_not_the_original_definition_duration(self):
  finite=observe(case('infinite-definition-refreshed-finite'));self.assertEqual(finite['carriers'][0]['expiry'],1.1)
  infinite=observe(case('finite-definition-refreshed-infinite'));self.assertEqual(infinite['carriers'][0]['expiry'],1e30)
 def test_invalid_names_targets_and_enemy_without_world_fail_closed(self):
  e=case('shared-instance-whole-expiry')['effects'][-1]
  for name in (None,1,False):
   bad=copy.deepcopy(e);bad['target_effect']=name
   with self.subTest(name=name),self.assertRaises(ValueError):plan(bad)
  for target in (None,False,'unmodelled-selector'):
   bad=copy.deepcopy(e);bad['target']=target
   with self.subTest(target=target),self.assertRaises(ValueError):plan(bad)
  bad=copy.deepcopy(e);bad['target']='boss'
  with self.assertRaises(ValueError):plan(bad)
if __name__=='__main__':unittest.main()
