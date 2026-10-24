"""Private shared lowering must preserve the original modifier case table."""
import array,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_specs import LIMITS as L,FIELDS as F
from portable_runtime import compile_program,UnsupportedPortable
s=importlib.util.spec_from_file_location('modifier_gpu_tests',ROOT/'research/verify-destructible-modifier-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class ModifierGPUTests(unittest.TestCase):
    def test_same_twenty_cpu_cases_pack_without_a_damage_oracle(self):
        before=copy.deepcopy(a.fixtures())
        with patch.object(a,'observe',side_effect=AssertionError('No oracle')),patch.object(a,'native_reference',side_effect=AssertionError('No oracle')):rows,data=a.prepare()
        self.assertEqual((len(rows),sum(c is not None for _,_,c in rows)),(29,20));self.assertEqual(len(data),4+29*86304*4);self.assertEqual(a.fixtures(),before)
    def test_modifier_axis_is_private_and_not_an_ordinary_damage_buff(self):
        for c in a.fixtures():
            words,_=a.compile_case(c)
            for row,e in enumerate(c['effects']):
                axis=a.AXES.get(e.get('stat'),0)
                self.assertEqual(words[86048+row],axis)
                if axis:
                    at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
                    self.assertEqual(words[at+F['STAT']],0);self.assertEqual(words[at+F['KIND']],4)
                    value=a.struct.unpack('<d',a.struct.pack('<II',*words[at+F['VALUE']:at+F['VALUE']+2]))[0]
                    self.assertEqual(value,e['fixed_value'])
        c=a.fixtures()[1];chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=a.engine_worker.META[n]) for n in a.NAMES]
        with self.assertRaises(UnsupportedPortable):compile_program(chars,[(e,a.NAMES[o]) for e,o in zip(c['effects'],c['owners'])],[[0,0,0,0,0,-1,0,0]],[1000]*5)
    def test_original_cpu_contracts_remain_literal_and_model_gaps(self):
        from portable_destructible_modifier_contracts import verify
        for c in a.fixtures():
            result=verify(c,a.native_reference(c));self.assertTrue(result['reference_model_gap']);self.assertFalse(result['in_game_rules_verified'])
    def test_previous_battle_sources_match_exact_reviewed_projection(self):
        from portable_backend import source_hashes
        from portable_destructible_shield_source_contract import verify_retained_sources
        for entry,golden in [('gpu/destructible_battle_entry.slang','research/portable-destructible-battle-short-expected.json'),('gpu/world_projectile_chain_entry.slang','research/portable-world-projectile-chain-retention-short-expected.json')]:
            verify_retained_sources(ROOT,entry,json.loads((ROOT/golden).read_text())['source_sha256'])
    def test_actual_metal_blocks_preserve_bits_and_reject_corruption(self):
        from portable_backend import source_hashes
        fixture=json.loads((ROOT/'tests/fixtures/portable-destructible-modifier-raw.json').read_text());self.assertEqual(fixture['source_sha256'],source_hashes('gpu/destructible_modifier_probe.slang'))
        rows,_=a.prepare()
        for record,(name,words,domain) in zip(fixture['records'],rows):
            self.assertEqual(record['name'],name);self.assertEqual(hashlib.sha256(array.array('I',words).tobytes()).hexdigest(),record['input_sha256'])
            block=array.array('I',[0])*fixture['output_words']
            for at,value in record['nonzero']:block[at]=value
            self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),record['output_sha256'])
            if domain is None:a.validate_rejection(block,name);continue
            a.compare(block,domain)
            for at in (0,159713,159714,159716,159718,159720,159743):
                changed=array.array('I',block);changed[at]^=1
                with self.subTest(name=name,offset=at),self.assertRaises(AssertionError):a.compare(changed,domain)

    def test_undefined_modifier_targets_and_scaling_are_rejected_before_packing(self):
        for change in [dict(target='boss'),dict(scaling='stack_count'),dict(type='damage')]:
            c=copy.deepcopy(a.fixtures()[1]);c['effects'][-1].update(change)
            with self.assertRaisesRegex(ValueError,'plain allied'):a.compile_case(c)

if __name__=='__main__':unittest.main()
