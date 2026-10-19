"""Native reference-index correctness without discarding its cached lookup."""
import sys,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker
from calculator.buff_manager import BuffManager

class ReferenceCacheTests(unittest.TestCase):
    def manager(self):
        manager=BuffManager.__new__(BuffManager)
        manager._active=[];manager._cache_version=0;manager._name_index_cache={};manager.state={};manager._cur_t=2
        return manager
    def carrier(self,stack):return SimpleNamespace(effect={'name':'state'},caster='owner',stack=stack)
    def test_registration_append_invalidates_prior_absent_lookup(self):
        m=self.manager();self.assertIsNone(m.ref_count('owner','state'));m._active.append(self.carrier(2));self.assertEqual(m.ref_count('owner','state'),2)
    def test_value_refresh_reuses_the_cached_object_list(self):
        m=self.manager();ab=self.carrier(2);m._active.append(ab);self.assertEqual(m.ref_count('owner','state'),2);cached=m._name_index_cache['state'];ab.stack=3
        self.assertEqual(m.ref_count('owner','state'),3);self.assertIs(m._name_index_cache['state'],cached)
    def test_replacement_and_structural_version_rebuild(self):
        m=self.manager();m._active.append(self.carrier(2));m.ref_count('owner','state');m._active=[self.carrier(4)];self.assertEqual(m.ref_count('owner','state'),4)
        m._active[0]=self.carrier(7);m._cache_version+=1;self.assertEqual(m.ref_count('owner','state'),7)
    def test_gauge_and_owned_source_precedence_remain_native(self):
        m=self.manager();m._active.append(self.carrier(8));m.state={'gauges':{'owner':{'state':0}}};self.assertEqual(m.ref_count('owner','state'),0)
        m.state={}
        from effect_runtime import pool
        pool(m,'periodic_sources')[('owner','state')]=SimpleNamespace(count=lambda t:1)
        self.assertEqual(m.ref_count('owner','state'),1)
if __name__=='__main__':unittest.main()
