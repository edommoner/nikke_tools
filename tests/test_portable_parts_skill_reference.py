"""Native packet/notification prerequisites; no portable admission yet."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,detail_gpu
from calculator import timeline
from portable_parts_skill_cases import fixtures
from portable_parts_skill_contracts import verify
from world_parts_skill_native import observe
from world_projectile_native import observe as plain_observe
s=importlib.util.spec_from_file_location('parts_reference_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
class PartsSkillReferenceTests(unittest.TestCase):
    def test_fifteen_literal_contracts_forbid_packing_and_gpu(self):
        def forbidden(*a,**k):raise AssertionError('GPU/packing forbidden')
        with patch.object(timeline,'simulate',forbidden):cases=fixtures()
        self.assertEqual(len(cases),15);before=copy.deepcopy(cases)
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',forbidden),patch.object(detail_gpu,'compile_effects',forbidden),patch.object(detail_gpu,'compile_full',forbidden):
            for case in cases:
                with self.subTest(case=case['name']):self.assertTrue(verify(case,observe(case)[0])['verified'])
        self.assertEqual(cases,before)
    def test_observer_preserves_full_native_state_and_trace(self):
        for case in fixtures():
            native,trace=observe(case);plain,plain_trace=plain_observe(case);native.pop('parts_skill_events');native.pop('parts_skill_accounting',None)
            with self.subTest(case=case['name']):self.assertEqual(native,plain);self.assertEqual(trace,plain_trace)
    def test_lost_part_wrong_order_extra_notice_and_double_factor_fail(self):
        case=fixtures()[2];native,_=observe(case);self.assertTrue(verify(case,native)['verified'])
        for edit in ('part','order','notice','notice-order','damage'):
            changed=copy.deepcopy(native);events=changed['parts_skill_events']
            if edit=='part':events.pop(next(i for i,e in enumerate(events) if e['kind']=='packet' and e['part']=='far'))
            elif edit=='order':
                indices=[i for i,e in enumerate(events) if e['kind']=='packet' and e['part']]
                events[indices[0]],events[indices[1]]=events[indices[1]],events[indices[0]]
            elif edit=='notice':events.append(copy.deepcopy(next(e for e in events if e['kind']=='named-hit')))
            elif edit=='notice-order':events.append(events.pop(next(i for i,e in enumerate(events) if e['kind']=='named-hit')))
            else:next(e for e in events if e['kind']=='packet' and e['part'])['damage']=4500
            with self.subTest(edit=edit),self.assertRaises(AssertionError):verify(case,changed)
    def test_profile_hook_restored_after_failure(self):
        previous=sys.getprofile()
        with patch('world_parts_skill_native.original_observe',side_effect=RuntimeError('injected failure')):
            with self.assertRaises(RuntimeError):observe(fixtures()[0])
        self.assertIs(sys.getprofile(),previous)

    def test_interrupt_credit_reach_time_and_gauge_cannot_silently_change(self):
        for case in fixtures():
            if not case.get('observe_parts_accounting'):continue
            native,_=observe(case)
            for edit in ('interrupt','reach','time','gauge'):
                changed=copy.deepcopy(native)
                if edit=='interrupt':changed['parts_skill_accounting']['interrupt_damage'][0]=9999
                elif edit=='gauge':changed['gauge']=1
                else:
                    packet=next(e for e in changed['parts_skill_events'] if e['kind']=='packet')
                    packet['reach' if edit=='reach' else 'time']=999
                with self.subTest(case=case['name'],edit=edit),self.assertRaises(AssertionError):verify(case,changed)
