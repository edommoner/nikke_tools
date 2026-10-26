"""Composition keeps the complete prior wire and explicitly separates typed banks."""
import copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);a=importlib.util.module_from_spec(s);s.loader.exec_module(a);return a
class CoordinateTypedTests(unittest.TestCase):
    def test_nonoverlapping_complete_wire_and_registered_source(self):
        from portable_coordinate_typed_specs import check_layout,INPUT_WORDS,OUTPUT_WORDS,SOURCE
        from portable_backend import validate_composed_stride
        p=check_layout(ROOT);self.assertEqual((INPUT_WORDS,OUTPUT_WORDS),(115680,2032000));self.assertEqual(p['output'][1]['base'],1769856)
        validate_composed_stride(SOURCE,INPUT_WORDS,OUTPUT_WORDS)
        from portable_arena_specs import audit_profile,audit_regions,Region
        plan=audit_profile('coordinate-typed-v1');self.assertTrue(plan['address_plan_verified']);self.assertFalse(plan['gpu_execution_verified'])
        from portable_coordinate_typed_specs import regions
        rows,iw,ow=regions();bad=rows+[Region('output','overlap-probe',1769856,1)];self.assertFalse(audit_regions(bad,iw,ow)['address_plan_verified'])
        for src,iw,ow in [('gpu/world_coordinate_original_shared_entry.slang',INPUT_WORDS,OUTPUT_WORDS),(SOURCE,INPUT_WORDS-1,OUTPUT_WORDS),(SOURCE,INPUT_WORDS,OUTPUT_WORDS-1)]:
            with self.subTest(src=src,iw=iw,ow=ow),self.assertRaises(ValueError):validate_composed_stride(src,iw,ow)
    def test_disabled_original_prefix_and_every_original_effect_are_kept(self):
        a=module('typed_coordinate_input_test','research/verify-coordinate-typed-short.py')
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU schedule in input')):rows,_=a.prepare()
        self.assertEqual(len(rows),10);name,words,d=rows[0]
        old=json.loads((ROOT/'research/portable-coordinate-original-short-expected.json').read_text())['entries'][0]
        import array
        self.assertEqual(hashlib.sha256(array.array('I',words[:109968]).tobytes()).hexdigest(),old['input_sha256']);self.assertFalse(any(words[109968:]))
        for name,words,(c,m,b,scene) in rows[1:]:
            self.assertEqual(c['effects'][:-1],[e['effect'] for e in c['original_run']['prepared']['effects']]);self.assertEqual(len(m['binding_source_indices']),len(c['effects']))
            source=m['binding_source_indices'].index(c['probe_source']);self.assertEqual(words[109968+5424:109968+5680],[c['probe_kind'] if i==source else 0 for i in range(256)])
    def test_old19_original_modifier_inputs_and_native_observer_are_identical(self):
        a=module('typed_retained_modifier_test','research/verify-original-modifier-probe-short.py');old=json.loads((ROOT/'research/portable-original-modifier-probe-short-expected.json').read_text())
        import array
        rows,_=a.prepare();self.assertEqual(len(rows),19)
        for (name,w,d),entry in zip(rows,old['entries'],strict=True):
            self.assertEqual(name,entry['name']);self.assertEqual(hashlib.sha256(array.array('I',w).tobytes()).hexdigest(),entry['input_sha256']);self.assertEqual(a.cross.digest(a.native_reference(d)),entry['native_sha256'])
    def test_typed_trace_partition_requires_exact_independently_checked_packets(self):
        a=module('typed_trace_partition_test','research/verify-coordinate-typed-short.py')
        trace=[dict(row=4,created=2.,landed=2.,amount=123.,hit=1,hits=1),dict(row=2,created=2.,landed=2.,amount=77.,hit=1,hits=1)]
        attacks=[dict(time=2.,damage=123.,owner=0,completed=True)]
        rest,typed=a.partition_trace(trace,attacks,4,0);self.assertEqual(rest,[trace[1]]);self.assertEqual(typed,[trace[0]])
        for key,value in [('damage',124.),('time',2.1),('owner',1),('completed',False)]:
            bad=copy.deepcopy(attacks);bad[0][key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):a.partition_trace(trace,bad,4,0)
        with self.assertRaises(AssertionError):a.partition_trace(trace,[],4,0)
    def test_live_parent_context_checks_both_disjoint_receipt_sets(self):
        from world_coordinate_comparison_context import validate
        case=dict(coordinate_typed_probe=True,probe_source=4,sampled_vital=True)
        ordinary=dict(row=2,created=1.,landed=1.,amount=77.,hit=1,hits=1);typed=dict(row=4,created=2.,landed=2.,amount=123.,hit=1,hits=1)
        native=dict(skill_trace=[ordinary],typed_target_battle=dict(suppressed_body_trace=[typed]));receipts=[ordinary,typed]
        validate((case,),native,receipts)
        for index in (0,1):
            bad=copy.deepcopy(receipts);bad[index]['amount']+=1
            with self.subTest(index=index),self.assertRaises(AssertionError):validate((case,),native,bad)
        for bad in (receipts[:1],receipts+[typed]):
            with self.assertRaises(AssertionError):validate((case,),native,bad)
    def test_clear_bank_and_counter_context_corruption_is_rejected(self):
        from portable_coordinate_typed_specs import OUTPUT_WORDS,regions,audit_reserved
        from portable_specs import LIMITS
        block=[0]*OUTPUT_WORDS;self.assertTrue(audit_reserved(block))
        positions=[r.base for r in regions()[0] if r.domain=='output' and ('reserved' in r.name or r.name.endswith('clear-tail'))]+[LIMITS['COUNTER_CONTEXT_BASE']]
        for at in positions:
            block[at]=1
            with self.subTest(at=at),self.assertRaises(AssertionError):audit_reserved(block)
            block[at]=0
        with self.assertRaises(AssertionError):audit_reserved(block[:-1])
    def test_exact_historical_inverse_and_unreviewed_change_rejection(self):
        from portable_coordinate_typed_source_contract import project_sources,ledger
        data=ledger(ROOT);old=project_sources(ROOT)
        for name,row in data['sources'].items():
            self.assertEqual(hashlib.sha256(old[name].encode()).hexdigest(),row['baseline_sha256'])
            with self.subTest(name=name),self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// unreviewed\n'})
if __name__=='__main__':unittest.main()
