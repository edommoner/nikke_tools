import copy,importlib.util,json,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_code_oracle import observe
from portable_specs import ABI,LIMITS as L
from portable_runtime import compile_program
from portable_code_specs import TARGET_CODE,code_names
s=importlib.util.spec_from_file_location('code_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
CASES=json.loads((R/'tests/fixtures/portable-enemy-codes.json').read_text())['cases']
def case(name):return next(c for c in CASES if c['name']=='enemy-code-'+name)
class EnemyCodeContracts(unittest.TestCase):
    def test_native_matrix_matches_exact_global_code(self):
        codes=['작열','수냉','풍압','전격','철갑','','unknown:code',' 전격 ']
        for wi,world in enumerate([None]+codes):
            for pi,predicate in enumerate(codes):self.assertEqual(observe(case('matrix-'+str(wi)+'-'+str(pi)))['queries'][0]['attack_buffs'][0],10 if not world or world==predicate else 0)
    def test_world_code_is_not_owned_by_a_character(self):
        for owner in range(5):
            for match in (True,False):self.assertEqual(observe(case('owner-'+str(owner)+'-'+str(match)))['queries'][0]['attack_buffs'],[10 if match else 0]*5)
    def test_passive_conditions_are_checked_at_runtime(self):
        for duration in (-1,1):
            self.assertEqual(observe(case('passive-'+str(duration)+'-False'))['queries'][0]['attack_buffs'][0],0)
            self.assertEqual([q['attack_buffs'][0] for q in observe(case('passive-'+str(duration)+'-True'))['queries']],[10,10])
    def test_code_and_dynamic_state_remain_separate_conditions(self):
        for match in (True,False):self.assertEqual([q['attack_buffs'][0] for q in observe(case('code-and-live-state-'+str(match)))['queries']],[0,10 if match else 0,0])
    def test_inherited_add_target_does_not_replace_global_code(self):
        for world in ('전격','풍압'):
            for predicate in ('전격','풍압'):
                r=observe(case('global-context-'+world+'-'+predicate))
                self.assertEqual([q['enemy_modifiers']['defense_pct'] for q in r['queries']],[0,-25 if world==predicate else 0])
    def test_code_and_actor_kind_conditions_can_be_combined(self):
        r=observe(case('global-code-and-add-context'));self.assertEqual([q['enemy_modifiers']['defense_pct'] for q in r['queries']],[0,-25])
    def test_zero_code_tag_means_native_missing_or_empty(self):
        for name in ('matrix-0-3','matrix-6-3'):
            words,_=v.compile_case(case(name));self.assertEqual(words[L['WORLD_META_BASE']],0);self.assertGreater(words[L['WORLD_META_BASE']+1],0)
    def test_compiler_encodes_names_instead_of_a_legacy_boolean(self):
        words,meta=v.compile_case(case('matrix-4-3'));at=L['CONDITION_BASE'];world=L['WORLD_META_BASE']
        self.assertEqual(words[at],TARGET_CODE);self.assertNotEqual(TARGET_CODE,22);self.assertEqual(words[at+1],words[world]);self.assertEqual(words[at+2:at+4],[0,0])
    def test_name_id_zero_is_not_confused_with_an_unspecified_code(self):
        words,meta=v.compile_case(case('label-collision'));self.assertEqual(meta['states']['gate'],0);self.assertEqual(words[L['WORLD_META_BASE']],1)
    def test_unneeded_world_metadata_does_not_use_name_capacity(self):
        states={str(i):i for i in range(256)};self.assertEqual(code_names([], '전격',states,256),(0,0));self.assertEqual(len(states),256)
    def test_invalid_code_types_fail_closed(self):
        for value in (0,False,[],{}):
            c=copy.deepcopy(case('matrix-4-3'));c['environment']['enemy_code']=value
            with self.subTest(value=value),self.assertRaises(ValueError):v.compile_case(c)
    def test_code_names_obey_the_shared_capacity(self):
        effects=[(dict(trigger=dict(condition=['target_code:전격'])), 'owner')]
        states={str(i):i for i in range(255)};self.assertEqual(code_names(effects,'전격',states,256),(256,256))
        with self.assertRaises(ValueError):code_names(effects,'풍압',states,256)
    def test_raw_target_damage_field_is_not_accidentally_admitted(self):
        c=copy.deepcopy(case('matrix-4-3'));c['effects'][0]['target_code']='전격'
        with self.assertRaises(ValueError):v.compile_case(c)
    def test_every_case_compiles_without_changing_authored_input(self):
        for c in CASES:
            before=copy.deepcopy(c);words,_=v.compile_case(c);self.assertEqual(c,before);self.assertEqual(len(words),86016);self.assertEqual(words[0],ABI)
if __name__=='__main__':unittest.main()
