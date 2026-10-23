"""Original definition lowering and ordinary scalar damage ownership."""
import array,copy,hashlib,importlib.util,json,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
s=importlib.util.spec_from_file_location('ds_unit',ROOT/'research/verify-destructible-skill-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
from destructible_skill_specs import coefficient,compiler_effect
from portable_specs import LIMITS as L,FIELDS as F
class SkillTests(unittest.TestCase):
    def test_original_definition_levels_and_existing_scalar_formula(self):
        answers={c['name'].split('/')[-1]:a.native_reference(c) for c in a.fixtures()}
        number=lambda x:struct.unpack('<d',bytes.fromhex(x))[0]
        self.assertEqual(number(answers['original-level1']['sampled']['coefficient']),24.76)
        self.assertEqual(number(answers['original-level10']['sampled']['coefficient']),41.9)
        self.assertEqual(number(answers['original-level10']['sampled']['damage']),450.)
        self.assertEqual(number(answers['original-full-burst']['sampled']['damage']),660.)
        self.assertEqual(number(answers['explicit-defense100']['sampled']['damage']),405.)
        self.assertEqual(number(answers['live-attack-buff']['sampled']['damage']),619.)
        self.assertEqual(answers['expired-buff']['sampled'],answers['original-level10']['sampled'])
        self.assertEqual(answers['empty-selection']['receipts'],[])
        zero=answers['zero-coefficient'];self.assertEqual(zero['receipts'],[]);self.assertEqual(zero['trace'],[])
        self.assertEqual(number(zero['sampled']['damage']),0.)
        live=answers['original-level10'];self.assertEqual([number(r['remaining']) for r in live['state'][:2]],[550.,550.]);self.assertEqual(number(live['atk']),11.)
    def test_lowering_changes_route_and_selects_original_level_only(self):
        for c in a.fixtures():
            e=c['effects'][c['skill_row']];before=copy.deepcopy(e);lowered=compiler_effect(e,a.character(c))
            self.assertEqual(e,before);self.assertEqual(lowered['name'],e['name']);self.assertEqual(lowered['trigger'],e['trigger']);self.assertEqual(lowered['target'],'boss')
            self.assertEqual(lowered['fixed_value'],coefficient(e,a.character(c)))
            words=a.compile_case(c);at=L['DEFINITION_BASE']+c['skill_row']*L['DEFINITION_WORDS']
            self.assertEqual(words[at+F['KIND']],3);self.assertEqual(words[at+F['DAMAGE_FLAGS']],0)
            self.assertEqual(words[0],L['WORLD_SKILL_ABI']);self.assertEqual(words[L['TARGET_COUNTER_INPUT_BASE']+6],7)
            self.assertEqual(words[L['COMMAND_BASE']+1:L['COMMAND_BASE']+3],words[L['WORLD_FRAME_INPUT_BASE']+6:L['WORLD_FRAME_INPUT_BASE']+8])
            self.assertEqual(words[L['DAMAGE_DEFINITION_BASE']],1)
            self.assertEqual(words[L['TARGET_COUNTER_INPUT_BASE']+9:L['TARGET_COUNTER_INPUT_BASE']+12],[2,10,1])
    def test_unmodeled_semantics_cannot_be_silently_removed(self):
        c=a.fixtures()[0];e=c['effects'][c['skill_row']]
        for extra in [dict(scaling='stack_count'),dict(damage_formula='normal_attack'),dict(hits_parts=True),dict(target='all_enemies'),dict(fixed_value=1.),dict(values=[]),dict(values={'1':float('nan')})]:
            with self.subTest(extra=extra),self.assertRaises(ValueError):compiler_effect(dict(e,**extra),a.character(c))
    def test_packing_runs_no_damage_oracle_or_gpu(self):
        import portable_backend
        with patch.object(a,'native_reference',side_effect=AssertionError('No oracle')),patch.object(portable_backend,'build',side_effect=AssertionError('No GPU')):
            rows,data=a.prepare()
        self.assertEqual((len(rows),sum(c is not None for _,_,c in rows)),(18,10));self.assertEqual(len(data),4+18*102600*4)
    def test_old_projectile_producer_inputs_and_native_results_are_preserved(self):
        old=json.loads((ROOT/'research/portable-destructible-attack-short-expected.json').read_text());rows,data=a.attack.prepare()
        self.assertEqual(hashlib.sha256(data).hexdigest(),old['input_sha256'])
        for (name,_,c),saved in zip(rows,old['entries']):
            self.assertEqual(name,saved['name']);self.assertEqual(a.attack.cross.digest(a.attack.native_reference(c) if c is not None else dict(status=64)),saved['native_sha256'])
    def test_saved_gpu_checks_scalar_context_and_landing_results(self):
        from portable_backend import source_hashes
        fixture=json.loads((ROOT/'tests/fixtures/portable-destructible-skill-raw.json').read_text())
        self.assertEqual(fixture['source_sha256'],source_hashes('gpu/destructible_skill_probe.slang'));rows,_=a.prepare()
        for record in fixture['records']:
            block=array.array('I',[0])*786432
            for i,v in record['nonzero']:block[i]=v
            self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),record['output_sha256'])
            name,_,c=rows[record['index']];self.assertEqual(name,record['name'])
            if c is None:
                a.validate_rejection(block,name);block[0]=0
                with self.assertRaises(AssertionError):a.validate_rejection(block,name)
                continue
            a.compare(block,c)
            for offset in [705004,705006,710000,616386,705000]:
                changed=array.array('I',block);changed[offset]^=1
                with self.subTest(name=name,offset=offset),self.assertRaises(AssertionError):a.compare(changed,c)
    def test_zero_coefficient_still_requires_valid_owned_context(self):
        from destructible_world_runtime import DestructibleWorld
        from destructible_skill_runtime import execute
        from test_target_counter_runtime import manager,NAMES
        c=next(c for c in a.fixtures() if c['name'].endswith('zero-coefficient'));bm=manager(c['effects']);world=DestructibleWorld(c['nodes'],c['bindings']);world.advance(0.)
        kw=dict(base_attack=1000.,weapon={},defense=0.,attack_id=123)
        for bad in [dict(attack_id=True),dict(attack_id=1<<24),dict(defense=float('nan')),dict(full_burst=1)]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):execute(world,bm,c['effects'][-1],a.character(c),**dict(kw,**bad))
        with self.assertRaises(ValueError):execute(world,bm,c['effects'][-1],dict(a.character(c),name='unbound'),**kw)
if __name__=='__main__':unittest.main()
