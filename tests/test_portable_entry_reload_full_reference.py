"""Full-world entry-reload contracts and transparent native observation."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_backend,portable_runtime,portable_reference,detail_gpu
from calculator import timeline
from portable_entry_reload_cases import fixtures
from portable_entry_reload_contracts import verify
from world_entry_reload_native import observe,data_context
from world_projectile_native import observe as plain_observe
s=importlib.util.spec_from_file_location('entry_reference_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)


class FullEntryReloadReferenceTests(unittest.TestCase):
    def test_literal_cases_and_full_native_contracts_forbid_gpu_and_packing(self):
        def forbidden(*a,**kw):raise AssertionError('Battle/packing/GPU forbidden here')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_runtime,'compile_program',forbidden),patch.object(portable_backend,'build',forbidden):cases=fixtures()
        self.assertEqual(len(cases),35);before=copy.deepcopy(cases)
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',forbidden),patch.object(detail_gpu,'compile_effects',forbidden),patch.object(detail_gpu,'compile_full',forbidden):
            for case in cases:
                with self.subTest(case['name']):
                    native,_=observe(case);self.assertTrue(verify(case,native)['verified'])
        self.assertEqual(cases,before)

    def test_observation_preserves_every_existing_battle_field_and_skill_trace(self):
        for case in fixtures():
            with self.subTest(case['name']):
                with data_context(case):plain,trace=plain_observe(case)
                native,recorded=observe(case);events=native.pop('entry_reload')
                self.assertTrue(events['frames']);self.assertEqual(native,plain);self.assertEqual(recorded,trace)

    def test_cli_native_reference_and_source_identity_include_compatibility_layers(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'native.json'
            result=portable_reference.run_reference('entry-reload',out,write=cli.write,forbid_gpu=cli.forbid_gpu)
            self.assertTrue(result['cpu_reference_verified']);self.assertEqual(result['case_count'],35)
            self.assertFalse(result['calculation_verified']);self.assertFalse(result['gpu_supported'])
            report=json.loads(out.read_text());sources=report['source_sha256']
            for path in ('app/weapon_mode_runtime.py','app/reference_rewrite.py','research/portable_entry_reload_contracts.py','research/world_entry_reload_native.py'):
                self.assertIn(path,sources)
            self.assertEqual(result['gpu_calls'],dict(build=0,execute=0));self.assertEqual(result['packing_calls'],0)
            original=out.read_bytes()
            with self.assertRaises(FileExistsError):portable_reference.run_reference('entry-reload',out,write=cli.write,forbid_gpu=cli.forbid_gpu)
            self.assertEqual(out.read_bytes(),original)

    def test_contract_detects_lost_latch_wrong_base_query_or_premature_physical_action(self):
        case=fixtures()[0];native,_=observe(case)
        for edit in ('latch','base','missing-query','early-shot'):
            changed=copy.deepcopy(native);events=changed['entry_reload']
            if edit=='latch':events['frames'][1]['after']['entry_until']=0
            elif edit=='base':events['queries'][0]['base_reload']=.9
            elif edit=='missing-query':events['queries'].pop()
            else:events['frames'][0]['hits']=1
            with self.subTest(edit=edit),self.assertRaises(AssertionError):verify(case,changed)


if __name__=='__main__':unittest.main()
