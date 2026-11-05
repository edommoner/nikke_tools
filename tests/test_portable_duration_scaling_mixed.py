import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from portable_duration_scaling_extended_cases import extra_fixtures
from portable_duration_scaling_extended_contracts import verify
from world_duration_scaling_native import observe
from world_projectile_native import observe as plain
from world_frame_native import roster_names
from world_late_attack_random_native import capture_queries
from test_portable_duration_scaling_reference import read_calls

class DurationScalingMixedTests(unittest.TestCase):
    def test_all9_mixed_consumers_preserve_original_battle_trace_and_queries(self):
        cases=extra_fixtures();before=copy.deepcopy(cases);self.assertEqual(len(cases),9)
        for c in cases:
            with self.subTest(case=c['name']):
                with capture_queries(roster_names(c)) as (q,s),read_calls() as r:n,t=observe(c)
                verify(c,n);n.pop('duration_scaling')
                with capture_queries(roster_names(c)) as (oldq,olds),read_calls() as oldr:original,trace=plain(c)
                self.assertEqual((n,t),(original,trace));self.assertEqual((q,s,r),(oldq,olds,oldr))
        self.assertEqual(cases,before)
    def test_passive_zero_missing_source_and_raw_stack_refresh_are_distinct(self):
        data={c['name']:observe(c)[0]['duration_scaling'] for c in extra_fixtures()}
        pick=lambda suffix:data['duration-scaling-mixed-'+suffix]
        for suffix in ('passive-finite','passive-ref-expired','passive-zero-gauge'):self.assertEqual(len(pick(suffix)['checks']),17)
        self.assertEqual([r['reads'][0]['value'] for r in pick('source-decay')['checks']],[3,2,1])
        self.assertEqual([r['reads'][0]['value'] for r in pick('source-zero-shadows-stack')['checks']],[0]*3)
        self.assertEqual(len(pick('stack-operation-raw-refresh')['checks']),1);self.assertEqual(pick('stack-operation-raw-refresh')['carriers'],[])
        operations=pick('stack-operation-raw-refresh')['stack_refresh'];self.assertEqual(len(operations),3)
        before=next(r for r in operations[0]['before'] if r['name']=='duration-scaled');after=next(r for r in operations[0]['after'] if r['name']=='duration-scaled')
        self.assertEqual((before['stack'],before['expires_at']),(1,.15000000000000002));self.assertEqual((after['stack'],after['expires_at']),(2,.05))

if __name__=='__main__':unittest.main()
