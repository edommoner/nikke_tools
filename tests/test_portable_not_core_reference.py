"""Real native context and accumulator contracts without GPU admission."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker,portable_backend
from portable_not_core_cases import fixtures,synthetic_fixtures
from portable_not_core_contracts import verify
from world_not_core_native import observe
from world_projectile_native import observe as plain
from world_late_attack_random_native import capture_queries
from world_frame_native import roster_names


class NotCoreReferenceTests(unittest.TestCase):
    def test_all27_observers_preserve_original_battle_trace_and_semantic_queries(self):
        cases=fixtures();before=copy.deepcopy(cases);self.assertEqual(len(cases),27)
        s=importlib.util.spec_from_file_location('not_core_test_real',ROOT/'research/verify-world-projectile-rosters.py');real=importlib.util.module_from_spec(s);s.loader.exec_module(real)
        with patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')):
            for c in cases:
                with self.subTest(case=c['name']):
                    names=c['body']['squad'] if 'body' in c else roster_names(c)
                    with capture_queries(names) as (queries,samples):n,t=observe(c)
                    verify(c,n);n.pop('not_core_condition')
                    with capture_queries(names) as (original_queries,original_samples):
                        if 'body' in c:
                            battle,shots=real.native_reference(c['body']);expected=dict(battle=battle,projectile_shots=shots);trace=[]
                        else:expected,trace=plain(c)
                    self.assertEqual((n,t),(expected,trace));self.assertEqual(queries,original_queries);self.assertEqual(samples,original_samples)
        self.assertEqual(cases,before)

    def test_context_absence_condition_order_and_budget_are_distinct(self):
        cases={c['name']:c for c in synthetic_fixtures()}
        def inspect(label):return observe(cases['not-core-'+label])[0]['not_core_condition']
        self.assertEqual(sum(r['result'] for r in inspect('zero-core')['checks']),3)
        core=inspect('guaranteed-core');self.assertEqual(sum(r['result'] for r in core['checks']),0);self.assertTrue(core['states'])
        absent=inspect('attack-context-absent');self.assertTrue(all(r['core_fraction'] is None and r['result'] for r in absent['checks']))
        self.assertEqual(inspect('first-condition-false')['states'],[]);self.assertTrue(inspect('last-condition-false')['states'])
        self.assertEqual(inspect('probability-first-zero')['states'],[]);self.assertTrue(inspect('probability-last-zero')['states'])
        budget=inspect('activation-budget');self.assertEqual(len(budget['checks']),3);self.assertEqual(sum(r['result'] for r in budget['checks']),2);self.assertEqual([c['stack'] for c in budget['carriers']],[1])
        duplicate=inspect('duplicate-condition');self.assertEqual(len(duplicate['states']),1);self.assertEqual(sum(r['result'] for r in duplicate['checks']),1)
        independent=inspect('independent-probability')['checks'][-1]['after'];self.assertNotEqual(independent['not_core'],independent['prob'])

    def test_nested_notify_clears_child_context_and_restores_parent(self):
        n,_=observe(next(c for c in synthetic_fixtures() if c['name']=='not-core-nested-notify-restores-parent'));checks=n['not_core_condition']['checks']
        parents=[r for r in checks if r['name']=='noncore-parent'];siblings=[r for r in checks if r['name']=='noncore-sibling'];children=[r for r in checks if r['name']=='noncore-child']
        self.assertEqual([r['core_fraction'] for r in parents],[r['core_fraction'] for r in siblings]);self.assertTrue(children)
        self.assertTrue(all(r['core_fraction'] is None and r['result'] and r['notify_depth']>1 for r in children))

    def test_context_accumulator_budget_and_trace_faults_are_rejected(self):
        c=synthetic_fixtures()[2];n,t=observe(c)
        changes=[lambda d:d['checks'][0].update(core_fraction=0.),lambda d:d['checks'][0].update(result=True),lambda d:d['checks'][0]['before']['not_core'].update(created=True),lambda d:d['checks'][0]['after']['not_core'].update(value=0.),lambda d:d['states'][0].update(value=0.),lambda d:d['carriers'][0].update(stack=99),lambda d:d.update(trace_sha256='0'*64)]
        for i,change in enumerate(changes):
            bad=copy.deepcopy(n);change(bad['not_core_condition'])
            with self.subTest(fault=i),self.assertRaises(AssertionError):verify(c,bad)

    def test_full_real_profiles_reach_actual_gauge_handlers(self):
        cases=[c for c in fixtures() if 'body' in c]
        for c,count in zip(cases,(3,34)):
            with self.subTest(case=c['name']):
                n,t=observe(c);verify(c,n);data=n['not_core_condition']
                self.assertEqual(data['definitions'],79);self.assertEqual(len(data['instant_calls']),count)
                self.assertTrue(all(r['stat']=='gauge_charge' and r['name']=='경험치 2' for r in data['instant_calls']))


if __name__=='__main__':unittest.main()
