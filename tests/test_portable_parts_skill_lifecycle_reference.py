"""Snapshot and part-group landing contracts before GPU lowering."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,detail_gpu
from calculator import timeline
from portable_parts_skill_lifecycle_cases import fixtures
from portable_parts_skill_contracts import verify
from world_parts_skill_native import observe
from world_projectile_native import observe as plain
s=importlib.util.spec_from_file_location('parts_lifecycle_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)


class PartsLifecycleReferenceTests(unittest.TestCase):
    def test_literal_seven_contracts_do_not_pack_or_execute_gpu(self):
        def forbidden(*a,**k):raise AssertionError('No packing/GPU in native contracts')
        with patch.object(timeline,'simulate',forbidden):cases=fixtures()
        self.assertEqual(len(cases),7);before=copy.deepcopy(cases)
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',forbidden),patch.object(detail_gpu,'compile_effects',forbidden),patch.object(detail_gpu,'compile_full',forbidden):
            for case in cases:
                with self.subTest(case=case['name']):self.assertTrue(verify(case,observe(case)[0])['verified'])
        self.assertEqual(cases,before)

    def test_observer_preserves_existing_state_trace_and_parent_hook(self):
        calls=[]
        def parent(frame,event,arg):
            if frame.f_code is observe.__code__:calls.append(event)
        old=sys.getprofile();sys.setprofile(parent)
        try:
            for case in fixtures():
                native,trace=observe(case);unobserved,plain_trace=plain(case)
                native.pop('parts_skill_events');native.pop('parts_skill_lifecycle')
                self.assertEqual(native,unobserved);self.assertEqual(trace,plain_trace)
                self.assertIs(sys.getprofile(),parent)
        finally:sys.setprofile(old)
        self.assertIn('call',calls);self.assertIn('return',calls)

    def test_recomputed_part_damage_rebound_generation_and_child_reorder_fail(self):
        cases=fixtures()
        edits=[(cases[0],'amount'),(cases[3],'generation'),(cases[5],'child-order'),(cases[2],'expired-target')]
        for case,edit in edits:
            native,_=observe(case);self.assertTrue(verify(case,native)['verified']);changed=copy.deepcopy(native)
            if edit=='amount':next(e for e in changed['parts_skill_events'] if e['kind']=='packet' and e['part']=='near')['damage']=5000
            elif edit=='generation':next(e for e in changed['parts_skill_lifecycle'] if e['kind']=='part-open' and e['ordinal']==2)['ordinal']=1
            elif edit=='expired-target':changed['parts_skill_lifecycle'].append(dict(kind='part-capture',parts=['near','far'],time=.2))
            else:
                events=changed['parts_skill_lifecycle'];i=next(i for i,e in enumerate(events) if e['kind']=='part-destroy');j=next(j for j,e in enumerate(events) if e['kind']=='packet' and e['part']=='near');events[i],events[j]=events[j],events[i]
            with self.subTest(edit=edit),self.assertRaises(AssertionError):verify(case,changed)
