"""Charge source groups, immunity transitions, overflow and safe GPU bounds."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('charge_immune_tests',ROOT/'scripts/verify-charge-immunity-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class ChargeImmunityTests(unittest.TestCase):
    def test_independent_whole_squads_match_across_source_groups_and_transitions(self):
        device=v.Cuda()
        try:rows=v.verify(device,'native',quick=True)
        finally:device.close()
        self.assertEqual(len(rows),33)
        self.assertTrue(all(row['passed'] for row in rows),[r for r in rows if not r['passed']])

    def test_out_of_bounds_groups_reject_before_any_cuda_access(self):
        ref=json.loads((ROOT/'research/detail-charge-immunity-cpu-references.json').read_text(encoding='utf-8'))['cases'][0]
        with v.c.p.custom_effects(ref['authored_effects']):compiled=v.c.a.evaluate({**ref['input'],'_compile_gpu_detail':True})
        for invalid in [-1,v.detail_gpu.NE,.5]:
            program=copy.deepcopy(compiled['program'])
            next(row for row in program['effects'] if row[1]==0 and row[2]==20)[45]=invalid
            with self.assertRaisesRegex(ValueError,'charge quantization group'):
                v.detail_gpu.run(None,[program],[[0,2,103,0,20,0,0,0]],[compiled['enemy']],[compiled['base_stats']])

if __name__=='__main__':unittest.main()
