from cpu_reference_guard import forbid_execution
import engine_worker,portable_backend,portable_runtime,detail_gpu
"""Native revival prerequisites; GPU and portable admission remain forbidden."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_revive_cases import fixtures
from world_revive_native import observe
from world_projectile_native import observe as unobserved
from portable_revive_contracts import verify


class RevivalReferenceTests(unittest.TestCase):
    pass

    def test_observer_preserves_entire_existing_native_result_and_trace(self):
        for c in fixtures():
            plain,trace=unobserved(c);recorded,recorded_trace=observe(c)
            events=recorded.pop('revival_events')
            self.assertEqual(bool(events),c['name']!='revive-alive-noop')
            self.assertEqual(recorded,plain);self.assertEqual(recorded_trace,trace)

    def test_literal_construction_and_all_native_contracts_without_packing_or_gpu(self):
        from calculator import timeline
        def forbidden(*a,**kw):raise AssertionError('Native/GPU work forbidden in literal construction')
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_runtime,'compile_program',forbidden),patch.object(portable_backend,'execute',forbidden):cases=fixtures()
        self.assertEqual(len(cases),26);before=copy.deepcopy(cases)
        with forbid_execution(),patch.object(portable_runtime,'compile_program',forbidden),patch.object(detail_gpu,'compile_effects',forbidden),patch.object(detail_gpu,'compile_full',forbidden):
            for c in cases:
                with self.subTest(c['name']):
                    native,_=observe(c);self.assertTrue(verify(c,native)['verified'])
        self.assertEqual(cases,before)





if __name__=='__main__':unittest.main()
