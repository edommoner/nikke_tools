import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
s=importlib.util.spec_from_file_location('live_world_tests',ROOT/'scripts/verify-live-parts-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from detail_world import read_parts,prepare_enemy

class WorldInputTests(unittest.TestCase):
 def test_parts_schema_is_strict_and_does_not_mutate_the_request(self):
  enemy={'def':31784,'parts':[{'name':'砲台','hp':0,'reach':2}]};saved=copy.deepcopy(enemy)
  prepared=prepare_enemy(enemy);self.assertEqual(enemy,saved);self.assertNotIn('parts',prepared)
  self.assertEqual(prepared['patterns'][0]['targets'][0]['emit_on_destroy'],['event:part_destroy'])
  for parts in [[{'name':'x','hp':True,'reach':1}],[{'name':'x','hp':1,'reach':True}],[{'name':'x','hp':-1,'reach':2}],[{'name':'x','hp':0,'reach':6}],[{'name':'x','hp':0,'reach':2,'ignored':1}],[{'name':'x','hp':1,'reach':1}]*2]:
   with self.assertRaises(ValueError):read_parts(parts)
 def test_real_cpu_and_compiled_world_keep_fixed_parts_and_original_input(self):
  body=v.p.body_for(['레드 후드','리타','크라운','앨리스','모더니아'],8,True);body['enemy']['parts']=[dict(name='near',hp=0,reach=1),dict(name='far',hp=5,reach=2)]
  saved=copy.deepcopy(body);cpu=v.p.a.evaluate(body);compiled=v.p.a.evaluate({**body,'_compile_detail':True})
  self.assertEqual(body,saved);self.assertGreater(cpu['parts_state'][0]['damage'],0);self.assertFalse(cpu['parts_state'][0]['destroyed']);self.assertTrue(cpu['parts_state'][1]['destroyed'])
  self.assertEqual(len(compiled['enemy']),68);self.assertEqual(compiled['enemy'][2],2)

class LivePartsGPUTests(unittest.TestCase):
    pass

if __name__=='__main__':unittest.main()
