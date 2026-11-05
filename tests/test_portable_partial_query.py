"""Read-only CPU consumers must retain battle, trace and all semantic reads."""
import array,copy,importlib.util,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker,portable_backend
from portable_partial_query_cases import fixtures
from portable_partial_query_contracts import verify
from world_partial_query_native import observe
from world_nonfull_charge_native import observe as plain


class PartialQueryTests(unittest.TestCase):
    def test_all17_native_contracts_preserve_original_battle_and_trace(self):
        cases=fixtures();before=copy.deepcopy(cases);self.assertEqual(len(cases),17)
        with patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')):
            for c in cases:
                with self.subTest(case=c['name']):
                    n,t=observe(c);verify(c,n,t);data=n.pop('partial_query');p,pt=plain(c)
                    self.assertEqual(n,p);self.assertEqual(t,pt)
                    if c['controls'][0].get('click') and 'callback' not in c['name'] and c['name'] not in ('partial-query-periodic-full','partial-query-spontaneous-full'):
                        reads=[r for r in data['reads'] if r['owner']==0]
                        partial=[r for r in n['nonfull_charge'] if r['kind']=='shot' and r['owner']==0 and not r['full']]
                        self.assertEqual(len(reads),len(partial))
                        self.assertEqual([r['time'] for r in reads],[r['time'] for r in partial])
        self.assertEqual(cases,before)

    def test_contract_rejects_reader_rng_notice_and_trace_faults(self):
        c=fixtures()[0];n,t=observe(c)
        for key in ('reads','queries','samples'):
            bad=copy.deepcopy(n);bad['partial_query'][key].pop()
            with self.subTest(key=key),self.assertRaises(AssertionError):verify(c,bad,t)
        bad=copy.deepcopy(n);bad['nonfull_charge'][0]['full']=False
        with self.assertRaises(AssertionError):verify(c,bad,t)
        with self.assertRaises(AssertionError):verify(c,n,t+['fault-injected-trace'])

    def test_static_inputs_cover_every_contract_without_running_gpu(self):
        s=importlib.util.spec_from_file_location('partial_query_suite',ROOT/'research/verify-world-partial-query-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        with patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')):rows,data=m.prepare()
        self.assertEqual(len(rows),17);self.assertEqual(len({name for name,_,_ in rows}),17)
        self.assertEqual(len(data),4+17*104400*4)

    def test_diagnostic_retains_the_original_inputs_and_domains(self):
        s=importlib.util.spec_from_file_location('partial_query_diag_suite',ROOT/'research/verify-world-partial-query-diagnostic-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        with patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')):
            rows,data=m.prepare();original={r[0]:r for r in m.base.prepare()[0]}
        self.assertEqual(len(rows),2);self.assertEqual((m.LOWER,m.UPPER),(.2,.8))
        for name,words,domain in rows:self.assertEqual((name,words,domain),original[name])

    def test_custom_query_window_rejects_wrong_bounds_and_omissions(self):
        from portable_specs import LIMITS as L
        from portable_query_diagnostic import decode,compare_misses
        b=array.array('I',[0])*786432;head=L['NATIVE_DIAG_BASE'];b[head:head+4]=array.array('I',[0x4e514431,1,1,0]);b[head+8:head+10]=array.array('I',[16,256])
        for at,value in ((head+4,.2),(head+6,.8),(head+22,.5333333333333333)):
            b[at:at+2]=array.array('I',struct.unpack('<II',struct.pack('<d',value)))
        b[head+16]=2
        expected=[dict(owner=0,target=0,exclusion=0,time=.5333333333333333,atk_flat=0.,atk_pct=0.,after_index=0,sample_total=0)]
        compare_misses(decode(b,lower=.2,upper=.8),expected)
        with self.assertRaises(AssertionError):decode(b)
        with self.assertRaises(AssertionError):decode(b,lower=.3,upper=.8)
        b[head+3]=1
        with self.assertRaises(AssertionError):compare_misses(decode(b,lower=.2,upper=.8),expected)


if __name__=='__main__':unittest.main()
