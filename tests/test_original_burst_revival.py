"""Full original B1 dispatch identity and actual multiple-candidate selection."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('original_burst_revival_test',ROOT/'research/verify-coordinate-original-burst-revival-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class OriginalBurstRevivalTests(unittest.TestCase):
    def test_all_original_definitions_pack_without_battle(self):
        from calculator import timeline
        from portable_parent_oracles import provider
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU battle in input')):entries,_=a.prepare()
        self.assertEqual(len(entries),4)
        for _,w,domain in entries:
            c,m,_,_=domain
            self.assertEqual(set(m['binding_source_indices']),set(range(len(c['effects']))))
            self.assertEqual(len(w),a.INPUT_WORDS)
            self.assertTrue(m['coordinate_original_input']['original_controls_preserved'])
            self.assertIs(provider(a,domain)[2],a.native_reference)

    def test_dispatch_observer_is_opt_in_and_checks_actual_row_owner(self):
        from calculator.buff_manager import BuffManager
        from world_revive_native import capture
        case=dict(names=a.fixtures()[0]['body']['squad'],owners=[0],effects=[dict(name='original',stat='revive')])
        manager=BuffManager.__new__(BuffManager)
        def dispatch(*args,**kw):return 'native'
        with patch.object(BuffManager,'_dispatch_instant',dispatch):
            with capture(case) as events:self.assertEqual(manager._dispatch_instant(dict(stat='revive'),case['names'][0],1),'native')
            self.assertEqual(events,[])
            case['observe_revival_attempts']=True;effect=dict(name='original',stat='revive',_portable_observer_row=0)
            with capture(case) as events:self.assertEqual(manager._dispatch_instant(effect,case['names'][0],2),'native')
            self.assertEqual(events,[dict(kind='revive-attempt',row=0,owner=0,time=2)])
            with self.assertRaisesRegex(ValueError,'identity mismatch'):
                with capture(case):manager._dispatch_instant(effect,case['names'][1],3)
            self.assertIs(BuffManager._dispatch_instant,dispatch)

    def test_clock_admission_inverse_and_wire_are_exact(self):
        import hashlib,json
        from portable_coordinate_original_clock_source_contract import project_sources,project_backend_source
        from portable_backend import validate_composed_stride
        baseline=json.loads((ROOT/'tests/fixtures/portable-coordinate-original-clock-source-delta.json').read_text())
        projected=project_sources(ROOT)
        for name,row in baseline['sources'].items():self.assertEqual(hashlib.sha256(projected[name].encode()).hexdigest(),row['baseline_sha256'])
        self.assertEqual(project_backend_source(ROOT),baseline['transport']['baseline'])
        with self.assertRaises(AssertionError):project_sources(ROOT,{'gpu/coordinate_sampling_runtime.slang':(ROOT/'gpu/coordinate_sampling_runtime.slang').read_text()+'\n'})
        with self.assertRaises(ValueError):project_backend_source(ROOT,(ROOT/'app/portable_backend.py').read_text()+'\n')
        validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
        with self.assertRaises(ValueError):validate_composed_stride(a.SOURCE,a.INPUT_WORDS-1,a.OUTPUT_WORDS)

    def test_actual_original_multiple_candidates_and_resume(self):
        row=a.fixtures()[-1];c,p=a.prepare_case(row);c.update(observe_skill_clocks=True,observe_revival_attempts=True,expected_down_owners=row['expected_down_owners'],expected_revived_owners=row['expected_revived_owners']);before=copy.deepcopy(p)
        _,m,b,d=a.compile_coordinate_battle(p);previous=sys.getprofile();n=a.native_reference((c,m,b,d))
        self.assertIs(sys.getprofile(),previous);self.assertEqual(p,before)
        self.assertTrue(a.verify_witness(c,n))
        wrong=copy.deepcopy(n);next(e for e in wrong['original_revival_events'] if e['kind']=='after-revive')['owner']=4
        with self.assertRaises(AssertionError):a.verify_witness(c,wrong)
if __name__=='__main__':unittest.main()
