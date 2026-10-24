"""Caller-pool geometry order, static-only packing and complete output checks."""
import array,copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_coordinate_scene_specs import LAYOUT as L,compile_scene,source_matches
from portable_coordinate_scene_cases import fixtures
from world_coordinate_scene_native import observe
spec=importlib.util.spec_from_file_location('coordinate_scene_test_adapter',ROOT/'research/verify-coordinate-scene-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class CoordinateSceneTests(unittest.TestCase):
    def test_layout_and_static_pack_have_no_simulated_geometry_or_battle(self):
        from calculator import timeline
        from calculator.boss_pattern import BossScript
        self.assertTrue(source_matches());self.assertLessEqual(L['QUERIES']+L['OPS']*L['SNAPSHOT'],L['OUTPUT'])
        with patch.object(timeline,'simulate',side_effect=AssertionError('No battle input')),patch.object(BossScript,'_apply_geom',side_effect=AssertionError('No native target-list input')):
            for c in fixtures():words,meta=compile_scene(c);self.assertEqual(len(words),L['INPUT'])
        c=copy.deepcopy(fixtures()[-3]);c['patterns'][1]['targets'].append(dict(name='overflow',hp=1,x=0,y=0,r=1))
        with self.assertRaisesRegex(ValueError,'capacity'):compile_scene(c)
    def test_native_depth_birth_pattern_ordinal_generation_and_capacity(self):
        cases={c['name'].split('/')[-1]:c for c in fixtures()}
        n,_=observe(cases['same-depth-later-birth'])
        self.assertEqual([r[0] for r in n['snapshots'][0]['all']],[3,2,1])
        self.assertEqual([r[0] for r in n['snapshots'][-1]['all']],[2,1,3])
        self.assertEqual([r[3] for r in n['snapshots'][-1]['all']],[2,2,1])
        n,_=observe(cases['capacity127']);self.assertEqual(len(n['snapshots'][0]['all']),127);self.assertEqual(len(n['snapshots'][1]['all']),126)
        n,_=observe(cases['unbreakable']);self.assertEqual(len(n['snapshots'][1]['all']),3)
    def test_complete_output_detects_descriptor_owner_generation_and_tail_corruption(self):
        entries,_=a.prepare();self.assertEqual(len(entries),21);self.assertEqual(sum(d is not None for _,_,d in entries),10)
        domain=entries[2][2];out=a.expected_block(domain);a.compare(out,domain)
        for at in (L['DESC']+6,L['STATE'],L['QUERIES']+8+3,L['OUTPUT']-1):
            bad=array.array('I',out);bad[at]^=1
            with self.assertRaises(AssertionError):a.compare(bad,domain)
        rejected=array.array('I',[0])*L['OUTPUT'];rejected[0]=64
        for name,_,d in entries:
            if d is None:a.validate_rejection(rejected,name)
        rejected[-1]=1
        with self.assertRaises(AssertionError):a.validate_rejection(rejected,'reject/coordinate-scene-kind')
if __name__=='__main__':unittest.main()
