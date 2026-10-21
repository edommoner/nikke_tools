"""Native ordering and authored packing for immediate pending batches."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
import world_pending_cases as cases
class PendingContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows={c['name']:c for c in cases.fixtures()}
 def observe(self,name):return cases.suite.inspect_native(self.rows[name])[1]
 def test_pending_lands_on_creation_frame(self):
  r=self.observe('pending-baseline');self.assertEqual(len(r),1);self.assertEqual(r[0]['created'],r[0]['landed'])
 def test_pending_does_not_drain_ordinary_children_early(self):
  c=self.rows['pending-does-not-drain-fullburst-ordinary-child'];r=self.observe(c['name']);pending=next(x for x in r if c['effects'][x['row']]['name']=='pending');ordinary=next(x for x in r if c['effects'][x['row']]['name']=='ordinary')
  self.assertEqual(pending['created'],ordinary['created']);self.assertGreater(ordinary['landed'],pending['landed'])
 def test_pending_snapshot_excludes_later_cast_buff(self):
  self.assertEqual(self.observe('pending-after-attack-buff')[0]['amount'],354);self.assertEqual(self.observe('pending-before-attack-buff')[0]['amount'],748)
 def test_pending_quantities_precede_counter_field_changes(self):
  self.assertEqual([r['amount'] for r in self.observe('pending-two-amounts-before-first-counter-child')],[354,354])
 def test_pending_overrides_normal_formula_in_authored_packing(self):
  c=self.rows['pending-precedes-explicit-normal-formula'];w,_,_=cases.compile_case(c);L=cases.L
  self.assertEqual(w[L['DAMAGE_DEFINITION_BASE']+8+3],0)
  from portable_specs import FIELDS as F
  self.assertEqual(w[L['DEFINITION_BASE']+L['DEFINITION_WORDS']+F['DAMAGE_FLAGS']],0)
 def test_pending_all128_and_counter_free_are_literal_inputs(self):
  c=self.rows['pending-all128'];w,_,_=cases.compile_case(c);self.assertEqual(self.observe(c['name'])[0]['recipients'],list(range(128)));self.assertEqual(w[cases.L['TARGET_COUNTER_INPUT_BASE']+6],9)
if __name__=='__main__':unittest.main()
