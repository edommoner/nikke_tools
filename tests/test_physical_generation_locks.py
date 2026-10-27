"""Original quota lifetime, native charging grid, pre-removal shot snapshot."""
import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
s=importlib.util.spec_from_file_location('physical_lock_suite',ROOT/'research/verify-physical-locks.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)
class PhysicalLockTests(unittest.TestCase):
 def test_periodic_activations_read_original_two_shot_quota(self):
  c=suite.fixtures()[0];n=suite.observe(c)
  self.assertEqual([p['receipt'][0] for p in n['lock_pulses']],[15,15,15,15,5,5])
  self.assertEqual([len(s['handles']) for s in n['lock_shots']],[2,2]);self.assertEqual(len(n['lock_clears']),2)
  original=suite.source_definitions()[20];self.assertEqual(c['effects'][0],original)
  for s in n['lock_shots']:self.assertTrue(s['handles'])
 def test_short_charge_uses_global_native_grid_and_preserves_empty_snapshots(self):
  n=suite.observe(suite.fixtures()[2]);self.assertEqual([len(s['handles']) for s in n['lock_shots']],[0,1,0,1,1,0]);self.assertEqual(len(n['lock_clears']),6)
 def test_actual_death_prunes_stale_targets_before_emission(self):
  n=suite.observe(suite.fixtures()[1]);self.assertEqual([len(s['handles']) for s in n['lock_shots']],[1,1]);self.assertEqual(n['lock_pulses'][1]['receipt'][1],2);self.assertEqual(len(n['lock_shots'][0]['handles']),1)
 def test_queued_skill_death_and_rebirth_do_not_retarget_frozen_shot(self):
  rows=suite.fixtures();killed=suite.observe(rows[3]);body=suite.observe(rows[4]);reborn=suite.observe(rows[5])
  self.assertEqual(killed['lock_shots'][0]['handles'],[[0,0,1],[5,0,1]])
  self.assertEqual(killed['lock_shots'][1]['handles'],[[0,0,1]])
  self.assertEqual(body['lock_shots'][1]['handles'],[[0,0,1],[5,0,1]])
  self.assertEqual(reborn['lock_shots'][0]['handles'][-1],[5,0,1]);self.assertEqual(reborn['lock_shots'][1]['handles'][-1],[5,0,2])
 def test_arena_is_separate_from_all_live_actor_sets_and_transport_agrees(self):
  from portable_physical_lock_layout import check,BASE,CANDIDATE,SNAPSHOTS,END,OUTPUT
  from portable_wire_layout import check_metal
  r=check(ROOT);self.assertEqual(r['actor_set_capacity'],32);self.assertGreaterEqual(CANDIDATE,BASE)
  self.assertLess(CANDIDATE,SNAPSHOTS);self.assertLessEqual(END,OUTPUT);check_metal(ROOT,OUTPUT)
  import portable_backend
  with self.assertRaisesRegex(ValueError,'separate arena wire'):portable_backend.validate_composed_stride(suite.SOURCE,suite.INPUT,786432)
  with self.assertRaisesRegex(ValueError,'separate arena wire'):portable_backend.validate_composed_stride('gpu/world_projectile_entry.slang',suite.INPUT,OUTPUT)
 def test_transport_guard_changes_are_exactly_reviewed_not_excluded(self):
  import json
  from portable_physical_lock_arena_source_contract import project_sources
  data=json.loads((ROOT/'tests/fixtures/portable-physical-lock-arena-source-delta.json').read_text());out=project_sources(ROOT)
  for name in ('app/portable_wire_layout.py','scripts/run-metal-probe.swift'):
   self.assertEqual(out[name],data['sources'][name]['baseline'])
   with self.assertRaisesRegex(AssertionError,'Unreviewed'):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// unreviewed'})
 def test_no_cpu_period_or_shot_schedule_is_used_for_packing(self):
  import portable_backend
  from calculator import timeline
  with patch.object(timeline,'simulate',side_effect=AssertionError('No simulation in packing')),patch.object(portable_backend,'build',side_effect=AssertionError('GPU forbidden')),patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')):
   entries,data=suite.prepare();self.assertEqual(len(entries),10);self.assertEqual(sum(d is not None for _,_,d in entries),6)
   for _,w,domain in entries:
    if domain:
     c,m,b=domain;self.assertTrue(all(w[suite.L['COMMAND_BASE']+i*8] not in (45,46) for i in range(w[2])))
 def test_source_inverse_preserves_old_state_and_weapon_contracts(self):
  import json
  from portable_physical_lock_source_contract import project_sources
  data=json.loads((ROOT/'tests/fixtures/portable-physical-lock-source-delta.json').read_text());old=project_sources(ROOT)
  for name,row in data['sources'].items():
   self.assertEqual(old[name],row['baseline'])
   with self.assertRaisesRegex(AssertionError,'Unreviewed'):project_sources(ROOT,{name:row['current']+'\n// mutation'})
if __name__=='__main__':unittest.main()
