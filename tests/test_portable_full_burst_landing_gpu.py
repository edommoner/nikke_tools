"""Wire modes, signed/count names, shared shape and retained proof boundaries."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_specs import LIMITS as L
from world_full_burst_landing_native import observe
from portable_full_burst_landing_cases import fixtures

def load(name):
    s=importlib.util.spec_from_file_location('test_full_burst_'+name,ROOT/'research'/('verify-world-'+name+'-short.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class FullBurstLandingGpuTests(unittest.TestCase):
    def test_default_wire_controls_preserve_all_native_fields(self):
        m=load('full-burst-landing')
        for c in fixtures():self.assertEqual(observe(c),observe(m.wire_case(c)))
    def test_static_modes_names_and_signed_count_payloads(self):
        rows,_=load('full-burst-landing').prepare();self.assertEqual((len(rows),sum(d is not None for _,_,d in rows)),(26,13))
        for _,w,domain in rows[:13]:
            c,meta,_=domain;row=next(i for i,e in enumerate(c['effects']) if e.get('name')=='landing');at=L['DAMAGE_DEFINITION_BASE']+row*8
            self.assertEqual(w[at+6],2 if c['contract']['delayed'] else 0)
            if c['contract']['delayed']:
                self.assertEqual(w[L['MODE_BASE']+row*L['MODE_WORDS']+17:L['MODE_BASE']+row*L['MODE_WORDS']+20],[0x46424c31,0,0])
                expected=4096+meta['states']['cast-count'] if c['contract']['reference'] else 4096+meta['states']['missing'] if c['contract']['missing'] else c['contract']['latched_count']&0xffffffff
                self.assertEqual(w[at+7],expected)
        self.assertTrue(all(d is None for _,_,d in rows[13:]))
    def test_all_old230_wire_bytes_retained(self):
        _,old=load('named-enemy-removal-retention').prepare();rows,new=load('full-burst-landing-retention').prepare();self.assertEqual((len(rows),sum(d is not None for _,_,d in rows)),(258,186));self.assertEqual(new[4:len(old)],old[4:])
    def test_declared_single_body_counter_selectors_have_no_other_world_alias(self):
        import copy
        from types import SimpleNamespace
        from portable_target_counter_specs import single_body_selector,pack_single_body_selectors
        rows,_=load('full-burst-landing-rosters').prepare()
        for _,words,(case,meta,prepared,_) in rows:
            self.assertEqual(len(prepared['effects']),76)
            row=next(i for i,r in enumerate(prepared['effects']) if 'target_counter' in r['effect']);e=prepared['effects'][row]['effect'];before=copy.deepcopy(e)
            self.assertEqual(e['target'],'enemies_random:1');self.assertEqual(words[L['DAMAGE_DEFINITION_BASE']+row*8:L['DAMAGE_DEFINITION_BASE']+row*8+2],[1,1])
            for target in ('enemies_random:1','enemies_nearest:1','all_enemies','boss'):
                x=dict(e,target=target);self.assertTrue(single_body_selector(x,[SimpleNamespace(kind=0)]))
                self.assertFalse(single_body_selector(x,[SimpleNamespace(kind=0),SimpleNamespace(kind=5)]));self.assertFalse(single_body_selector(x,[SimpleNamespace(kind=1)]))
            for target in ('self','all_allies','unported'):
                self.assertFalse(single_body_selector(dict(e,target=target),[SimpleNamespace(kind=0)]))
            x=copy.deepcopy(e);x['target_counter']['world_scope']='physical_actor';self.assertFalse(single_body_selector(x,[SimpleNamespace(kind=0)]));self.assertEqual(e,before)
    def test_source_projection_rejects_unreviewed_queue_changes(self):
        from portable_full_burst_landing_source_contract import project_sources
        project_sources(ROOT)
        name='gpu/full_burst_landing_runtime.slang';s=(ROOT/name).read_text()
        with self.assertRaises(AssertionError):project_sources(ROOT,{name:s.replace('index<end','index<results[header]')})
if __name__=='__main__':unittest.main()
