"""Original ammunition callbacks and gauge steps are measured, never injected."""
import copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('original_ammo_test',ROOT/'research/verify-coordinate-original-ammo-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class OriginalAmmoTests(unittest.TestCase):
    def test_all_definitions_pack_and_old_entry_rejects_before_gpu(self):
        from calculator import timeline
        from portable_coordinate_kind_admission import KindAdmission
        from portable_parent_oracles import provider
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU schedule in input')):rows,_=a.prepare()
        self.assertEqual(len(rows),4)
        old=KindAdmission(ROOT,'gpu/world_coordinate_original_resource_entry.slang');current=KindAdmission(ROOT,a.SOURCE)
        for _,words,domain in rows:
            case,metadata,_,_=domain
            self.assertEqual(set(metadata['binding_source_indices']),set(range(len(case['effects']))))
            self.assertTrue({r['kind'] for r in old.inspect(words)['unsupported']}<={13,14})
            self.assertTrue(old.inspect(words)['unsupported']);self.assertEqual(current.inspect(words)['unsupported'],[])
            self.assertIs(provider(a,domain)[2],a.native_reference)

    def test_positive_original_level_step_replenishes_real_bullets(self):
        row=a.fixtures()[0];case,prepared=a.prepare_case(row);case['ammo_witness']=row['ammo_witness'];before=copy.deepcopy(prepared)
        _,m,b,d=a.compile_coordinate_battle(prepared);previous=sys.getprofile();native=a.native_reference((case,m,b,d))
        self.assertIs(sys.getprofile(),previous);self.assertEqual(prepared,before)
        self.assertTrue(a.verify_witness(case,native))
        wrong=copy.deepcopy(native);wrong['original_resources']['notifications']=[]
        with self.assertRaises(AssertionError):a.verify_witness(case,wrong)

    def test_profile_is_restored_on_exception(self):
        from world_original_ammo_native import capture
        case,_=a.prepare_case(a.fixtures()[0]);previous=sys.getprofile()
        with self.assertRaisesRegex(RuntimeError,'native failure'):
            with capture(case):raise RuntimeError('native failure')
        self.assertIs(sys.getprofile(),previous)

    def test_source_inverse_and_complete_wire_are_exact(self):
        from portable_coordinate_original_ammo_source_contract import project_sources,project_backend_source
        from portable_coordinate_original_resource_source_contract import project_sources as parent_sources
        from portable_backend import validate_composed_stride
        baseline=json.loads((ROOT/'tests/fixtures/portable-coordinate-original-ammo-source-delta.json').read_text())
        projected=project_sources(ROOT)
        for name,row in baseline['sources'].items():self.assertEqual(projected[name],row['baseline'])
        self.assertNotIn('gpu/coordinate_vital_kind_admission.slang',parent_sources(ROOT),'File absent from old baseline must not leak into ancestor projection')
        self.assertEqual(project_backend_source(ROOT),baseline['transport']['baseline'])
        with self.assertRaises(AssertionError):project_sources(ROOT,{'gpu/coordinate_vital_kind_admission.slang':(ROOT/'gpu/coordinate_vital_kind_admission.slang').read_text()+'\n'})
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        with self.assertRaises(ValueError):validate_composed_stride(a.SOURCE,a.INPUT_WORDS-1,a.OUTPUT_WORDS)
if __name__=='__main__':unittest.main()
