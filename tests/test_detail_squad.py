import importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('squad_tests',ROOT/'scripts/verify-squad-condition-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from detail_gpu import compile_effects

class SquadConditionTests(unittest.TestCase):
 def test_metadata_predicate_including_costume_and_unregistered_names(self):
  refs=json.loads((ROOT/'research/detail-squad-condition-cpu-references.json').read_text(encoding='utf-8'))
  for ref in refs['primitives']:
   names=list(ref['names'])
   while len(names)<5:names.append('unregistered padding '+str(len(names)))
   chars=[{'name':n,'_weapon':v.a.META.get(n,{}),'skill_levels':{'1':10,'2':10,'3':10}} for n in names]
   effect=v.r.E('squad predicate','buff','atk_pct',30,condition=['squad_ally_exists'])
   row=compile_effects(chars,[(effect,ref['caster'])])['effects'][0]
   self.assertEqual(row[15:18],[25,0,int(ref['expected'])],ref)

 def test_positive_and_negative_whole_squads_match_independent_cpu(self):
  device=v.Cuda()
  try:rows=v.verify(device,'native',quick=True)
  finally:device.close()
  self.assertEqual(len(rows),32)
  self.assertTrue(all(r['passed'] for r in rows),[r for r in rows if not r['passed']])
