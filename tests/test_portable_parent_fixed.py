"""Actual parent context, shared input tags and source containment contracts."""
import array,copy,importlib.util,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_parent_fixed_cases import fixtures
from world_parent_fixed_native import observe,plain
from portable_parent_fixed_contracts import verify
class ParentFixedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=fixtures();cls.native=[observe(c) for c in cls.cases]
    def test_authored_clock_matches_static_native_weapon_normalization(self):
        from world_frame_native import authored_metadata,roster_names
        from portable_charge_clock_specs import normalize_static_clock
        for c in self.cases:
            names=roster_names(c);chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10}) for n in names]
            with patch.object(timeline,'simulate',side_effect=AssertionError('Static normalization only')),patch.dict(timeline._NIKKE,authored_metadata(c)),patch.dict(timeline._DELAYS['_exceptions'],{},clear=True),patch.dict(timeline._DELAYS['_defaults_by_weapon_type'],{'AR':{'post_reload_delay':0}},clear=True):
                self.assertEqual(normalize_static_clock(chars,c['base_atk'],c['enemy']),c['post_fire_delays'])
    def test_literal_notification_amounts_timing_integer_zero_and_budget(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('Static fixture')):self.assertEqual(fixtures(),self.cases)
        for c,(n,t) in zip(self.cases,self.native):verify(c,n)
    def test_observer_preserves_full_battle_trace_and_rng(self):
        for c,(n,t) in zip(self.cases,self.native):
            b=copy.deepcopy(n);b.pop('parent_fixed');self.assertEqual((b,t),plain(c))
    def test_observer_does_not_query_or_notify_more(self):
        c=next(c for c in self.cases if c['contract']['kind']=='nested-context-empty')
        def measure(fn):
            counts=[0]*4;get=BuffManager.get_buffs;ref=BuffManager.notify_ctx;notify=BuffManager.notify;sample=random.sample
            def counted_get(*a,**kw):counts[0]+=1;return get(*a,**kw)
            def counted_ref(*a,**kw):counts[1]+=1;return ref(*a,**kw)
            def counted_notify(self,event,t,caster,**kw):counts[2]+=1;return notify(self,event,t,caster,**kw)
            def counted_sample(*a,**kw):counts[3]+=1;return sample(*a,**kw)
            old=sys.getprofile()
            with patch.object(BuffManager,'get_buffs',counted_get),patch.object(BuffManager,'notify_ctx',counted_ref),patch.object(BuffManager,'notify',counted_notify),patch.object(random,'sample',counted_sample):fn(c);state=random.getstate()
            self.assertIs(sys.getprofile(),old);return counts,state
        self.assertEqual(measure(observe),measure(plain))
    def test_faulty_parent_context_rounding_and_packet_rejected(self):
        for c,(n,t) in zip(self.cases,self.native):
            if n['parent_fixed']['reads']:
                b=copy.deepcopy(n);b['parent_fixed']['reads'][0]['value']+=1
                with self.assertRaises(AssertionError):verify(c,b)
            if t:
                b=copy.deepcopy(n);b['parent_fixed']['packets'][0]['amount']+=1
                with self.assertRaises(AssertionError):verify(c,b)
    def test_static_parent_tag_and_private_world_requirement(self):
        from portable_parent_fixed_specs import validate
        for c in self.cases:
            e=next(e for e in c['effects'] if e.get('name')=='fixed-parent');self.assertTrue(validate(e,combat={},world_frame=True))
            with self.assertRaises(ValueError):validate(e,combat={},world_frame=False)
            with self.assertRaises(ValueError):validate(e,combat=None,world_frame=True)
        s=importlib.util.spec_from_file_location('parent_tag_test',ROOT/'research/verify-world-parent-fixed-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);rows,_=m.prepare();self.assertEqual((len(rows),sum(d is not None for n,w,d in rows)),(30,23))
if __name__=='__main__':unittest.main()
