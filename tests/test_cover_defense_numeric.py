"""Independent cover DEF, ordered arithmetic, original carrier and wire guards."""
import copy,hashlib,importlib.util,json,math,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('cover_numeric_adapter',ROOT/'research/verify-cover-defense-numeric.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
import engine_worker
from cover_defense_model import numeric,live_defense

class CoverDefenseNumeric(unittest.TestCase):
    def test_body_defense_cannot_change_cover_damage(self):
        low=numeric(1000.,100.,100.,128.57,0.,0.)
        high=numeric(1000.,100.,100.,128.57,0.,900.)
        self.assertEqual(low['values'][:2],high['values'][:2]);self.assertNotEqual(low['values'][2],high['values'][2])
        self.assertEqual(low['values'][0],100.*(1.+128.57/100.))
        self.assertEqual(low['values'][1],(1000.-low['values'][0])*100./100.)
        self.assertNotEqual(low['values'][1],1000.-low['values'][0])

    def test_floor_negative_modifiers_and_nonfinite_results(self):
        for q in [(0.,100.,100.,0.,0.,0.),(100.,0.,100.,0.,0.,0.),(1000.,100.,100.,0.,-100.,0.)]:self.assertEqual(numeric(*q)['values'][1:], [1.,1.])
        self.assertEqual(numeric(1000.,100.,100.,-200.,0.,0.)['values'][0],-100.)
        self.assertEqual(numeric(1e308,1000.,0.,0.,0.,0.),dict(status=16,values=None))
        for q in [(-1.,100.,0.,0.,0.,0.),(1.,100.,-1.,0.,0.,0.),(1.,math.inf,0.,0.,0.,0.)]:
            with self.assertRaises(ValueError):numeric(*q)

    def test_actual_original_carrier_rank_value_expiry_and_independent_base(self):
        from portable_original_identity_inventory import selected_prepared_profiles
        from calculator.buff_manager import BuffManager
        _,_,p=next(selected_prepared_profiles(['솔져 O.W.'],0));names=[c['name'] for c in p['chars']]
        state=dict(base_stats={name:dict(atk=atk,hp=1e6,**{'def':100000.*(i+1)}) for i,(name,atk) in enumerate(zip(names,p['base_atk']))},hp_pct={n:100. for n in names})
        manager=BuffManager(p['chars'],state)
        effect,caster=next((e,c) for e,c in manager._effects if c=='솔져 O.W.' and e.get('stat')=='cover_def_pct')
        before=copy.deepcopy(effect);manager._activate(effect,caster,10.)
        carrier=next(ab for ab in manager._active if ab.effect is effect)
        self.assertIsNone(carrier.target_chars)
        live_defense(manager,names[0],10.,1000.)
        targets=carrier.target_chars
        self.assertEqual(targets,[n for n,_ in sorted(zip(names,p['base_atk']),key=lambda item:item[1],reverse=True)][:3])
        for name in names:
            expected=1000.*(1.+128.57/100.) if name in targets else 1000.
            self.assertEqual(live_defense(manager,name,10.,1000.),expected)
            self.assertEqual(live_defense(manager,name,15.,1000.),1000.)
        self.assertEqual(effect,before)

    def test_vectors_and_wire_do_not_execute_a_battle(self):
        import engine_worker
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('Numeric oracle cannot simulate')):
            rows,data=m.prepare()
            for _,_,domain in rows:
                if domain is not None:self.assertIn(m.native_reference(domain)['status'],(0,16))
        self.assertEqual(len(rows),572);self.assertEqual(len(data),4+572*16*4)
        self.assertEqual(sum(d is not None for _,_,d in rows),562)

    def test_full_word_comparison_rejects_numeric_and_reserved_corruption(self):
        case=dict(name='corrupt',quantities=[1000.,100.,100.,128.57,0.,0.]);n=m.native_reference((case,))
        block=[0,m.MAGIC,0,0,*m.words(n['values']),0,0];m.compare(block,(case,))
        for at in (2,4,6,8,11):
            bad=list(block);bad[at]^=1
            with self.assertRaises(AssertionError):m.compare(bad,(case,))

    def test_sealed_scalar_proof_and_standalone_cached_profile_are_bound(self):
        import nikke_gpu as cli
        from portable_backend import source_hashes
        config=cli.SUITES['cover-defense-numeric'];cached=cli.SUITES['cover-defense-numeric-cache-only']
        self.assertFalse(config['development_only']);self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1')
        self.assertFalse(cached.get('require_paired_generation',False))
        for key in ('source','script','golden','inputs','native','input_words','output_words'):self.assertEqual(config[key],cached[key])
        golden=json.loads((ROOT/config['golden']).read_text());_,data=m.prepare()
        self.assertEqual(golden['input_sha256'],hashlib.sha256(data).hexdigest())
        self.assertEqual(golden['source_sha256'],source_hashes(m.SOURCE))
        receipt=json.loads((ROOT/'tests/fixtures/cover-defense-numeric-independent-v1.json').read_text())
        proof=json.loads((ROOT/'tests/fixtures/cover-defense-numeric-metal-v1.json').read_text())
        self.assertEqual((receipt['input_count'],receipt['native_cases'],receipt['gpu_calls']),(572,562,0));self.assertFalse(receipt['live_parent_receipt_present'])
        for key in ('input_sha256','output_sha256'):
            self.assertEqual(receipt[key],golden[key]);self.assertEqual(proof[key],golden[key])

    def test_numeric_evidence_does_not_remove_the_original_model_gap(self):
        from portable_readiness_semantics import reference_readiness
        result=reference_readiness(dict(phase='effect',kind='buff',stat='cover_def_pct',target='allies_top_atk:3'))
        self.assertEqual(result['lane'],'reference_model_gap');self.assertFalse(result['gpu_supported'])
        numeric=result['declared_cover_defense_numeric'];self.assertTrue(numeric['metal_verified'])
        self.assertEqual(numeric['evidence_sha256'],hashlib.sha256((ROOT/numeric['evidence']).read_bytes()).hexdigest())
        for key in ('cuda_verified','cover_layer_connected','original_full_battle_verified','in_game_level_curve_verified'):self.assertFalse(numeric[key])

if __name__=='__main__':unittest.main()
