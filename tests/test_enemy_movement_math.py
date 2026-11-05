"""Small motion ABI and arithmetic failures remain distinct from battle support."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('movement_math_suite',ROOT/'research/verify-enemy-movement-math.py');suite=importlib.util.module_from_spec(s);s.loader.exec_module(suite)

class MovementMathTests(unittest.TestCase):
    def test_all_status_precedence_signed_zero_and_overflow_cases_use_full_words(self):
        rows,raw=suite.prepare();self.assertEqual(len(rows),43);self.assertEqual(sum(d is not None for _,_,d in rows),34)
        self.assertEqual(len(raw),4+43*24*4)
        failures=0
        for name,words,domain in rows:
            self.assertEqual(len(words),24)
            if domain is None:continue
            n=suite.native_reference(domain);self.assertFalse(n['gpu_world_consumer'])
            failures+=n['status']==16
            expected=[16]+[0]*15 if n['status']==16 else [0,suite.MAGIC,domain[0],domain[1],*n['position_words'],*([0]*8)]
            self.assertEqual(suite.compare(expected,domain),n)
            expected[-1]=1
            with self.assertRaises(AssertionError):suite.compare(expected,domain)
        self.assertEqual(failures,2)

if __name__=='__main__':unittest.main()
