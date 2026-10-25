"""Legal mixed scenes reuse real native routing and the shared GPU runtime."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from portable_coordinate_mixed_cases import fixtures
from portable_coordinate_mixed_contracts import verify
from world_coordinate_mixed_native import observe
from world_coordinate_group_native import observe as baseline
from portable_coordinate_route_audit import verify as audit
spec=importlib.util.spec_from_file_location('mixed_adapter',ROOT/'research/verify-coordinate-mixed-short.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

class MixedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=fixtures();cls.before=copy.deepcopy(cls.cases);cls.answers=[observe(c) for c in cls.cases]
    def test_all_literal_contracts_and_input_immutability(self):
        self.assertEqual(len(self.cases),19)
        for c,(n,t) in zip(self.cases,self.answers,strict=True):self.assertTrue(verify(c,n)['verified'])
        self.assertEqual(self.cases,self.before)
    def test_passive_observer_preserves_complete_native_battle_and_trace(self):
        for c,(n,t) in zip(self.cases,self.answers,strict=True):
            plain,trace=baseline(c);self.assertEqual({k:n[k] for k in plain},plain);self.assertEqual(t,trace)
    def test_all_old225_inputs_and_domains_retained_without_oracle_packing(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No oracle in wire')):
            new,raw=a.prepare();old,_=a.parent.prepare()
        self.assertEqual(new[:225],old);self.assertEqual((len(new),sum(d is not None for _,_,d in new)),(244,218));self.assertEqual(len(raw),4+244*a.INPUT_WORDS*4)
    def test_old_share_is_rejected_but_valid_split_is_a_separate_model(self):
        from calculator.boss_pattern import validate
        for patterns in [[dict(kind='parts',targets=[dict(name='p',hp=1,r=1,x=0,y=0,share=.5)])],[dict(kind='summon',spec=dict(count=1,hp=1,share=.5))]]:
            with self.assertRaisesRegex(ValueError,'share'):validate(patterns,coord=True)
        result=audit(ROOT);self.assertEqual(result['obsolete_share']['classification'],'native_reference_exclusion');self.assertTrue(result['valid_split_damage']['native_model_available']);self.assertFalse(result['calculation_verified'])
    def test_route_audit_rejects_changed_rejection_or_split_weight(self):
        name='research/upstream/nikke-calc-master/calculator/boss_pattern.py';text=(ROOT/name).read_text()
        for old,new in [('if "share" in raw:','if False:'),('1.0 / len(hit)','1.0 / 2')]:
            self.assertIn(old,text)
            with self.assertRaises(AssertionError):audit(ROOT,{name:text.replace(old,new,1)})
    def test_historical_gpu_source_inverse_and_complete_wire(self):
        from portable_backend import source_hashes,validate_composed_stride
        import json
        golden=json.loads((ROOT/'research/portable-coordinate-group-short-expected.json').read_text())
        from portable_coordinate_group_source_contract import historical_source_hashes
        from portable_coordinate_mixed_source_contract import project_sources
        self.assertEqual(historical_source_hashes(ROOT,a.parent.SOURCE,project_sources(ROOT)),golden['source_sha256']);validate_composed_stride(a.SOURCE,a.INPUT_WORDS,a.OUTPUT_WORDS)
    def test_legacy_scene_guard_is_preserved_and_new_world_nodes_use_same_slots(self):
        c=self.cases[4]
        with self.assertRaises(ValueError):a.parent.compile_case(c)
        w,m,bindings,desc=a.compile_case(c)
        for row in desc['rows']:self.assertEqual((int(bindings[row['slot']].kind),bindings[row['slot']].identity),(row['kind'],row['identity']))
    def test_exact_mixed_inverse_rejects_unreviewed_guards_trace_or_transport(self):
        from portable_coordinate_mixed_source_contract import project_sources,project_backend_source
        project_sources(ROOT)
        for name in ['gpu/world_overlay_runtime.slang','gpu/world_skill_runtime.slang','gpu/coordinate_area_runtime.slang']:
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n// unreviewed\n'})
        with self.assertRaises(ValueError):project_backend_source(ROOT,(ROOT/'app/portable_backend.py').read_text()+'\n# unreviewed\n')
    def test_split_contract_rejects_rounding_or_target_corruption(self):
        n=copy.deepcopy(self.answers[0][0]);p=next(p for p in n['landed_packets'] if p['skill_name']=='mixed-split');p['damage']=666
        with self.assertRaises(AssertionError):verify(self.cases[0],n)

if __name__=='__main__':unittest.main()
