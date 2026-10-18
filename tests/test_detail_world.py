import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
s=importlib.util.spec_from_file_location('live_world_tests',ROOT/'scripts/verify-live-parts-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from detail_world import read_parts,prepare_enemy
from gpu_service import resolve_verification

class WorldInputTests(unittest.TestCase):
 def test_parts_schema_is_strict_and_does_not_mutate_the_request(self):
  enemy={'def':31784,'parts':[{'name':'砲台','hp':0,'reach':2}]};saved=copy.deepcopy(enemy)
  prepared=prepare_enemy(enemy);self.assertEqual(enemy,saved);self.assertNotIn('parts',prepared)
  self.assertEqual(prepared['patterns'][0]['targets'][0]['emit_on_destroy'],['event:part_destroy'])
  for parts in [[{'name':'x','hp':True,'reach':1}],[{'name':'x','hp':1,'reach':True}],[{'name':'x','hp':-1,'reach':2}],[{'name':'x','hp':0,'reach':6}],[{'name':'x','hp':0,'reach':2,'ignored':1}],[{'name':'x','hp':1,'reach':1}]*2]:
   with self.assertRaises(ValueError):read_parts(parts)
 def test_equal_totals_with_wrong_part_state_are_rejected(self):
  cpu=dict(total_damage=100,members=[],base_stats={},burst_timeline=[],parts_state=[dict(name='x',destroyed=False)])
  gpu={**copy.deepcopy(cpu),'parts_state':[dict(name='x',destroyed=True)],'compute':{'backend':'cuda_detail'}}
  result=resolve_verification(gpu,cpu)
  self.assertEqual(result['compute']['backend'],'cpu');self.assertFalse(result['compute']['cpu_verification']['parts_state_equal'])
 def test_real_cpu_and_compiled_world_keep_fixed_parts_and_original_input(self):
  body=v.p.body_for(['레드 후드','리타','크라운','앨리스','모더니아'],8,True);body['enemy']['parts']=[dict(name='near',hp=0,reach=1),dict(name='far',hp=5,reach=2)]
  saved=copy.deepcopy(body);cpu=v.p.a.evaluate(body);compiled=v.p.a.evaluate({**body,'_compile_gpu_detail':True})
  self.assertEqual(body,saved);self.assertGreater(cpu['parts_state'][0]['damage'],0);self.assertFalse(cpu['parts_state'][0]['destroyed']);self.assertTrue(cpu['parts_state'][1]['destroyed'])
  self.assertEqual(len(compiled['enemy']),68);self.assertEqual(compiled['enemy'][2],2)

class LivePartsGPUTests(unittest.TestCase):
 def test_native_lifecycle_and_complete_battles(self):
  d=v.Cuda()
  try:rows=v.verify(d,'native',quick=True)
  finally:d.close()
  self.assertTrue(all(row['passed'] for row in rows),[row for row in rows if not row['passed']])
 def test_all_parts_destroyed_last_frame_and_full_32_target_mask(self):
  import random
  from detail_gpu import evaluate_full
  d=v.Cuda()
  try:
   for count,base_presence,duration,reach in [(1,False,4,1),(1,True,4,1),(32,False,4,5),(1,False,1,1),(1,False,4,5)]:
    body=v.p.body_for(v.NAMES,duration,True);body.update(seed=12345,burst_gauge_mode='accumulate',_debug_random_state=True)
    body['enemy'].update(has_parts=base_presence,parts=[dict(name='target'+str(i),hp=0 if reach==5 and count==1 else 5,reach=reach) for i in range(count)])
    owner=v.NAMES[2];effects=[v.E('area','damage','damage',100,'all_enemies',event='every:0.98s' if duration==1 else 'every:1s',hits_parts=True),v.E('part power','buff','part_dmg_pct',35),v.E('on destroy','buff','atk_pct',1,'all_allies',event='event:part_destroy',max_stack=32)]
    if count==1 and reach==5:effects=[v.E('pierce','buff','pierce_enabled',1),v.E('wide','buff','pierce_range',100)]
    with v.p.custom_effects({owner:effects}):
     gpu=evaluate_full(d,v.p.a.evaluate({**body,'_compile_gpu_detail':True}),module_backend='native');cpu=v.p.a.evaluate(body);rng=list(random.getstate()[1])
    result=resolve_verification(gpu,cpu)
    self.assertEqual(result['compute']['backend'],'cuda_detail',(count,base_presence,duration,reach,result['compute']))
    self.assertEqual(gpu['_random_state'],rng)
    if count==1 and reach==5:self.assertEqual(cpu['parts_state'][0]['damage'],0)
    else:self.assertTrue(all(p['destroyed'] for p in cpu['parts_state']))
  finally:d.close()

if __name__=='__main__':unittest.main()
