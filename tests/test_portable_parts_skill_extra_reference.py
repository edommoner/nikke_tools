"""Range precedence and accounting are independent of GPU representation."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,detail_gpu
from calculator import timeline
from portable_parts_skill_extra_cases import fixtures
from portable_parts_skill_contracts import verify
from world_parts_skill_native import observe
from world_projectile_native import observe as plain_observe
s=importlib.util.spec_from_file_location('parts_extra_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
class PartsSkillExtraTests(unittest.TestCase):
    def test_ten_independent_contracts_forbid_gpu_and_packing(self):
        def forbidden(*a,**k):raise AssertionError('GPU/packing forbidden')
        with patch.object(timeline,'simulate',forbidden):cases=fixtures()
        self.assertEqual(len(cases),10);before=copy.deepcopy(cases)
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',forbidden),patch.object(detail_gpu,'compile_effects',forbidden),patch.object(detail_gpu,'compile_full',forbidden):
            for case in cases:
                with self.subTest(case=case['name']):self.assertTrue(verify(case,observe(case)[0])['verified'])
        self.assertEqual(cases,before)
    def test_no_native_state_or_trace_changes_from_observation(self):
        for case in fixtures():
            native,trace=observe(case);plain,other=plain_observe(case);native.pop('parts_skill_events');native.pop('parts_skill_accounting')
            with self.subTest(case=case['name']):self.assertEqual(native,plain);self.assertEqual(trace,other)
    def test_interrupt_credit_is_rejected_when_lost(self):
        case=fixtures()[0];native,_=observe(case)
        changed=copy.deepcopy(native);changed['parts_skill_accounting']['interrupt_damage'][0]=0
        with self.assertRaises(AssertionError):verify(case,changed)
    def test_pending_body_only_is_an_explicit_reference_gap(self):
        case=next(c for c in fixtures() if c['contract'].get('reference_model_gap'));native,_=observe(case);self.assertTrue(verify(case,native)['reference_model_gap'])
        changed=copy.deepcopy(native);next(e for e in changed['parts_skill_events'] if e['kind']=='packet')['part_damage']=4500
        with self.assertRaises(AssertionError):verify(case,changed)
        changed=copy.deepcopy(native);changed['parts_skill_events'].pop(next(i for i,e in enumerate(changed['parts_skill_events']) if e['kind']=='packet'))
        with self.assertRaises(AssertionError):verify(case,changed)

    def test_nonsaturating_healing_detects_missing_and_duplicate_packets(self):
        for case in fixtures():
            if 'unsaturated' not in case['name']:continue
            native,_=observe(case)
            for delta in (-300,300):
                changed=copy.deepcopy(native);changed['allies'][0]['hp']+=delta
                with self.subTest(case=case['name'],delta=delta),self.assertRaises(AssertionError):verify(case,changed)
