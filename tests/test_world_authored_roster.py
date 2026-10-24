"""Per-slot levels must survive the common compiler and native battle routes."""
import array,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from world_authored_roster import skill_levels
from destructible_original_battle_cases import fixtures,original,CHARACTER
from destructible_skill_specs import coefficient
from portable_specs import LIMITS as L,FIELDS as F
s=importlib.util.spec_from_file_location('original_battle_tests',ROOT/'research/verify-destructible-original-battle-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class AuthoredRosterTests(unittest.TestCase):
    def test_levels_are_complete_strict_and_detached(self):
        self.assertEqual(skill_levels({}),[{'1':10,'2':10,'3':10} for _ in range(5)])
        for bad in [None,{},[],[{'1':1,'2':2,'3':3}]*4,[{'1':1,'2':2}]*5,[{'1':True,'2':2,'3':3}]*5,[{'1':0,'2':2,'3':3}]*5,[{'1':11,'2':2,'3':3}]*5,[{'1':1.,'2':2,'3':3}]*5]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):skill_levels(dict(skill_levels=bad))
        c=fixtures()[0];answer=skill_levels(c);answer[0]['3']=10;self.assertEqual(c['skill_levels'][0]['3'],1)
    def test_original_definition_is_unchanged_and_owner_levels_select_the_wire_value(self):
        from calculator.buff_manager import _get_skill_lv
        for c in fixtures():
            before=copy.deepcopy(c);words,domain=a.battle.compile_case(c)
            index=next(i for i,e in enumerate(c['effects']) if e.get('target')=='all_projectiles');owner=c['owners'][index]
            self.assertEqual(c['effects'][index],original());self.assertEqual(c['names'][owner],CHARACTER)
            value=coefficient(original(),dict(name=CHARACTER,skill_levels=skill_levels(c)[owner]))
            row=domain[1]['binding_source_indices'].index(index);self.assertEqual(a.battle.number(words,L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['VALUE']),value)
            self.assertEqual(value,original()['values'][str(c['skill_levels'][owner]['3'])]);self.assertEqual(c,before)
    def test_real_burst_clock_uses_original_levels_and_named_completion(self):
        answers={c['name'].split('/')[-1]:a.native_reference(a.battle.compile_case(c)[1]) for c in fixtures()}
        for name,amount in [('level1',240.),('level5',313.),('level10',405.),('defense0',450.),('live-buff',631.),('named-child',405.),('last-owner',240.)]:
            with self.subTest(name=name):
                attacks=answers[name]['typed']['attacks'];self.assertEqual(len(attacks),1);self.assertEqual(attacks[0]['damage'],amount);self.assertAlmostEqual(attacks[0]['time'],.2)
                self.assertEqual(attacks[0]['owner'],4 if name=='last-owner' else 0)
        self.assertEqual(answers['named-child']['battle']['damage'],[484.,0,0,0,0]);self.assertEqual(answers['empty-targets']['typed']['attacks'],[])
    def test_original_table_packing_does_not_observe_native_events(self):
        with patch.object(a,'native_reference',side_effect=AssertionError('No oracle')),patch.object(a.battle,'observe',side_effect=AssertionError('No events')):rows,data=a.prepare()
        self.assertEqual(len(rows),8);self.assertEqual(len(data),4+8*109536*4)
    def test_existing44_inputs_and_all_native_fingerprints_are_retained(self):
        import nikke_gpu
        old=json.loads((ROOT/'research/portable-destructible-battle-short-expected.json').read_text());rows,data=a.battle.prepare()
        self.assertEqual(hashlib.sha256(data).hexdigest(),old['input_sha256'])
        for (name,words,domain),expected in zip(rows,old['entries']):
            self.assertEqual(name,expected['name']);self.assertEqual(nikke_gpu.native_hash(a.battle,domain),expected['native_sha256'])
    def test_saved_actual_metal_blocks_check_original_coefficients_and_owner(self):
        from portable_destructible_shield_source_contract import verify_retained_sources
        from portable_backend import source_hashes
        fixture=json.loads((ROOT/'tests/fixtures/portable-destructible-original-battle-raw.json').read_text())
        verify_retained_sources(ROOT,'gpu/destructible_battle_entry.slang',fixture['source_sha256'])
        rows,_=a.prepare()
        for record,(name,words,domain) in zip(fixture['records'],rows):
            self.assertEqual(record['name'],name);self.assertEqual(hashlib.sha256(array.array('I',words).tobytes()).hexdigest(),record['input_sha256'])
            block=array.array('I',[0])*fixture['output_words']
            for at,value in record['nonzero']:block[at]=value
            self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),record['output_sha256']);a.compare(block,domain)
            if name.endswith('/empty-targets'):
                changed=array.array('I',block);changed[786433]=1
                with self.assertRaises(AssertionError):a.compare(changed,domain)
            else:
                for offset in (790002,790006,790008,790019):
                    changed=array.array('I',block);changed[offset]^=1
                    with self.subTest(name=name,offset=offset),self.assertRaises(AssertionError):a.compare(changed,domain)

    def test_unchanged_shader_matches_typed44_and_normal492(self):
        from portable_destructible_shield_source_contract import verify_retained_sources
        from portable_backend import source_hashes
        for entry,golden in [('gpu/destructible_battle_entry.slang','research/portable-destructible-battle-short-expected.json'),('gpu/world_projectile_chain_entry.slang','research/portable-world-projectile-chain-retention-short-expected.json')]:
            verify_retained_sources(ROOT,entry,json.loads((ROOT/golden).read_text())['source_sha256'])

if __name__=='__main__':unittest.main()
