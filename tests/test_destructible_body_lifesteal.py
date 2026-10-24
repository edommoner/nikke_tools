"""Original lifesteal profiles and strict opt-in/body-only boundaries."""
import array,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('lifesteal_shield_tests',ROOT/'research/verify-destructible-body-lifesteal-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class BodyLifestealTests(unittest.TestCase):
    def test_all_definitions_pack_without_native_events(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU events')):rows,data=a.prepare()
        self.assertEqual((len(rows),sum(d is not None for _,_,d in rows)),(13,10));self.assertEqual(len(data),4+13*110112*4)
        original=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text())
        for _,words,domain in rows[:10]:
            c,m,p,_=domain;self.assertEqual(len(m['effects']),len(p['effects']));self.assertEqual(words[110080:110087],[0x48534935,0,0,1,1,1,1])
            for owner in c['body']['squad']:
                actual=[r['effect'] for r in p['effects'] if r['owner']==owner and r['effect'].get('source') in ('스킬1','스킬2','스킬3')]
                self.assertEqual(actual,[r for r in original[owner] if not r.get('favorite',0)])
    def test_native_body_heals_and_shield_exclusion_all_cases(self):
        for c in a.fixtures():
            before=copy.deepcopy(c);n,_=a.observe(c);self.assertTrue(a.verify(c,n)['body_only_lifesteal']);self.assertEqual(c,before)
    def test_old_policy_and_accumulation_remain_rejected(self):
        c=a.fixtures()[0];p=a.roster.engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True));before=copy.deepcopy(p)
        with self.assertRaisesRegex(ValueError,'post-landing'):a.compile_weapon_shield_roster(p,c['typed_bindings'],skill_shields=True)
        for flag in (1,None,'yes'):
            with self.assertRaises(ValueError):a.compile_weapon_shield_roster(p,c['typed_bindings'],skill_shields=True,body_lifesteal=flag)
        from destructible_battle_runtime import typed_battle
        with self.assertRaises(ValueError):
            with typed_battle(c['typed_bindings'],body_lifesteal=True):pass
        bad=copy.deepcopy(p);next(r for r in bad['effects'] if r['effect'].get('stat')=='lifesteal_pct')['effect']['stat']='dmg_accum_dealt_atk_pct'
        with self.assertRaisesRegex(ValueError,'post-landing'):a.compile_weapon_shield_roster(bad,c['typed_bindings'],skill_shields=True,body_lifesteal=True)
        self.assertEqual(p,before)
    def test_historical_source_inverse_rejects_unreviewed_changes(self):
        from portable_destructible_lifesteal_source_contract import project_sources
        f=json.loads((ROOT/'tests/fixtures/portable-destructible-lifesteal-source-delta.json').read_text());self.assertEqual(len(f['sources']),3);project_sources(ROOT)
        for name,row in f['sources'].items():
            with self.assertRaisesRegex(AssertionError,'Unreviewed'):project_sources(ROOT,{name:row['current']+'\n'})
    def test_native_observer_restores_profile_and_scopes_after_failure(self):
        from calculator import timeline,buff_manager
        import destructible_damage_policy
        before=(sys.getprofile(),timeline.simulate,timeline.calc_damage,timeline.HitEvent,timeline.CharState._fire,buff_manager.BuffManager.register_damage_handler)
        with patch.object(destructible_damage_policy,'calculate',side_effect=RuntimeError('lifesteal observer failure')):
            with self.assertRaisesRegex(RuntimeError,'lifesteal observer failure'):a.observe(a.fixtures()[0])
        self.assertEqual(before,(sys.getprofile(),timeline.simulate,timeline.calc_damage,timeline.HitEvent,timeline.CharState._fire,buff_manager.BuffManager.register_damage_handler))
    def test_saved_hp_healing_and_body_trace_corruptions_are_detected(self):
        from portable_backend import source_hashes
        from portable_specs import LIMITS as L
        fixture=json.loads((ROOT/'tests/fixtures/portable-destructible-body-lifesteal-raw.json').read_text());rows,_=a.prepare()
        self.assertEqual(source_hashes(ROOT/'gpu/destructible_roster_lifesteal_entry.slang'),fixture['source_sha256']);checked=0
        for record in fixture['records']:
            name,words,domain=rows[record['index']];self.assertEqual(name,record['name']);self.assertEqual(hashlib.sha256(array.array('I',words).tobytes()).hexdigest(),record['input_sha256'])
            block=array.array('I',[0])*fixture['output_words']
            for at,value in record['nonzero']:block[at]=value
            self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),record['output_sha256'])
            native=a.native_reference(domain);a.shared_compare(block,domain,copy.deepcopy(native))
            for offset,mask in ((0,1),(L['HEALTH_QUERY_BASE']+1,0x40000000),(L['HEALTH_QUERY_BASE']+11,0x40000000),(L['HEALTH_QUERY_BASE']+9,0x40000000)):
                bad=array.array('I',block);bad[offset]^=mask
                with self.subTest(name=name,offset=offset),self.assertRaises(AssertionError):a.shared_compare(bad,domain,copy.deepcopy(native))
                checked+=1
        self.assertEqual(checked,12)

if __name__=='__main__':unittest.main()
