"""Explicit Python-event observation contract, restoration and rejected consumers."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
from native_python_profile import python_observers_only,observer_chain
class NativePythonProfileTests(unittest.TestCase):
    def test_python_event_order_and_original_profiler_restored(self):
        events=[]
        def watched():return len([1,2])
        def observer(frame,event,answer):
            if frame.f_code is watched.__code__ and event in ('call','return'):events.append(event)
        previous=sys.getprofile();sys.setprofile(observer)
        try:
            watched();expected=events.copy();events.clear()
            with python_observers_only(True) as counts:watched()
            self.assertIs(sys.getprofile(),observer);self.assertEqual(events,expected);self.assertEqual(events,['call','return']);self.assertGreater(counts['c_call'],0)
        finally:sys.setprofile(previous)
    def test_explicit_c_event_consumer_rejected_before_replacing_profiler(self):
        def consumer(frame,event,answer):
            if event=='c_call':pass
        previous=sys.getprofile();sys.setprofile(consumer)
        try:
            with self.assertRaises(ValueError):
                with python_observers_only(True):pass
            self.assertIs(sys.getprofile(),consumer)
        finally:sys.setprofile(previous)
    def test_exception_and_disabled_paths_preserve_profiler(self):
        def observer(frame,event,answer):return None
        previous=sys.getprofile();sys.setprofile(observer)
        try:
            with self.assertRaises(RuntimeError):
                with python_observers_only(True):raise RuntimeError('failed native')
            self.assertIs(sys.getprofile(),observer)
            with python_observers_only(False):self.assertIs(sys.getprofile(),observer)
        finally:sys.setprofile(previous)
    def test_unknown_callback_objects_rejected(self):
        with self.assertRaises(ValueError):observer_chain(object())
if __name__=='__main__':unittest.main()
