"""Native live-list order, snapshot ownership and exact private source boundary."""
import copy,importlib.util,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_full_burst_queue_cases import fixtures
from portable_full_burst_queue_contracts import verify
from world_full_burst_queue_native import observe,plain
class FullBurstQueueTests(unittest.TestCase):
    def test_literal_live_queue_and_owned_tail_contracts(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('Factory must be static')):cases=fixtures()
        self.assertEqual(len(cases),7);before=copy.deepcopy(cases)
        for c in cases:verify(c,observe(c)[0])
        self.assertEqual(cases,before)
    def test_observation_preserves_semantic_queries_and_rng(self):
        for c in fixtures():
            def measured(fn):
                old=sys.getprofile()
                counts=[0]*4;get=BuffManager.get_buffs;ref=BuffManager.ref_count;notify=BuffManager.notify;sample=random.sample
                def counted_get(*args,**kw):counts[0]+=1;return get(*args,**kw)
                def counted_ref(*args,**kw):counts[1]+=1;return ref(*args,**kw)
                def counted_notify(self,event,t,caster,**kw):counts[2]+=1;return notify(self,event,t,caster,**kw)
                def counted_sample(*args,**kw):counts[3]+=1;return sample(*args,**kw)
                with patch.object(BuffManager,'get_buffs',counted_get),patch.object(BuffManager,'ref_count',counted_ref),patch.object(BuffManager,'notify',counted_notify),patch.object(random,'sample',counted_sample):
                    value=fn(c);state=random.getstate()
                self.assertIs(sys.getprofile(),old);return value,counts,state
            (n,t),calls,state=measured(observe);n.pop('full_burst_queue')
            self.assertEqual(((n,t),calls,state),measured(plain),c['name'])
    def test_wrong_live_order_tail_and_snapshot_rejected(self):
        for c in fixtures():
            n,_=observe(c);b=copy.deepcopy(n)
            b['full_burst_queue']['packets'][-1]['amount']+=1
            with self.assertRaises(AssertionError):verify(c,b)
            b=copy.deepcopy(n);b['pending_burst']['count']+=1
            with self.assertRaises(AssertionError):verify(c,b)
            if c['contract']['kind'].startswith(('parts-','interrupt-')):
                b=copy.deepcopy(n);next(x for x in b['parts_skill_events'] if x['kind']=='packet')['part_damage']=0
                with self.assertRaises(AssertionError):verify(c,b)
    def test_exact_source_projection_rejects_queue_and_sidecar_changes(self):
        from portable_full_burst_landing_source_contract import project_sources
        project_sources(ROOT)
        for name,old,new in [('gpu/full_burst_landing_runtime.slang','index<s.pendingCount','index<1'),('gpu/full_burst_landing_runtime.slang','i<38','i<0'),('gpu/pending_burst_runtime.slang','releasePendingBatch(s,count)','releasePendingBatch(s,0)')]:
            text=(ROOT/name).read_text();self.assertIn(old,text)
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:text.replace(old,new)})
    def test_wire_defaults_preserve_native_and_full_fixture_count(self):
        s=importlib.util.spec_from_file_location('queue_test',ROOT/'research/verify-world-full-burst-queue-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        rows,_=m.prepare();self.assertEqual(len(rows),7)
        for original,(_,_,domain) in zip(fixtures(),rows):self.assertEqual(observe(original),observe(domain[0]))
if __name__=='__main__':unittest.main()
