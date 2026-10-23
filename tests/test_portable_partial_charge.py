"""Tap wire admission, strict source deltas and unchanged state capacities."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_backend
from calculator import timeline
from portable_specs import LIMITS as L
from portable_partial_charge_source_contract import project_sources,ledger
from portable_charge_control_specs import compile_policy,CLICK_BASE


def verifier():
 s=importlib.util.spec_from_file_location('partial_unit',ROOT/'research/verify-world-partial-charge-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class PartialChargeTests(unittest.TestCase):
 def test_all_native_inputs_pack_without_battle_or_gpu_and_negatives_are_real(self):
  def forbidden(*a,**k):raise AssertionError('Static packing executed battle/GPU')
  with patch.object(timeline,'simulate',forbidden),patch.object(portable_backend,'execute',forbidden):rows,data=verifier().prepare()
  self.assertEqual(len(rows),45);self.assertEqual(len(data),4+45*104400*4)
  for name,w,domain in rows[:23]:
   p=L['WORLD_CONTROL_INPUT_BASE'];case=domain[0];owner=case['contract']['owner']
   if name.endswith('automatic-full-only'):self.assertEqual(w[p+1:p+2],[1]);self.assertEqual(w[p+5],0)
   else:
    self.assertEqual(w[p+1],2);self.assertEqual(w[p+5],1<<owner);self.assertEqual(w[p+CLICK_BASE+owner*8*16],1)
  self.assertTrue(all(w!=rows[0][1] for _,w,_ in rows[23:]))
  self.assertEqual((L['WORLD_CONTROL_STATE_BASE'],L['OUTPUT_WORDS']),(653160,159744))

 def test_zero_negative_and_unresolved_counter_semantics_are_explicit(self):
  rows,_=verifier().prepare()
  for name in ('zero-clamped','negative-clamped','unresolved-template'):
   _,w,domain=next(r for r in rows if r[0]=='nonfull-charge-'+name);at=L['EVENT_BASE']+L['EVENT_WORDS']
   self.assertEqual(w[at],40);self.assertEqual(w[at+3],1);self.assertEqual(w[at+7],2 if name=='unresolved-template' else 1)

 def test_source_delta_rejects_removed_paths_and_wrong_full_flag(self):
  project_sources(ROOT)
  for name,row in ledger(ROOT)['sources'].items():
   text=(ROOT/name).read_text()
   for c in row['changes']:
    bad=text.replace(c['current'],c['baseline'],1);self.assertNotEqual(text,bad)
    with self.assertRaises(AssertionError):project_sources(ROOT,{name:bad})
  name='gpu/weapon_frame_phases.slang';text=(ROOT/name).read_text();bad=text.replace('PARTIAL_IS_FULL(w)?11:40','11');self.assertNotEqual(text,bad)
  with self.assertRaises(AssertionError):project_sources(ROOT,{name:bad})

 def test_state_rejects_input_addresses_and_unknown_rows(self):
  import array
  from portable_partial_charge_state import validate_state
  rows,_=verifier().prepare();policy=rows[0][2][1]['_control_policy'];block=array.array('I',[0])*786432;at=L['WORLD_CONTROL_STATE_BASE']
  block[at+17]=1;validate_state(block,policy)
  for offset,value in [(17,123400),(17,2),(18,2),(19,2),(23,2)]:
   bad=array.array('I',block);bad[at+offset]=value
   with self.assertRaises(AssertionError):validate_state(bad,policy)

 def test_real_preparation_keeps_all77_effects_and_bindings(self):
  s=importlib.util.spec_from_file_location('partial_real_unit',ROOT/'research/verify-world-partial-charge-rosters-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  def forbidden(*a,**k):raise AssertionError('Real static packing executed battle/GPU')
  with patch.object(timeline,'simulate',forbidden),patch.object(portable_backend,'execute',forbidden):rows,data=m.prepare()
  self.assertEqual(len(rows),4)
  for _,w,(case,p,_,meta) in rows:
   original=m.real.engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True))
   self.assertEqual(p['effects'],original['effects']);self.assertEqual(len(p['effects']),77);self.assertEqual(len(meta['effects']),77)
   self.assertEqual(sorted(meta['binding_source_indices']),list(range(77)));self.assertFalse(p['cpu_battle_executed'])

 def test_control_timing_is_literal_and_rejects_boolean_nonfinite_and_zero_hold(self):
  rows,_=verifier().prepare();_,w,(case,meta,bindings)=rows[0]
  # The static normalizer records five authored durations; neither shot times
  # nor a computed full/partial decision belong in the immutable input.
  from portable_charge_control_specs import normalize_static_controls
  from world_frame_native import authored_metadata,roster_names
  names=roster_names(case);chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},control=c) for n,c in zip(names,case['controls'])]
  with patch.dict(timeline._NIKKE,authored_metadata(case)):
   norm=normalize_static_controls(chars,case['base_atk'],case['enemy'],case['control_mode'])
  self.assertEqual(set(norm['owners'][0]['clicks'][0]['tap_timing']),{'hold','charge','release','post','full_charge_interval'})
  for key,value in [('hold',0),('charge',True),('post',float('nan')),('release',float('inf')),('full_charge_interval',-1)]:
   n=copy.deepcopy(norm);n['owners'][0]['clicks'][0]['tap_timing'][key]=value
   with self.assertRaises(ValueError):compile_policy(n,[],names,meta['states'],0)


if __name__=='__main__':unittest.main()
