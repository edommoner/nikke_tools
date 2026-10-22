"""Observe only: fixed disjoint bank, bounded decoder and exact source delta."""
import array,importlib.util,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_specs import LIMITS as L
from portable_query_diagnostic import decode,compare_misses,LOWER,UPPER,decode_census,compare_census
from portable_query_diagnostic_source_contract import ledger,project_sources


class QueryDiagnosticTests(unittest.TestCase):
    def fixture(self):
        b=array.array('I',[0])*786432;head=L['NATIVE_DIAG_BASE'];b[head:head+4]=array.array('I',[0x4e514431,1,1,0])
        for at,value in ((head+4,LOWER),(head+6,UPPER),(head+16+6,13.33),(head+16+8,40.),(head+16+10,20.)):
            b[at:at+2]=array.array('I',struct.unpack('<II',struct.pack('<d',value)))
        b[head+8:head+10]=array.array('I',[16,256]);b[head+16:head+22]=array.array('I',[2,1,0,0,3,5]);return b

    def test_decoder_retains_query_values_and_rejects_faults(self):
        b=self.fixture();a=decode(b);expected=[dict(owner=1,target=0,exclusion=0,time=13.33,atk_flat=40.,atk_pct=20.,after_index=0,sample_total=0)]
        compare_misses(a,expected)
        for word in (0,1,2,3,4,8,10,16,17,22,24,28):
            changed=array.array('I',b);changed[L['NATIVE_DIAG_BASE']+word]^=1
            with self.subTest(word=word),self.assertRaises(AssertionError):compare_misses(decode(changed),expected)

    def test_fixed_bank_is_disjoint_and_latest_source_changes_are_exact(self):
        self.assertEqual(L['NATIVE_DIAG_BASE'],L['ORDERED_HISTORY_BASE']+L['ORDERED_HISTORY_WORDS'])
        self.assertLessEqual(L['NATIVE_DIAG_BASE']+L['NATIVE_DIAG_WORDS'],786416)
        project_sources(ROOT)
        for name,row in ledger(ROOT)['sources'].items():
            text=(ROOT/name).read_text()
            for c in row['changes']:
                with self.subTest(name=name),self.assertRaises(AssertionError):project_sources(ROOT,{name:text.replace(c['current'],c['baseline'],1)})

    def test_census_bounds_counters_endpoints_and_tail(self):
        b=array.array('I',[0])*786432;h=L['NATIVE_DIAG_BASE']
        b[h:h+4]=array.array('I',[0x4e514331,2,2,0]);b[h+8:h+10]=array.array('I',[2,2048])
        for at,v in ((h+4,0.),(h+6,1.)):
            b[at:at+2]=array.array('I',struct.unpack('<II',struct.pack('<d',v)))
        b[h+16:h+20]=array.array('I',[1,624,3,4])
        expected=[dict(time=0.,sample_total=1,after_index=624),dict(time=1.,sample_total=3,after_index=4)]
        compare_census(decode_census(b),expected)
        for word in (0,1,2,3,4,8,10,16,17,18,19,20):
            changed=array.array('I',b);changed[h+word]^=1
            with self.subTest(word=word),self.assertRaises(AssertionError):compare_census(decode_census(changed),expected)

    def test_factory_keeps_the_original_full_lily30_input(self):
        s=importlib.util.spec_from_file_location('diag_test',ROOT/'research/verify-world-native-query-diagnostic-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        def forbidden(*a,**kw):raise AssertionError('Packing cannot execute battle/GPU')
        import portable_backend
        from calculator import timeline
        with patch.object(timeline,'simulate',forbidden),patch.object(portable_backend,'execute',forbidden):rows,data=m.prepare()
        original=next(e for e in m.base.prepare()[0] if e[0]=='state-focus-real/릴리/30s')
        self.assertEqual(len(rows),1);self.assertEqual(rows[0][1],original[1]);self.assertEqual(rows[0][2][0]['body'],original[2][0]['body'])


if __name__=='__main__':unittest.main()
