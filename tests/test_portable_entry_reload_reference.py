"""Native entry-reload query order before shared GPU lowering.

Uses the existing standalone CharState observer. Full-world contracts and GPU
admission are deliberately separate coverage; this test certifies neither.
"""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
import portable_backend
import portable_runtime
from calculator import timeline
from mode_entry_native import observe

spec=importlib.util.spec_from_file_location('entry_reload_literal_cases',ROOT/'research/build-mode-entry-cases.py')
factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)


class EntryReloadNativeTests(unittest.TestCase):
    def test_base_reload_query_repeats_after_latching_and_explicit_delay_bypasses_it(self):
        original=timeline.CharState._reload_duration
        def forbidden(*args,**kwargs):raise AssertionError('Packing/GPU forbidden in native contract')
        with patch.object(portable_backend,'build',forbidden),patch.object(portable_backend,'execute',forbidden),patch.object(portable_runtime,'compile_program',forbidden):
            for owner in (0,4):
                for mode in ('auto','charge'):
                    for delay in (None,0,.1):
                        with self.subTest(owner=owner,mode=mode,delay=delay):
                            case=factory.make(owner,'auto',mode,0,'initial')
                            case['mode_entry_context']['delays']={} if delay is None else {'Mode A':delay}
                            case['effects'][2].update(entry_reload=True,reload_time=.9)
                            case['script']=[row for row in case['script'] if row[0]<=.2]
                            before=copy.deepcopy(case);calls=[]
                            def duration(actor,bm,time):
                                state=(time,actor.weapon['reload_time'],actor._wc_entry_reload_until)
                                value=original(actor,bm,time);calls.append((*state,value));return value
                            with patch.object(timeline.CharState,'_reload_duration',duration):native=observe(case)
                            self.assertEqual(case,before)
                            if delay is None:
                                self.assertEqual(len(calls),13)
                                self.assertEqual([c[0] for c in calls],[frame/60 for frame in range(13)])
                                self.assertTrue(all(c[1]==.5 and c[3]==.5 for c in calls))
                                self.assertEqual(calls[0][2],-1)
                                self.assertTrue(all(c[2]==.5 for c in calls[1:]))
                                self.assertEqual(native['mode_entry_wait_until'][owner],.5)
                                self.assertEqual(native['queries'][-1]['combat']['weapons'][owner]['shots'],0)
                            else:self.assertEqual(calls,[])


if __name__=='__main__':unittest.main()
