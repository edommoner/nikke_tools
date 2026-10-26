"""Wire retention across shared target-carrier lowering, no simulation needed."""
import array,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
from portable_target_modifier_input import lower_effect,pack_axes
from portable_specs import LIMITS as L,FIELDS as F
class TargetModifierInputTests(unittest.TestCase):
    def test_original_before_refactor_eight_complete_wire_images(self):
        s=importlib.util.spec_from_file_location('target_lowering_factory',ROOT/'research/verify-world-projectile-rosters.py');f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
        from portable_destructible_roster_input import compile_weapon_shield_roster
        from calculator import timeline
        records=json.loads((ROOT/'tests/fixtures/target-modifier-old-wire.json').read_text())['rows']
        with patch.object(timeline,'simulate',side_effect=AssertionError('Packing must not simulate')):
            for r in records:
                body=dict(f.body_for(f.policy.roster_for(r['name']),r['duration']),seed=4301,burst_gauge_mode='accumulate');body['enemy']['patterns']=[dict(id='reuse-shield',kind='idle',until=dict(time=r['duration']))]
                p=f.engine_worker.evaluate(dict(body,_portable_static_inputs=True));before=copy.deepcopy(p)
                words,meta=compile_weapon_shield_roster(p,[dict(node='reuse-shield',kind=r['kind'],identity=10,capacity=1000000.,owner=[0,0,1])],skill_shields=r['name']=='레이')
                self.assertEqual(p,before);self.assertEqual(meta['binding_source_indices'],r['bindings']);self.assertEqual(hashlib.sha256(array.array('I',words).tobytes()).hexdigest(),r['words_sha256'])
    def test_prior_modifier18_and_shield88_wire_images_are_identical(self):
        data=json.loads((ROOT/'tests/fixtures/target-modifier-old-suites.json').read_text())
        for table in data['suites']:
            s=importlib.util.spec_from_file_location('retained_'+table['adapter'],ROOT/'research'/table['adapter']);a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
            rows,_=a.prepare();self.assertEqual(len(rows),len(table['entries']))
            for (name,words,domain),expected in zip(rows,table['entries'],strict=True):
                self.assertEqual(name,expected['name']);self.assertEqual(domain is not None,expected['native']);self.assertEqual(hashlib.sha256(array.array('I',words).tobytes()).hexdigest(),expected['sha256'])
    def test_receipt_copy_historical_inverse_rejects_any_unreviewed_change(self):
        from portable_coordinate_full_burst_source_contract import project_file,ledger
        name='gpu/full_burst_landing_runtime.slang';row=ledger(ROOT)['sources'][name]
        value=project_file(ROOT,name);self.assertEqual(hashlib.sha256(value.encode()).hexdigest(),row['baseline_sha256'])
        with self.assertRaises(AssertionError):project_file(ROOT,name,(ROOT/name).read_text()+'\n// unreviewed\n')
    def test_axis_identity_and_rejections_without_mutating_definitions(self):
        effects=[dict(type='buff',name='p',stat='projectile_dmg_pct',target='self'),dict(type='buff',name='s',stat='shield_dmg_pct',target='all_allies')];before=copy.deepcopy(effects)
        self.assertEqual([lower_effect(e)['stat'] for e in effects],['atk_dmg_pct']*2);self.assertEqual(effects,before)
        words=[0]*L['INPUT_WORDS'];meta=dict(binding_source_indices=[1,0]);axes=pack_axes(words,meta,effects);self.assertEqual(axes[:3],[3,2,0])
        for row in range(2):self.assertEqual(words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['KIND']],4)
        for changed in (dict(target='all_enemies'),dict(scaling='stack_count'),dict(type='instant')):
            with self.assertRaises(ValueError):lower_effect(dict(effects[0],**changed))
        with self.assertRaises(ValueError):pack_axes(words,meta,effects)
if __name__=='__main__':unittest.main()
