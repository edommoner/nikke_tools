"""Typed admission, independent quantity observations and bounded pool allocation."""
from unittest.mock import patch
import copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import portable_runtime
from portable_heal_charge_cases import fixtures
from portable_heal_charge_specs import validate
from portable_specs import LIMITS as L,FIELDS as F

def adapter():
    s=importlib.util.spec_from_file_location('healing_charge_test_adapter',ROOT/'research/verify-world-heal-charge-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class HealChargeGPUContracts(unittest.TestCase):
    def test_same_table_and_single_word_refusals(self):
        rows,packed=adapter().prepare();self.assertEqual((len(rows),sum(d is not None for _,w,d in rows)),(37,29))
        for _,w,_ in rows[29:]:self.assertEqual(sum(a!=b for a,b in zip(rows[0][1],w)),1)
    def test_canonical_ids_and_static_policy_carry_no_cpu_quantities(self):
        m=adapter();c=fixtures()[7];w,metadata,body=m.suite.compile_case(c)
        for i,e in enumerate(c['effects']):
            stat=e['stat'];at=L['DEFINITION_BASE']+i*L['DEFINITION_WORDS'];policy=w[L['PROTECTION_DEFINITION_BASE']+i]
            if stat=='heal_overcharge_store_atk_pct':self.assertEqual((w[at+F['KIND']],w[at+F['STAT']],policy),(0,76,10))
            if stat=='accumulate_max_scale_pct':self.assertEqual((w[at+F['KIND']],w[at+F['STAT']],policy),(0,77,267))
            if stat=='heal_overcharge_discharge':self.assertEqual((w[at+F['KIND']],w[at+F['STAT']],policy),(32,0,12))
        self.assertEqual(w[L['PROTECTION_META_BASE']],65)
    def test_unported_interpretations_rejected_before_packing(self):
        pool=fixtures()[0]['effects'][1];release=fixtures()[0]['effects'][2];boost=fixtures()[7]['effects'][2];combat=fixtures()[0]['combat']
        for e in (dict(pool,type='instant'),dict(pool,tick_interval=.1),dict(pool,scaling='max_hp'),dict(release,scaling='stack_count'),dict(release,target_effect=''),dict(boost,target_effect=None)):
            with self.subTest(effect=e),self.assertRaises(ValueError):portable_runtime.validate_effect(e,combat=combat,world_frame=True)
        for kwargs in (dict(combat=None,world_frame=True),dict(combat=combat,world_frame=False)):
            with self.assertRaises(ValueError):validate(pool,**kwargs)
    def test_trace_uses_actual_native_capacity_returns_not_hp_deltas(self):
        m=adapter();c=fixtures()[1];w,meta,b=m.suite.compile_case(c);n=m.native_reference((c,meta,b));trace=m.expected_trace(n['battle']['healing_charge']['events'])
        self.assertEqual([r[0] for r in trace],[1,2,3]);self.assertEqual(trace[1][4:],(0.,1000.,1500.,1000.));self.assertEqual(trace[2][4],1000.)
        self.assertEqual([a['hp'] for a in n['battle']['allies']],[10000.]*5)
    def test_comparison_returns_the_complete_immutable_native_fingerprint(self):
        m=adapter();c=fixtures()[1];w,meta,b=m.suite.compile_case(c);domain=(c,meta,b);native=m.native_reference(domain);saved=copy.deepcopy(native)
        trace=m.expected_trace(native['battle']['healing_charge']['events']);block=[0]*L['WORLD_RELOAD_OUTPUT_WORDS']
        block[m.TRACE_BASE:m.TRACE_BASE+8]=[m.TRACE_MAGIC,len(trace),len(trace),0,0,0,0,0]
        for i,row in enumerate(trace):
            at=m.TRACE_BASE+8+i*m.TRACE_WORDS;block[at:at+m.TRACE_WORDS]=m.trace_words(row)
        with patch.object(m,'native_reference',return_value=native),patch.object(m.prior.prior.prior.landing.base,'compare_expected') as compare:
            result=m.compare(block,domain)
            self.assertEqual(result,saved);self.assertEqual(native,saved)
            self.assertNotIn('healing_charge',compare.call_args.args[2]['battle'])
    def test_trace_rejects_wrong_quantity_order_and_omitted_observations(self):
        m=adapter();c=fixtures()[1];w,meta,b=m.suite.compile_case(c);domain=(c,meta,b);native=m.native_reference(domain)
        trace=m.expected_trace(native['battle']['healing_charge']['events']);base=[0]*L['WORLD_RELOAD_OUTPUT_WORDS'];base[m.TRACE_BASE:m.TRACE_BASE+8]=[m.TRACE_MAGIC,len(trace),len(trace),0,0,0,0,0]
        for i,row in enumerate(trace):
            at=m.TRACE_BASE+8+i*m.TRACE_WORDS;base[at:at+m.TRACE_WORDS]=m.trace_words(row)
        for offset in (m.TRACE_BASE+2,m.TRACE_BASE+8,m.TRACE_BASE+8+m.TRACE_WORDS+7):
            block=list(base);block[offset]^=1
            with patch.object(m,'native_reference',return_value=native),patch.object(m.prior.prior.prior.landing.base,'compare_expected'),self.assertRaises(AssertionError):m.compare(block,domain)
    def test_scratch_bank_capacity_does_not_overlap_existing_maxima(self):
        from portable_scratch_layout import verify
        r=verify(L,mode='heal-charge');self.assertTrue(r['verified'])
        self.assertEqual(L['PROTECTION_OBJECTS'],1024)
    def test_source_inverse_exact_and_unknown_edits_rejected(self):
        from portable_heal_charge_source_contract import project_sources
        d=json.loads((ROOT/'tests/fixtures/portable-heal-charge-source-delta.json').read_text());result=project_sources(ROOT)
        for name,row in d['sources'].items():
            self.assertEqual(result[name],row['baseline'])
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:row['current']+'\n'})
        for name in d['added_sources']:
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})
if __name__=='__main__':unittest.main()
