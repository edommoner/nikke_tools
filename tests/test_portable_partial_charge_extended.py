"""Dynamic charge classification, arbitration and notification ordering."""
import copy,sys,random,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker,portable_backend
from calculator.buff_manager import BuffManager
from portable_partial_charge_extended_cases import fixtures
from portable_nonfull_charge_contracts import verify
from world_nonfull_charge_native import observe
from world_projectile_native import observe as plain


class ExtendedChargeTests(unittest.TestCase):
 def test_all14_literal_contracts_and_semantic_reads_are_unchanged(self):
  rows=fixtures();before=copy.deepcopy(rows);self.assertEqual(len(rows),14)
  for case in rows:
   def measured(run):
    with patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get,patch.object(BuffManager,'has_live_stat',autospec=True,side_effect=BuffManager.has_live_stat) as live,patch.object(random,'sample',side_effect=random.sample) as rng:
     result=run(case);return result,[get.call_count,live.call_count,rng.call_count]
   with self.subTest(case=case['name']),patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')):
    (native,trace),reads=measured(observe);verify(case,native);native.pop('nonfull_charge');(baseline,original),counts=measured(plain)
    self.assertEqual(native,baseline);self.assertEqual(trace,original);self.assertEqual(reads,counts)
  self.assertEqual(rows,before)

 def test_authored_base_clocks_match_static_native_metadata(self):
  from calculator import timeline
  from world_frame_native import authored_metadata,roster_names
  for c in fixtures():
   with self.subTest(case=c['name']),patch.dict(timeline._NIKKE,authored_metadata(c)),patch.dict(timeline._DELAYS['_exceptions'],{},clear=True),patch.dict(timeline._DELAYS['_defaults_by_weapon_type'],{'AR':{'post_reload_delay':0}},clear=True):
    for who,name in enumerate(roster_names(c)):
     state=timeline.CharState(dict(name=name),c['base_atk'][who],c['enemy'].get('code'))
     self.assertEqual(c['post_fire_delays'][who],state.post_fire_delay);self.assertEqual(c['combat']['weapons'][who].get('min_cycle',0),state._min_fire_cycle)

 def test_order_witnesses_require_visible_prior_notifications(self):
  for c in fixtures()[-2:]:
   n,_=observe(c);verify(c,n);bad=copy.deepcopy(n);next(e for e in bad['nonfull_charge'] if e['kind']=='activate')['time']+=.001
   with self.assertRaises(AssertionError):verify(c,bad)


if __name__=='__main__':unittest.main()
