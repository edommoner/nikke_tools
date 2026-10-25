"""Complete original cover definitions, world inputs and exact source boundaries."""
import importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('original_cover_test',ROOT/'research/verify-coordinate-original-cover-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class OriginalCoverTests(unittest.TestCase):
    def test_original_definitions_and_real_reload_cover_attacks(self):
        from calculator import timeline
        from portable_coordinate_kind_admission import KindAdmission
        from portable_parent_oracles import provider
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU schedule in GPU input')):rows,_=a.prepare()
        self.assertEqual(len(rows),6);old=KindAdmission(ROOT,'gpu/world_coordinate_original_shield_entry.slang');new=KindAdmission(ROOT,a.SOURCE)
        self.assertEqual([len(d[0]['effects']) for _,_,d in rows],[70]*3+[68]*3)
        for _,words,domain in rows:
            c,m,_,_=domain;self.assertEqual(set(m['binding_source_indices']),set(range(len(c['effects']))));self.assertEqual({r['kind'] for r in old.inspect(words)['unsupported']},{30});self.assertEqual(new.inspect(words)['unsupported'],[]);self.assertIs(provider(a,domain)[2],a.native_reference)
            self.assertEqual(c['duration'],6 if c['cover_witness']['scenario']=='full' else 46)
            self.assertEqual(len(c['patterns'])-1,c['cover_witness']['broken'])
    def test_observer_restores_on_native_failure(self):
        from calculator.buff_manager import BuffManager
        from world_original_cover_native import capture
        before=[BuffManager._register_all,BuffManager._dispatch_instant,BuffManager.revive_cover];c,_=a.prepare_case(a.fixtures()[0])
        with self.assertRaises(RuntimeError):
            with capture(c):raise RuntimeError('failed native')
        self.assertEqual(before,[BuffManager._register_all,BuffManager._dispatch_instant,BuffManager.revive_cover])
    def test_strict_source_inverse_and_transport(self):
        from portable_coordinate_original_cover_source_contract import project_sources,project_backend_source
        from portable_coordinate_original_slot_source_contract import project_sources as ancestor
        from portable_backend import validate_composed_stride
        d=json.loads((ROOT/'tests/fixtures/portable-coordinate-original-cover-source-delta.json').read_text());projected=project_sources(ROOT)
        for path,row in d['sources'].items():self.assertEqual(projected[path],row['baseline'])
        self.assertEqual(project_backend_source(ROOT),d['transport']['baseline']);self.assertNotIn('gpu/world_coordinate_original_cover_entry.slang',ancestor(ROOT))
        with self.assertRaises(AssertionError):project_sources(ROOT,{'gpu/coordinate_vital_kind_admission.slang':(ROOT/'gpu/coordinate_vital_kind_admission.slang').read_text()+'\n'})
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        with self.assertRaises(ValueError):validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS-1)
if __name__=='__main__':unittest.main()
