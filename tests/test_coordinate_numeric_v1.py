"""Common policy has independent accuracy and strict whole-word comparisons."""
import importlib.util,math,sys,unittest
from decimal import Decimal,localcontext
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import portable_coordinate_numeric_v1 as n
from coordinate_numeric_accuracy import audit,common
from coordinate_decimal_oracle import reference,pi
s=importlib.util.spec_from_file_location('numeric_adapter',ROOT/'research/verify-coordinate-numeric-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class NumericTests(unittest.TestCase):
    def test_recipe_and_generated_source_identity(self):
        n.check_schema(ROOT)
        with self.assertRaises(TypeError):n.polynomial('sin')[0]['x']=1
        with localcontext() as ctx:
            ctx.prec=185;self.assertLess(abs(n.high_precision_pi()-pi()),Decimal('1e-180'))
    def test_no_host_transcendentals(self):
        from contextlib import ExitStack
        with ExitStack() as stack:
            for name in ('sin','cos','atan','atan2','acos','sqrt'):stack.enter_context(patch.object(math,name,side_effect=AssertionError(name)))
            for op in range(1,6):common(op,n.bits(.3),n.bits(.7))
    def test_independent_boundary_accuracy(self):
        report=audit(ROOT,32)
        self.assertTrue(report['accuracy_verified']);self.assertEqual(report['operations']['sqrt']['max_ulp'],0)
    def test_signed_axes_and_large_exact_degree_periodicity(self):
        self.assertEqual(n.sincos_degrees(n.bits(-180.)),(n.SIGN,n.bits(-1.)))
        self.assertEqual(n.sincos_degrees(n.bits(270.)),(n.bits(-1.),0))
        self.assertEqual(n.sqrt_bits(n.SIGN),n.SIGN)
        self.assertEqual(n.atan2_bits(n.SIGN,n.SIGN),n.PI|n.SIGN)
        for value in [0x7fefffffffffffff,0xffefffffffffffff,1,n.SIGN|1]:
            sine,cosine=n.sincos_degrees(n.positive_remainder(value))
            self.assertEqual(n.sincos_degrees(value),(sine^(value&n.SIGN),cosine))
    def test_packing_no_numeric_reference_and_typed_reference(self):
        with patch.object(a,'native_reference',side_effect=AssertionError('packing evaluated outputs')):rows,raw=a.prepare()
        self.assertEqual(len(rows),2783);self.assertEqual(len(raw),4+2783*12*4)
        self.assertEqual(sum(d is None for _,_,d in rows),12)
        self.assertEqual(a.native_reference((1,0,0))['reference_kind'],'deterministic-common-cpu')
    def test_whole_output_and_rejection_mutations(self):
        domain=(1,n.bits(45.),0);x,y=common(*domain);words=[0,n.MAGIC,1,1,*a.words64(x),*a.words64(y),*([0]*8)]
        a.compare(words,domain)
        for at in [0,1,3,4,5,6,7,15]:
            changed=list(words);changed[at]^=1
            with self.subTest(at=at),self.assertRaises(AssertionError):a.compare(changed,domain)
        a.validate_rejection([64]+[0]*15,'reject/coordinate-common-v1/test')
        with self.assertRaises(AssertionError):a.validate_rejection([64]+[0]*14+[1],'reject/coordinate-common-v1/test')
    def test_domains_explicitly_reject_nonfinite_and_unbounded_radians(self):
        for fn,value in [(n.sincos_degrees,0x7ff0000000000000),(n.sincos_radians,n.TAU+1),(n.acos_bits,n.ONE+1),(n.sqrt_bits,n.SIGN|1)]:
            with self.subTest(fn=fn),self.assertRaises(ValueError):fn(value)
    def test_accuracy_sample_bound(self):
        for samples in [-1,10001,True]:
            with self.assertRaises(ValueError):audit(ROOT,samples)
    def test_cli_audit_writes_once_without_gpu_or_native_battle(self):
        import contextlib,io,json,tempfile
        s=importlib.util.spec_from_file_location('numeric_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'accuracy.json'
            with contextlib.redirect_stdout(io.StringIO()),patch.object(cli,'native_hash',side_effect=AssertionError('No native battle')):
                cli.main(['numeric-audit','--samples','0','--out',str(out)])
            self.assertTrue(json.loads(out.read_text())['accuracy_verified'])
            with self.assertRaises(ValueError):cli.main(['numeric-audit','--samples','0','--out',str(out)])
if __name__=='__main__':unittest.main()
