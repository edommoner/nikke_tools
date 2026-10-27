"""Actual shot clocks own the named capacity lifetime; no supplied schedules."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
from portable_effect_target_count_shot_cases import fixtures
from portable_heavyarms_lock_cases import source_definitions
from portable_effect_target_count_shot_specs import compile_case,HEAD,TRACE,CAPACITY,WORDS,INPUT,OUTPUT
from world_effect_target_count_shot_native import observe
from portable_specs import LIMITS as L,FIELDS as F
from effect_target_count_policy import MODEL

class NamedTargetCountShotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('count_shots_test',ROOT/'research/verify-target-count-shots.py');cls.adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.adapter)
        cls.cases=fixtures();cls.observed=[observe(c) for c in cls.cases]
    def test_original_definition_is_unchanged_and_two_actual_shots_remove_it(self):
        for c,n in zip(self.cases[:2],self.observed[:2]):
            self.assertEqual(c['effects'][0],source_definitions()[20]);self.assertTrue(c['target_count_original_definition'])
            active=[e for e in n['target_count_shots'] if e['who']==0 and e['before']['remaining']]
            self.assertEqual([(e['before']['remaining'],e['after']['remaining']) for e in active],[(2,1),(1,0)])
            self.assertEqual([e['before']['capacity'] for e in active],[15,15]);self.assertEqual(active[-1]['after']['capacity'],5)
    def test_same_frame_non_bound_and_attack_bound_use_actual_native_rule(self):
        ordinary=[e for e in self.observed[2]['target_count_shots'] if e['who']==0 and e['before']['remaining']]
        attack=[e for e in self.observed[3]['target_count_shots'] if e['who']==0 and e['before']['remaining']]
        self.assertEqual([(e['before']['remaining'],e['after']['remaining']) for e in ordinary],[(2,2),(2,1),(1,0)])
        self.assertTrue(ordinary[0]['before']['skipped']);self.assertEqual([(e['before']['remaining'],e['after']['remaining']) for e in attack],[(2,1),(1,0)])
        self.assertFalse(attack[0]['before']['skipped'])
    def test_multiple_pellets_muzzles_and_allied_clocks_do_not_multiply_consumption(self):
        n=self.observed[0];shots=[s for s in n['battle']['projectile_shots'] if s['owner']==0];consumed=[e for e in n['target_count_shots'] if e['who']==0]
        self.assertTrue(any(s['pellets']==3 and s['muzzles']==2 for s in shots));self.assertEqual(len(shots),len(consumed))
        n=self.observed[4];retired={who:next(e['time'] for e in n['target_count_shots'] if e['who']==who and e['before']['remaining'] and not e['after']['remaining']) for who in (0,1)}
        self.assertNotEqual(retired[0],retired[1])
    def test_pack_is_static_preserves_exact_definition_and_has_no_trace_input(self):
        import portable_backend
        from calculator import timeline
        c=self.cases[0];before=copy.deepcopy(c)
        def forbidden(*a,**kw):raise AssertionError('Battle/GPU during physical packing')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_backend,'build',forbidden),patch.object(portable_backend,'execute',forbidden):
            w,m,_=compile_case(self.adapter.parent,c,model=MODEL)
        self.assertEqual(c,before);self.assertEqual(m['named_count_physical']['original_definition'],source_definitions()[20]);self.assertEqual(len(w),INPUT)
        at=L['DEFINITION_BASE']+m['named_count_physical']['row']*L['DEFINITION_WORDS'];self.assertEqual(w[at+F['STAT']],93)
        self.assertEqual(TRACE+CAPACITY*WORDS,L['QUERY_BASE']+L['COMMANDS']*L['QUERY_WORDS']);self.assertGreaterEqual(HEAD,L['QUERY_BASE']+L['QUERY_WORDS'])
    def test_registered_adapter_retains_whole_battle_comparator_and_raw_rejections(self):
        entries,data=self.adapter.prepare();self.assertEqual((len(entries),sum(d is not None for _,_,d in entries)),(9,5));self.assertEqual(len(data),(1+9*INPUT)*4)
        self.assertEqual(OUTPUT,786432)
    def test_charge_literal_disagreement_is_rejected_before_battle_or_gpu(self):
        from calculator import timeline
        import portable_backend
        c=copy.deepcopy(self.cases[1]);c['post_fire_delays'][0]=.2
        def forbidden(*a,**kw):raise AssertionError('Execution before static clock validation')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_backend,'build',forbidden),patch.object(portable_backend,'execute',forbidden),self.assertRaisesRegex(ValueError,'post-fire delays differ'):
            compile_case(self.adapter.parent,c,model=MODEL)
    def test_modified_battle_cannot_be_hidden_by_capacity_observer(self):
        import world_effect_target_count_shot_native as observer
        original=observer.baseline;calls=[]
        def corrupt(case):
            result,trace=original(case);calls.append(1)
            return (dict(result,changed=True) if len(calls)==1 else result),trace
        with patch.object(observer,'baseline',side_effect=corrupt),self.assertRaisesRegex(AssertionError,'changed complete native'):
            observe(self.cases[0])
    def test_physical_hooks_inverse_is_exact_and_rejects_unreviewed_changes(self):
        from portable_effect_target_count_shot_source_contract import project_sources,ledger
        data=ledger(ROOT);old=project_sources(ROOT)
        for name,row in data['sources'].items():
            self.assertEqual(old[name],row['baseline'])
            with self.subTest(name=name),self.assertRaisesRegex(AssertionError,'Unreviewed'):
                project_sources(ROOT,{name:row['current']+'\n// mutation'})
        for name in data['added_sources']:
            with self.subTest(name=name),self.assertRaisesRegex(AssertionError,'Unreviewed'):
                project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// mutation'})

if __name__=='__main__':unittest.main()
