"""No schedule injection, no arena borrowing, exact source inverses."""
import importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
spec=importlib.util.spec_from_file_location('physical_cover_test',ROOT/'research/verify-physical-lock-cover.py')
suite=importlib.util.module_from_spec(spec);spec.loader.exec_module(suite)

class PhysicalCoverTests(unittest.TestCase):
    def test_manual_arena_is_after_all_snapshots_inside_existing_wire(self):
        from portable_physical_lock_cover_layout import check,BASE,WORDS,OUTPUT
        from portable_physical_lock_layout import END
        r=check(ROOT);self.assertEqual(BASE,END);self.assertLessEqual(BASE+WORDS,OUTPUT)
        self.assertEqual(r['actor_set_capacity'],32)
        from portable_backend import validate_composed_stride
        validate_composed_stride(suite.SOURCE,suite.INPUT,suite.OUTPUT)
        with self.assertRaisesRegex(ValueError,'complete lock/manual arena'):validate_composed_stride(suite.SOURCE,suite.INPUT,suite.OUTPUT-1)

    def test_all_old_inputs_retained_and_packing_never_simulates(self):
        from calculator import timeline
        import portable_backend
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU schedule')),patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')):
            old,_=suite.parent.prepare();rows,data=suite.prepare()
            self.assertEqual(len(rows),23);self.assertEqual(sum(d is not None for _,_,d in rows),11)
            self.assertEqual([(n,w) for n,w,_ in rows[:10]],[(n,w) for n,w,_ in old])

    def test_manual_version_and_cover_tag_are_from_common_literal_producer(self):
        from portable_specs import LIMITS as L
        from portable_charge_control_specs import SEQUENCE_BASE
        for case in suite.fixtures():
            words,meta,_=suite.compile_case(case);at=L['WORLD_CONTROL_INPUT_BASE']
            self.assertEqual(words[at+1],3);self.assertEqual(words[at+6],meta['states']['cover'])
            self.assertEqual(words[at+7],0x4d435631)
            who=case['cover_contract']['owner'];self.assertEqual(words[at+SEQUENCE_BASE+who*64+4],1)

    def test_source_inverse_is_complete_and_rejects_mutation(self):
        from portable_physical_lock_cover_source_contract import project_sources,project_backend_source
        ledger=json.loads((ROOT/'tests/fixtures/portable-physical-lock-cover-source-delta.json').read_text())
        old=project_sources(ROOT)
        for name,row in ledger['sources'].items():
            self.assertEqual(old[name],row['baseline'])
            with self.subTest(name=name),self.assertRaisesRegex(AssertionError,'Unreviewed'):
                project_sources(ROOT,{name:row['current']+'\n// mutation'})
        with self.assertRaisesRegex(ValueError,'Unreviewed'):project_backend_source(ROOT,(ROOT/'app/portable_backend.py').read_text()+'\n# mutation')

if __name__=='__main__':unittest.main()
