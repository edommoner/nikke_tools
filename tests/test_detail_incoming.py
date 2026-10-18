"""Incoming inputs fail closed; real layer computation executes on the GPU."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('incoming_tests',ROOT/'scripts/verify-incoming-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_boss import WB,validate_world

class IncomingInputs(unittest.TestCase):
 def test_complete_fixture_compilation_never_invokes_cpu_combat(self):
  with patch.object(v.v.a.sim,'execute',side_effect=AssertionError('CPU combat invoked')):
   for name,b,extra in v.fixtures():
    saved=copy.deepcopy(b)
    with v.context(name,extra):c=v.v.a.evaluate({**b,'_compile_gpu_detail':True})
    validate_world(c['program']['world']);self.assertEqual(saved,b,name)
 def test_attack_bytecode_rejects_bad_indices_values_and_unknown_fields(self):
  b=v.body();b['enemy']['patterns']=[v.attack('slot:1')]
  c=v.v.a.evaluate({**b,'_compile_gpu_detail':True})
  for at,value in [(264,-1),(267,2),(WB+80,-1),(WB+80,0),(WB+81,-1),(WB+82,5),(WB+83,6),(WB+84,6),(WB+85,2),(WB+87,0),(WB+88,-1),(WB+89,1)]:
   w=copy.deepcopy(c['program']['world']);w[at]=value
   with self.assertRaises(ValueError,msg=str((at,value))):validate_world(w)
 def test_incoming_model_gaps_and_attached_debuffs_are_explicitly_rejected(self):
  b=v.body();b['enemy']['patterns']=[v.attack()]
  for stat in ('damage_reduction_pct','force_move','cover_def_pct'):
   with v.v.v.t.p.custom_effects({v.NAMES[0]:[v.B('gap',stat)]}):
    with self.assertRaisesRegex(v.v.g.UnsupportedDetail,'Incoming model gap'):v.v.a.evaluate({**b,'_compile_gpu_detail':True})
  b['enemy']['patterns'][0]['spec']['debuffs']=[{'stat':'atk_pct','value':-10,'duration':1}]
  with self.assertRaises((ValueError,v.v.g.UnsupportedDetail)):v.v.a.evaluate({**b,'_compile_gpu_detail':True})
  for key in ('coeff','atk'):
   b=v.body();p=v.attack();p['spec'][key]=0;b['enemy']['patterns']=[p]
   with self.assertRaises(ValueError):v.v.a.evaluate({**b,'_compile_gpu_detail':True})
 def test_equal_damage_does_not_hide_wrong_incoming_hits(self):
  cpu=dict(total_damage=1,members=[],base_stats={},burst_timeline=[],incoming_hits=[dict(target='a',hp=1)])
  gpu={**copy.deepcopy(cpu),'incoming_hits':[dict(target='b',hp=1)],'compute':{'backend':'cuda_detail'}}
  r=v.v.v.resolve_verification(gpu,cpu)
  self.assertEqual(r['compute']['backend'],'cpu');self.assertFalse(r['compute']['cpu_verification']['incoming_hits_equal'])
 def test_log_and_rng_queries_reject_invalid_addresses_before_cuda(self):
  b=v.body(1);b['enemy']['patterns']=[v.attack()];c=v.v.a.evaluate({**b,'_compile_gpu_detail':True})
  for event,arg in [(117,-1),(117,4096),(117,.5),(118,-1),(118,14),(110,-1),(110,14)]:
   script=[[0,4,0,0,0,-1,0,0],[1,5,0,0,0,-1,0,0],[1,2,event,0,arg,0,0,0]]
   with self.assertRaises(ValueError):v.v.g.run(None,[c['program']],script,[c['enemy']],[c['base_stats']])

class IncomingGPU(unittest.TestCase):
 def test_frame_witnesses_do_not_change_combat_or_either_random_stream(self):
  b=v.body();b['_debug_boss_frames']=True;b['enemy']['patterns']=[v.attack('random:2',hits=8,interval=.5)]
  extra={v.NAMES[0]:[v.B('random capture','atk_caster_based_pct',17,'allies_random:2',event='every:0.5s',duration=.6)]}
  d=v.v.v.Cuda()
  try:
   with v.context('controlled',extra):
    first=v.v.g.evaluate_full(d,v.v.a.evaluate({**b,'_compile_gpu_detail':True}),module_backend='native')
    b['_debug_boss_frames']=False;b['_debug_incoming_frames']=False
    second=v.v.g.evaluate_full(d,v.v.a.evaluate({**b,'_compile_gpu_detail':True}),module_backend='native')
   for key in ('total_damage','members','burst_timeline','incoming_hits','_random_state','_boss_random_state','_incoming_state'):self.assertEqual(first[key],second[key],key)
  finally:d.close()
 def test_target_rules_layer_order_and_complete_squads(self):
  d=v.v.v.Cuda()
  try:rows=[v.compare(d,n,b,e,'native') for n,b,e in list(v.fixtures(quick=True))+[f for f in v.fixtures() if f[0].startswith('lowest-cover-') or f[0]=='raw-아니스-incoming']]
  finally:d.close()
  self.assertTrue(all(r['passed'] for r in rows),[r for r in rows if not r['passed']])
 def test_true_down_matches_cpu_and_context_recovers(self):
  b=v.body(1);b['enemy']['patterns']=[v.attack(atk=100000000)]
  d=v.v.v.Cuda()
  try:
   gpu=v.v.g.evaluate_full(d,v.v.a.evaluate({**b,'_compile_gpu_detail':True}),module_backend='native')
   cpu=v.v.a.evaluate(b)
   self.assertTrue(v.v.v.resolve_verification(gpu,cpu)['compute']['cpu_verification']['matched'])
   self.assertTrue(gpu['_down_mask'])
   n,b,e=next(v.fixtures(quick=True));self.assertTrue(v.compare(d,n,b,e,'native')['passed'])
  finally:d.close()
 def test_log_and_pending_shot_overflows_reject_and_context_recovers(self):
  d=v.v.v.Cuda()
  try:
   for patterns in [[v.attack('all',hits=820,interval=0)],[{**v.attack('all',hits=40,interval=0),'id':'attack'+str(i)} for i in range(32)]]:
    b=v.body(1);b['enemy']['patterns']=patterns
    with self.assertRaisesRegex(RuntimeError,r'\[512\]'):v.v.g.evaluate_full(d,v.v.a.evaluate({**b,'_compile_gpu_detail':True}),module_backend='native')
   n,b,e=next(v.fixtures(quick=True));self.assertTrue(v.compare(d,n,b,e,'native')['passed'])
  finally:d.close()

if __name__=='__main__':unittest.main()
