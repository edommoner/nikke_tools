import array,importlib.util,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'research')]
from portable_coordinate_math_cases import exact_bits,compatible_bits,native_bits,vectors,INF,NAN
class CoordinateMathTests(unittest.TestCase):
    def test_exact_oracle_matches_native_full_range(self):
        for a,b in vectors():self.assertEqual(compatible_bits(a,b),native_bits(a,b),(hex(a),hex(b)))
        rng=random.Random(0x4e494b4b45)
        for _ in range(20000):
            a,b=rng.getrandbits(64),rng.getrandbits(64);self.assertEqual(compatible_bits(a,b),native_bits(a,b),(hex(a),hex(b)))
        for _ in range(10000):
            exponent=rng.randrange(2047);gap=rng.randrange(29)
            a=(exponent<<52)|rng.getrandbits(52);b=(max(0,exponent-gap)<<52)|rng.getrandbits(52)
            self.assertEqual(compatible_bits(a,b),native_bits(a,b),(hex(a),hex(b)))
    def test_subnormal_native_double_rounding_is_preserved(self):
        a,b=0xc000000000000,0x7000000000000
        self.assertEqual(exact_bits(a,b),0xde477359432dd)
        self.assertEqual(compatible_bits(a,b),0xde477359432dc)
        self.assertEqual(compatible_bits(a,b),native_bits(a,b))
    def test_specials_and_exact_subnormal_triples(self):
        self.assertEqual(exact_bits(INF,NAN),INF);self.assertEqual(exact_bits(1<<63,0),0)
        for n in [1,2,3,100,(1<<49)-1]:self.assertEqual(exact_bits(3*n,4*n),5*n)
        self.assertEqual(exact_bits(0x7fefffffffffffff,0x7fefffffffffffff),INF)
    def test_static_pack_and_whole_buffer_comparator(self):
        s=importlib.util.spec_from_file_location('coordinate_math_test_adapter',ROOT/'research/verify-coordinate-math-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
        with patch.object(a,'native_reference',side_effect=AssertionError('Packing must not evaluate distances')):entries,raw=a.prepare()
        self.assertEqual(len(entries),1026);self.assertEqual(len(raw),4+1026*8*4)
        row=entries[100];v=a.native_reference(row[2])['bits'];good=array.array('I',[0,0x43484e31,v&0xffffffff,v>>32,0,0,0,0]);a.compare(good,row[2]);good[-1]=1
        with self.assertRaises(AssertionError):a.compare(good,row[2])
if __name__=='__main__':unittest.main()
