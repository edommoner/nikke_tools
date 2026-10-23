"""Private wire contracts, projection boundaries and GPU result reader faults."""
import copy,importlib.util,json,hashlib,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_damage_accum_specs import compiler_effect,validate,policy
from portable_damage_accum_cases import fixtures
from portable_specs import LIMITS as L,FIELDS as F
from portable_damage_accum_source_contract import project_sources

def adapter():
    s=importlib.util.spec_from_file_location('damage_battle_test',ROOT/'research/verify-world-damage-accum-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class DamageBattleTests(unittest.TestCase):
    def test_original_duplicate_pool_names_survive_static_lowering(self):
        cases=fixtures();c=next(c for c in cases if c['contract']['kind']=='duplicate-name-first-active');before=copy.deepcopy(c)
        m=adapter();words,metadata,_=m.suite.compile_case(c)
        self.assertEqual(c,before)
        for row in (1,2):
            at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS'];self.assertEqual(words[at+F['NAME']],metadata['states']['pool']);self.assertEqual(words[at+F['STAT']],80+row)
            projected=compiler_effect(c['effects'][row]);self.assertEqual({k:v for k,v in projected.items() if k!='stat'},{k:v for k,v in c['effects'][row].items() if k!='stat'})
    def test_absent_zero_empty_and_named_rate_are_distinct_policies(self):
        rows=fixtures()
        def get(kind):return next(e for c in rows if c['contract']['kind']==kind for e in c['effects'] if e.get('stat')=='dmg_accum_rate_pct')
        self.assertEqual(policy(get('absent-base')),15);self.assertEqual(policy(get('explicit-zero-base')),527);self.assertEqual(policy(get('empty-values-is-zero')),527)
        e=dict(get('absent-base'),target_effect='pool');self.assertEqual(policy(e),271)
    def test_unconnected_scaling_tick_and_bullet_lifetime_fail_closed(self):
        c=fixtures()[0];e=c['effects'][1]
        for extra in (dict(scaling='stack_count'),dict(tick_interval=.1),dict(tick_start=.1),dict(duration_bullets=1)):
            with self.subTest(extra=extra),self.assertRaises(ValueError):validate(dict(e,**extra),combat=c['combat'],world_frame=True)
    def test_every_original_battle_packs_without_cpu_runtime_values(self):
        m=adapter();rows,payload=m.prepare();self.assertEqual(len(rows),62);self.assertEqual(sum(d is not None for _,_,d in rows),52)
        for _,words,d in rows[:52]:self.assertEqual(words[L['PROTECTION_META_BASE']]&129,129)
    def test_header_and_notice_scratch_preserve_all_prior_owners(self):
        from portable_damage_accum_specs import audit_layout
        result=audit_layout(L);self.assertTrue(result['verified']);self.assertEqual(len(result['modes']),5)
        source=(ROOT/'gpu/damage_accum_battle_runtime.slang').read_text()
        self.assertIn('DA_BATTLE_HEADER=260666,DA_BATTLE_QUEUE=260668,DA_BATTLE_QUEUE_COUNT=512',source)
    def test_exact_inverse_refuses_source_mutation(self):
        data=json.loads((ROOT/'tests/fixtures/portable-damage-accum-source-delta.json').read_text());projected=project_sources(ROOT)
        for name,row in data['sources'].items():
            self.assertEqual(hashlib.sha256(projected[name].encode()).hexdigest(),row['baseline_sha256'])
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:row['current']+'\n'})
        for name in data['added_sources']:
            with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})
if __name__=='__main__':unittest.main()
