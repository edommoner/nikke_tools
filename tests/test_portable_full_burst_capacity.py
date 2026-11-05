"""Native finite512/513, end-list ownership and exact private codec contract."""
import copy,importlib.util,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_full_burst_capacity_cases import fixtures
from portable_full_burst_capacity_contracts import verify
from world_full_burst_capacity_native import observe,plain
class FullBurstCapacityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=fixtures();cls.native=[observe(c) for c in cls.cases]
    def test_finite_literal_boundary_and_next_collection_contracts(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('Factory must be static')):self.assertEqual(fixtures(),self.cases)
        for c,(n,t) in zip(self.cases,self.native):verify(c,n,t)
        self.assertEqual([len(t) for n,t in self.native],[3,3,514,514,515])
    def test_final_observer_preserves_all_native_fields_and_rng(self):
        for c,(n,t) in zip(self.cases,self.native):
            original=sys.getprofile();bare,trace=plain(c);self.assertIs(sys.getprofile(),original)
            b=copy.deepcopy(n);b.pop('full_burst_capacity');self.assertEqual((b,t),(bare,trace))
    def test_observer_does_not_query_or_notify(self):
        c=self.cases[1]
        def measure(fn):
            calls=[0]*4;get=BuffManager.get_buffs;ref=BuffManager.ref_count;notify=BuffManager.notify;sample=random.sample
            def counted_get(*a,**kw):calls[0]+=1;return get(*a,**kw)
            def counted_ref(*a,**kw):calls[1]+=1;return ref(*a,**kw)
            def counted_notify(self,event,t,caster,**kw):calls[2]+=1;return notify(self,event,t,caster,**kw)
            def counted_sample(*a,**kw):calls[3]+=1;return sample(*a,**kw)
            with patch.object(BuffManager,'get_buffs',counted_get),patch.object(BuffManager,'ref_count',counted_ref),patch.object(BuffManager,'notify',counted_notify),patch.object(random,'sample',counted_sample):fn(c);state=random.getstate()
            return calls,state
        self.assertEqual(measure(observe),measure(plain))
    def test_final_queue_and_numeric_faults_rejected(self):
        for c,(n,t) in zip(self.cases,self.native):
            if c['contract']['late']:
                bad=copy.deepcopy(n);bad['full_burst_capacity']['entries']=[]
                with self.assertRaises(AssertionError):verify(c,bad,t)
            bad=copy.deepcopy(t);bad[-1]['amount']+=1
            with self.assertRaises(AssertionError):verify(c,n,bad)
    def test_wire_summary_is_only_history_not_workload_reduction(self):
        s=importlib.util.spec_from_file_location('capacity_test',ROOT/'research/verify-world-full-burst-capacity-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);rows,_=m.prepare()
        self.assertEqual((len(rows),sum(d is not None for n,w,d in rows)),(5,4))
        for c,(_,_,d) in zip(self.cases,rows):
            if not c['contract']['reject']:
                self.assertEqual(observe(c),observe(d[0]));self.assertEqual(d[0]['contract'],c['contract'])
    def test_private_source_delta_rejects_missing_codec_or_staging(self):
        from portable_full_burst_landing_source_contract import project_sources
        project_sources(ROOT);name='gpu/pending_burst_runtime.slang';s=(ROOT/name).read_text()
        for old,new in [('s.pendingCount-logicalCount','0'),('releasePendingBatch(s,count)','releasePendingBatch(s,0)')]:
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:s.replace(old,new)})
if __name__=='__main__':unittest.main()
