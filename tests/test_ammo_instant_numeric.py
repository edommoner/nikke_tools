"""Original percentage/flat arithmetic and the extracted shared consumers."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('ammo_numeric_test_adapter',ROOT/'research/verify-ammo-instant-numeric.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class AmmoInstantNumericTests(unittest.TestCase):
    def test_native_rounding_ties_and_flat_negative_state_are_distinct(self):
        for kind,cap,current,value,expected in [(13,10,3,5.,3),(13,10,3,15.,5),(13,10,3,25.,5),(13,10,3,-15.,1),(13,16,16,-2.95,16),(13,16,16,-5.,15),(14,10,0,-1.75,-1),(13,10,-3,0.,0),(14,10,-3,0.,-3)]:
            c=dict(kind=kind,capacity=cap,current=current,value=value)
            self.assertEqual(m.native_reference((c,)),dict(status=0,result=expected))

    def test_native_integer_domain_and_nonfinite_products_fail_closed(self):
        for kind,value in [(14,-1e30),(13,1e308),(13,-1e308)]:
            c=dict(kind=kind,capacity=2147483647,current=0,value=value)
            self.assertEqual(m.native_reference((c,)),dict(status=16,result=None))
        c=dict(kind=14,capacity=2147483647,current=-2147483648,value=1e30)
        self.assertEqual(m.native_reference((c,)),dict(status=0,result=2147483647))

    def test_all_literal_vectors_use_original_handlers_without_a_battle(self):
        from calculator import timeline
        before=copy.deepcopy(m.fixtures())
        with patch.object(timeline,'simulate',side_effect=AssertionError('Numeric oracle is not a battle')):
            rows,data=m.prepare()
            for _,_,d in rows:
                if d is not None:self.assertIn(m.native_reference(d)['status'],(0,16))
        self.assertEqual(m.fixtures(),before)
        self.assertEqual((len(rows),sum(d is not None for _,_,d in rows)),(713,705))
        self.assertEqual(len(data),4+713*16*4)

    def test_allied_consumer_calls_the_common_numeric_operator(self):
        source=(ROOT/'gpu/ammo_instant_runtime.slang').read_text()
        self.assertIn('#include "ammo_instant_numeric.slang"',source)
        self.assertIn('prepareAmmoInstant(d.kind,d.value,flat,fraction)',source)
        self.assertIn('ammoInstantResult(d.kind,capacity,s.ammo[who],flat,fraction,result)',source)
        self.assertNotIn('f64ToI64',source)

    def test_comparer_rejects_a_corrupt_numeric_result(self):
        c=dict(name='corrupt',kind=13,capacity=10,current=3,value=15.)
        with self.assertRaises(AssertionError):m.compare([0,0x414e5531,4,0,0,0,0,0],(c,))


if __name__=='__main__':unittest.main()
