from cpu_reference_guard import forbid_execution
import engine_worker,portable_backend,portable_runtime,detail_gpu
"""Full-world entry-reload contracts and transparent native observation."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from calculator import timeline
from portable_entry_reload_cases import fixtures
from portable_entry_reload_contracts import verify
from world_entry_reload_native import observe,data_context
from world_projectile_native import observe as plain_observe


class FullEntryReloadReferenceTests(unittest.TestCase):
    pass

    def test_observation_preserves_every_existing_battle_field_and_skill_trace(self):
        for case in fixtures():
            with self.subTest(case['name']):
                with data_context(case):plain,trace=plain_observe(case)
                native,recorded=observe(case);events=native.pop('entry_reload')
                self.assertTrue(events['frames']);self.assertEqual(native,plain);self.assertEqual(recorded,trace)


    def test_contract_detects_lost_latch_wrong_base_query_or_premature_physical_action(self):
        case=fixtures()[0];native,_=observe(case)
        for edit in ('latch','base','missing-query','early-shot'):
            changed=copy.deepcopy(native);events=changed['entry_reload']
            if edit=='latch':events['frames'][1]['after']['entry_until']=0
            elif edit=='base':events['queries'][0]['base_reload']=.9
            elif edit=='missing-query':events['queries'].pop()
            else:events['frames'][0]['hits']=1
            with self.subTest(edit=edit),self.assertRaises(AssertionError):verify(case,changed)

    def test_literal_cases_and_full_native_contracts_forbid_gpu_and_packing(self):
        def forbidden(*a,**kw):raise AssertionError('Battle/packing/GPU forbidden here')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_runtime,'compile_program',forbidden),patch.object(portable_backend,'build',forbidden):cases=fixtures()
        self.assertEqual(len(cases),35);before=copy.deepcopy(cases)
        with forbid_execution(),patch.object(portable_runtime,'compile_program',forbidden),patch.object(detail_gpu,'compile_effects',forbidden),patch.object(detail_gpu,'compile_full',forbidden):
            for case in cases:
                with self.subTest(case['name']):
                    native,_=observe(case);self.assertTrue(verify(case,native)['verified'])
        self.assertEqual(cases,before)



if __name__=='__main__':unittest.main()
