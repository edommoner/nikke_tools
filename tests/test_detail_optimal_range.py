"""Range extension must change live damage, not merely compile as a marker."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
s=importlib.util.spec_from_file_location('optimal_tests',ROOT/'scripts/verify-optimal-range-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
from detail_gpu import compile_effects,weapon_rows,UnsupportedDetail

class OptimalRangeCompilerTests(unittest.TestCase):
 def test_missing_range_metadata_rejects_effect_and_predicate(self):
  chars=v.oracle.characters(v.p.NAMES)
  for effect in [v.E('range','buff','optimal_range_min',50),v.E('predicate','buff','atk_pct',10,condition=['optimal_range'])]:
   with self.assertRaises(UnsupportedDetail):compile_effects(chars,[(effect,v.p.NAMES[0])])
 def test_owned_metadata_and_packed_bounds(self):
  body=v.p.body_for(v.p.NAMES,2,True);body['enemy']['distance']=30
  compiled=v.p.a.evaluate({**body,'_compile_gpu_detail':True})
  chars=compiled['program']['chars'];packed=weapon_rows(chars,compiled['base_stats'])
  self.assertEqual(packed[164:168],[15,35,30,2])
  bad=copy.deepcopy(chars);bad[0]['_detail_range']=[35,15,30]
  with self.assertRaises(ValueError):weapon_rows(bad,compiled['base_stats'])
  body['enemy'].pop('distance');compiled=v.p.a.evaluate({**body,'_compile_gpu_detail':True})
  self.assertEqual(weapon_rows(compiled['program']['chars'],compiled['base_stats'])[167],1)

class OptimalRangeGPUTests(unittest.TestCase):
 def test_native_primitives_and_complete_battles(self):
  d=v.Cuda()
  try:rows=v.verify(d,'native')
  finally:d.close()
  self.assertTrue(all(r['passed'] for r in rows),json.dumps([r for r in rows if not r['passed']],ensure_ascii=True))

if __name__=='__main__':unittest.main()
