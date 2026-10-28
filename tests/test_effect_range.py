"""Meaningful source, purity, recipient, expiry and selection boundaries."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
from portable_effect_range_cases import fixtures,native,original
from effect_range_policy import query,MODEL,validate_effect
from test_target_counter_runtime import manager,NAMES
class EffectRange(unittest.TestCase):
    def test_original_modifier_is_byte_preserved_and_changes_real_selection(self):
        rows=fixtures();self.assertEqual(original()[0],'레이 (가칭)');self.assertEqual(rows[0]['effects'][1],original()[1])
        expanded=native(rows[0]);ordinary=native(rows[1])
        self.assertEqual(expanded['radius'],6.);self.assertEqual(ordinary['radius'],1.)
        self.assertEqual(expanded['selected'],[0,1,2,4]);self.assertEqual(ordinary['selected'],[0])
        self.assertEqual(native(rows[2])['radius'],1.);self.assertEqual(native(rows[4])['radius'],6.)
        self.assertEqual(native(rows[3])['radius'],1.)
    def test_fractional_ordered_negative_zero_removal_and_refresh(self):
        rows={r['name'].split('/')[-1]:native(r) for r in fixtures()}
        self.assertEqual(rows['derived-fractional-allies']['factor'],1.125)
        self.assertEqual(rows['derived-ordered-addition']['percent'],112.5)
        self.assertEqual(rows['derived-negative-half']['radius'],.5)
        self.assertEqual(rows['derived-empty-radius-boundary']['selected'],[0])
        self.assertEqual(rows['derived-named-removal']['radius'],1.)
        self.assertEqual(rows['derived-refresh']['radius'],1.125)
    def test_query_preserves_native_caches_carriers_and_global_maps(self):
        e=dict(original()[1],target='all_allies');bm=manager([e]);bm.notify('full_burst_start',0.,NAMES[0])
        from calculator import buff_manager as b
        before=copy.deepcopy((bm._active,bm._plan_cache,bm._buffs_cache,bm.state));maps=(dict(b._STAT_TO_BUFF),dict(b._BUFFS_ZERO))
        answer=query(bm,NAMES[1],e['target_effect'],.1,base_radius=1.,model=MODEL)
        self.assertEqual(answer['radius'],6.);self.assertEqual(before,(bm._active,bm._plan_cache,bm._buffs_cache,bm.state))
        self.assertEqual(maps,(b._STAT_TO_BUFF,b._BUFFS_ZERO));self.assertNotIn('effect_range_pct',bm.get_buffs(NAMES[1],'__enemy__',.1))
    def test_readback_array_and_list_share_the_same_wire_contract(self):
        import array
        from portable_effect_range_specs import OUTPUT,OUTPUT_BASE,MAGIC,words,decode
        q=dict(who=1,marker='test',time=.1,targets=[[1,2.,0.,1.,0.,0.,0.]])
        meta=dict(named_range_selection=dict(selection=q),states=dict(test=2))
        raw=[0]*OUTPUT;row=[0]*32;row[:4]=[MAGIC,1,2,1];row[14:16]=[1,1]
        for at,value in ((4,500.),(6,6.),(8,1.),(10,6.),(12,.1),(16,1.)):row[at:at+2]=words(value)
        raw[OUTPUT_BASE:OUTPUT_BASE+32]=row
        expected=dict(percent=500.,factor=6.,base_radius=1.,radius=6.,selected=[0],distances=[1.])
        self.assertEqual(decode(raw,meta),expected);self.assertEqual(decode(array.array('I',raw),meta),expected)
    def test_scoped_seal_does_not_open_battle_default_or_cuda_admission(self):
        import hashlib,nikke_gpu
        from portable_backend import source_hashes
        from portable_readiness_semantics import reference_readiness
        config=nikke_gpu.SUITES['named-effect-range'];self.assertFalse(config['development_only'])
        self.assertIn('research/portable-coordinate-arcs-short-expected.json',config['support_files'])
        golden=json.loads((ROOT/config['golden']).read_text())
        from portable_source_baseline import check
        source=check(ROOT,nikke_gpu,'named-effect-range')
        self.assertEqual(source['source_sha256'],source_hashes(config['source']))
        self.assertFalse(source['calculation_verified'])
        cached=nikke_gpu.SUITES['named-effect-range-cache-only'];self.assertEqual(cached['golden'],config['golden'])
        self.assertTrue(cached['require_paired_generation']);self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1')
        r=reference_readiness(dict(phase='effect',kind='buff',stat='effect_range_pct',target='self'))
        proof=r['declared_named_range_selection'];raw=(ROOT/proof['evidence']).read_bytes();a=json.loads(raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),proof['evidence_sha256'])
        self.assertTrue(a['calculation_verified']);self.assertFalse(a['live_parent_receipt_present']);self.assertEqual(a['gpu_calls'],0)
        self.assertEqual((a['input_count'],a['native_cases']),(21,12));self.assertFalse(proof['battle_damage_delivery_verified'])
        self.assertFalse(proof['current_cuda_verified']);self.assertFalse(proof['default_producer_installed']);self.assertFalse(r['gpu_supported'])
        self.assertEqual(r['lane'],'reference_model_gap')
    def test_current_source_recertification_retains_every_historical_result(self):
        old=json.loads((ROOT/'research/portable-named-effect-range-v1-expected.json').read_text())
        new=json.loads((ROOT/'research/portable-named-effect-range-v2-expected.json').read_text())
        for key in ('input_sha256','output_sha256','entries'):self.assertEqual(old[key],new[key])
        self.assertNotEqual(old['source_sha256'],new['source_sha256'])
    def test_invalid_numeric_and_unreviewed_target_contracts_fail_closed(self):
        for changes in (dict(fixed_value=True),dict(fixed_value=float('nan')),dict(fixed_value=-101.),dict(target='all_enemies'),dict(target_effect=''),dict(scaling='max_ammo')):
            with self.subTest(changes=changes),self.assertRaises(ValueError):validate_effect(dict(original()[1],**changes))
    def test_literal_wire_contains_no_selection_answers_and_raw_negatives(self):
        from portable_effect_range_specs import BASE,INPUT,OUTPUT
        s=importlib.util.spec_from_file_location('range_test_adapter',ROOT/'research/verify-named-effect-range.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
        rows,raw=a.prepare();self.assertEqual(len(rows),21);self.assertEqual(len(raw),4+21*INPUT*4)
        self.assertEqual(sum(d is not None for _,_,d in rows),12)
        self.assertEqual(rows[0][1][BASE:BASE+2],[0x45524731,1]);self.assertEqual(OUTPUT,159744)
if __name__=='__main__':unittest.main()
