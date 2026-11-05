"""Admission and exact shared-source deltas for private interrupt landings."""
import array,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_interrupt_aim_trace import BASE,COUNT,MAGIC,gpu_records
from portable_scratch_layout import verify
from portable_specs import LIMITS


class InterruptAimGpuTests(unittest.TestCase):
    def test_all_native_contracts_pack_without_canonical_kind_aliases(self):
        spec=importlib.util.spec_from_file_location('interrupt_pack_test',ROOT/'research/verify-world-interrupt-aim-short.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        entries,_=m.prepare();self.assertEqual(len(entries),24)
        for name,words,domain in entries:
            self.assertIsNotNone(domain)
            self.assertTrue(all(int(b.kind) in (0,1,5,6) for b in domain[2]))


    def test_diagnostic_bank_and_reserved_fields_fail_closed(self):
        report=verify(LIMITS,mode='interrupt-aim-diagnostic');self.assertTrue(report['verified'])
        words=array.array('I',[0])*LIMITS['WORLD_RELOAD_OUTPUT_WORDS'];words[BASE]=MAGIC
        self.assertEqual(gpu_records(words,list('abcde')),[])
        for at,value in ((BASE+1,COUNT+1),(BASE+2,1),(BASE+16,1),(BASE+16+COUNT*32-1,1)):
            changed=array.array('I',words);changed[at]=value
            with self.subTest(at=at),self.assertRaises(AssertionError):gpu_records(changed,list('abcde'))


if __name__=='__main__':unittest.main()
