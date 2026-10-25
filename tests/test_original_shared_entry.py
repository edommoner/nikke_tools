"""Stable existing-handler scope, exact legacy inversion and non-certifying inventory."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import nikke_gpu
from portable_coordinate_kind_admission import KindAdmission
class OriginalSharedTests(unittest.TestCase):
    def test_same_cover_inputs_and_native_provider(self):
        from calculator import timeline
        from portable_parent_oracles import provider
        a=nikke_gpu.open_suite(dict(suite='coordinate-original-shared'));old=nikke_gpu.open_suite(dict(suite='coordinate-original-cover'))
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU schedule in inputs')):rows,raw=a.prepare();prior,old_raw=old.prepare()
        self.assertEqual(raw,old_raw);self.assertEqual([r[0] for r in rows],[r[0] for r in prior])
        for _,words,domain in rows:
            self.assertIs(provider(a,domain)[2],a.native_reference);self.assertEqual(KindAdmission(ROOT,a.SOURCE).inspect(words)['unsupported'],[])
    def test_source_inverse_and_transport(self):
        from portable_coordinate_original_shared_source_contract import project_sources,project_backend_source
        from portable_coordinate_original_slot_source_contract import project_sources as ancestor
        from portable_backend import validate_composed_stride
        d=json.loads((ROOT/'tests/fixtures/portable-coordinate-original-shared-source-delta.json').read_text());out=project_sources(ROOT)
        for path,r in d['sources'].items():self.assertEqual(out[path],r['baseline'])
        self.assertEqual(project_backend_source(ROOT),d['transport']['baseline']);self.assertNotIn('gpu/world_coordinate_original_shared_entry.slang',ancestor(ROOT));validate_composed_stride('gpu/world_coordinate_original_shared_entry.slang',109968,1769856)
        with self.assertRaises(AssertionError):project_sources(ROOT,{'gpu/coordinate_vital_kind_admission.slang':(ROOT/'gpu/coordinate_vital_kind_admission.slang').read_text()+'\n'})
    def test_expanded_kinds_are_not_reported_as_character_certification(self):
        from portable_original_entry_inventory import run
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'inventory.json';r=run(p,write=nikke_gpu.write,forbid_gpu=nikke_gpu.forbid_gpu,source='gpu/world_coordinate_original_shared_entry.slang',comparison_source='gpu/world_coordinate_original_cover_entry.slang');report=json.loads(p.read_text())
        self.assertEqual((r['profile_count'],r['packed_profiles'],r['kind_rejected_profiles'],r['expanded_kind_profiles']),(266,247,0,8));self.assertEqual(r['forbidden_calls'],dict(cpu_battle=0,gpu=0));self.assertFalse(r['calculation_verified']);self.assertFalse(r['gpu_admission_verified']);self.assertEqual(r['full_character_verified'],0)
        self.assertEqual({r['operator']['kind'] for r in report['expanded_kind_operator_priorities']},{18,20,21,31,34,35,37});self.assertEqual(len(report['packing_failures']),19)
        expanded={(r['character'],r['favorite_stage']) for r in report['profiles'] if r.get('expanded_kind_effects')};classified={(p['character'],p['favorite_stage']) for c in report['expanded_kind_operator_priorities'] for p in c['profiles']};self.assertEqual(expanded,classified)
if __name__=='__main__':unittest.main()
