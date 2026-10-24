"""Real Frame values must freeze before sibling landings and nested modifiers."""
import array,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from calculator import timeline,buff_manager
from destructible_battle_runtime import typed_battle
from world_frame_native import observe
s=importlib.util.spec_from_file_location('modifier_battle_tests',ROOT/'research/verify-destructible-modifier-battle-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class ModifierBattleTests(unittest.TestCase):
    def test_twelve_full_native_battles_and_literal_values(self):
        answers={c['name'].split('/')[-1]:a.native_reference(a.compile_case(c)[1]) for c in a.fixtures()}
        amounts={'physical-body-is-unmodified':[1451.,1451.],'shield-factor-does-not-affect-projectiles':[968.,968.],'expiry-before-second-skill':[1451.,968.],'different-ally-self':[968.,968.],'squad-gift':[1451.,1451.],'ordinary-and-target-factor-add':[1838.,1838.],'two-stacks':[1935.,1935.],'named-completion-keeps-body-normal':[1451.],'named-coefficient-is-preserved':[2177.,2177.],'reentrant-parent-child-grandchild':[968.,1451.,1935.],'zero-factor-keeps-native-minimum':[1.,1.],'empty-world-has-no-query':[]}
        for name,values in amounts.items():
            with self.subTest(name=name):self.assertEqual([r['damage'] for r in answers[name]['typed']['attacks']],values)
        self.assertEqual(answers['physical-body-is-unmodified']['battle']['damage'][0],3872)
        self.assertEqual(answers['named-completion-keeps-body-normal']['battle']['damage'][0],484)
        nested=answers['reentrant-parent-child-grandchild'];self.assertEqual([r['remaining'] for r in nested['typed']['state']],[5646.,5646.]);self.assertEqual(nested['battle']['damage'][0],968)
        self.assertEqual(nested['typed']['attacks'][0]['receipts'][1]['took'],968.)
    def test_named_coefficient_is_observed_from_the_real_native_handler(self):
        c=next(c for c in a.fixtures() if c['name'].endswith('/named-coefficient-is-preserved'))
        with typed_battle(c['typed_bindings'],modifier_model=True) as data:observe(c)
        self.assertEqual([r['coefficient'] for r in data['attacks']],[150.,150.])
        self.assertEqual([r['damage'] for r in data['attacks']],[2177.,2177.])
        self.assertEqual(next(e['fixed_value'] for e in c['effects'] if e.get('target')=='all_projectiles'),100.)

    def test_no_cpu_event_list_or_scalar_value_enters_gpu_input(self):
        with patch.object(a.battle,'observe',side_effect=AssertionError('No oracle')),patch.object(a,'native_reference',side_effect=AssertionError('No oracle')):rows,data=a.prepare()
        self.assertEqual((len(rows),sum(c is not None for _,_,c in rows)),(18,12));self.assertEqual(len(data),4+18*109824*4)
    def test_existing_shader_closures_match_exact_reviewed_projection(self):
        from portable_destructible_shield_source_contract import verify_retained_sources
        from portable_backend import source_hashes
        import json
        for entry,golden in [('gpu/destructible_battle_entry.slang','research/portable-destructible-battle-short-expected.json'),('gpu/destructible_modifier_probe.slang','research/portable-destructible-modifier-short-expected.json')]:
            verify_retained_sources(ROOT,entry,json.loads((ROOT/golden).read_text())['source_sha256'])
        source=(ROOT/'gpu/destructible_modifier_battle_entry.slang').read_text();self.assertIn('#include "destructible_frame_runtime.slang"',source);self.assertIn('#include "destructible_modifier_runtime.slang"',source)
    def test_optional_native_scope_restores_even_after_failure(self):
        before=(timeline.BuffManager,timeline.calc_damage,buff_manager.BuffManager.get_buffs,dict(buff_manager._STAT_TO_BUFF))
        c=a.fixtures()[0]
        with patch('destructible_damage_policy.calculate',side_effect=RuntimeError('scalar failure')):
            with self.assertRaisesRegex(RuntimeError,'scalar failure'):
                with typed_battle(c['typed_bindings'],modifier_model=True):observe(c)
        self.assertEqual(before,(timeline.BuffManager,timeline.calc_damage,buff_manager.BuffManager.get_buffs,dict(buff_manager._STAT_TO_BUFF)))
        self.assertEqual(a.native_reference(a.compile_case(c)[1])['typed']['attacks'][0]['damage'],1451.)
    def test_saved_actual_metal_blocks_check_sampled_coefficients_and_frozen_siblings(self):
        from portable_destructible_shield_source_contract import verify_retained_sources
        from portable_backend import source_hashes
        f=json.loads((ROOT/'tests/fixtures/portable-destructible-modifier-battle-raw.json').read_text());verify_retained_sources(ROOT,'gpu/destructible_modifier_battle_entry.slang',f['source_sha256'])
        rows,_=a.prepare()
        for record in f['records']:
            name,words,domain=rows[record['index']];self.assertEqual(name,record['name']);self.assertEqual(hashlib.sha256(array.array('I',words).tobytes()).hexdigest(),record['input_sha256'])
            block=array.array('I',[0])*f['output_words']
            for at,value in record['nonzero']:block[at]=value
            self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),record['output_sha256'])
            if domain is None:a.validate_rejection(block,name);continue
            a.compare(block,domain)
            for at in (0,790002,790006,790008,790020,790022):
                changed=array.array('I',block);changed[at]^=1
                with self.subTest(name=name,offset=at),self.assertRaises(AssertionError):a.compare(changed,domain)
            if name.endswith('/named-coefficient-is-preserved'):
                changed=array.array('I',block);changed[790006:790008]=array.array('I',a.battle.struct.unpack('<II',a.battle.struct.pack('<d',100.)))
                with self.assertRaisesRegex(AssertionError,'coefficient'):a.compare(changed,domain)

    def test_undefined_target_model_is_rejected_by_packer_and_native(self):
        for change in [dict(target='boss'),dict(scaling='stack_count')]:
            c=copy.deepcopy(a.fixtures()[0]);c['effects'][0].update(change)
            with self.assertRaisesRegex(ValueError,'plain allied'):a.compile_case(c)
            with self.assertRaisesRegex(ValueError,'plain allied'):
                with typed_battle(c['typed_bindings'],modifier_model=True):observe(c)

if __name__=='__main__':unittest.main()
