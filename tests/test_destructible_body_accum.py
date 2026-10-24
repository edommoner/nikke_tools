"""Static quantity admission and actual native shield/body accumulation order."""
import array,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('accum_shield_tests',ROOT/'research/verify-destructible-body-accum-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class BodyAccumTests(unittest.TestCase):
    def test_all_original_definitions_static_without_native_hit_input(self):
        from calculator import timeline
        original=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text())
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU event input')):rows,raw=a.prepare()
        self.assertEqual((len(rows),sum(d is not None for _,_,d in rows)),(18,14));self.assertEqual(len(raw),4+18*110112*4)
        for _,w,(c,m,p,_) in rows[:14]:
            self.assertEqual(w[110080:110088],[0x48534936,0,0,1,1,1,1,1]);self.assertEqual(len(m['effects']),len(p['effects']))
            for owner in c['body']['squad']:
                own=[r['effect'] for r in p['effects'] if r['owner']==owner and r['effect'].get('source') in ('스킬1','스킬2','스킬3')]
                self.assertEqual(own,[r for r in original[owner] if not r.get('favorite',0)])
    def test_native_pools_and_quantity_packets(self):
        # Full 14-case native parity belongs to the package/run gate. Exercise
        # both short authored integer boundaries here without duplicating it.
        for c in [c for c in a.fixtures() if c['contract']['duration']==3 and c['contract']['mode']=='hit' and c.get('declared_effects')]:
            n=a.native_reference((c,));self.assertTrue(n['typed']['finished']);self.assertIn('final',n['damage_accumulation'])
            for packet in n['packet_samples']:
                if packet.get('quantity_only'):self.assertEqual(packet['coefficient'],0.)
    def test_original_dorothy_piercing_remains_explicitly_unsupported(self):
        c=a.fixtures()[0];names=list(c['body']['squad']);names[3]='도로시'
        body=a.roster.body_for(names,3);body['enemy']=copy.deepcopy(c['body']['enemy'])
        p=a.roster.engine_worker.evaluate(dict(body,_portable_static_inputs=True))
        self.assertTrue(any(x['effect'].get('stat')=='pierce_enabled' for x in p['effects']))
        with self.assertRaisesRegex(ValueError,'piercing policy'):
            a.compile_weapon_shield_roster(p,c['typed_bindings'],skill_shields=True,body_lifesteal=True,body_accumulation=True)
    def test_policy_is_explicit_and_old_lifesteal_header_remains_closed(self):
        c=a.fixtures()[0];p=a.roster.engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True));before=copy.deepcopy(p)
        with self.assertRaises(ValueError):a.compile_weapon_shield_roster(p,c['typed_bindings'],skill_shields=True,body_lifesteal=True)
        for value in (1,None,'yes'):
            with self.assertRaises(ValueError):a.compile_weapon_shield_roster(p,c['typed_bindings'],skill_shields=True,body_lifesteal=True,body_accumulation=value)
        self.assertEqual(p,before)
    def test_reserved_notice_storage_is_bounded_and_not_frame_or_weapon_memory(self):
        self.assertGreaterEqual(960000,940000+32*544);self.assertLessEqual(960000+128*16,970000)
        text=(ROOT/'gpu/destructible_accum_landing.slang').read_text()
        for forbidden in ('damageValue(', 'damageFromFactors(', 'daTake(', 'daEmission(', 'sampleDamageFactorsForReach('):self.assertNotIn(forbidden,text)
    def test_exact_source_inverse_rejects_unreviewed_changes(self):
        from portable_destructible_accum_source_contract import project_sources
        f=json.loads((ROOT/'tests/fixtures/portable-destructible-accum-source-delta.json').read_text());project_sources(ROOT)
        for name,row in f['sources'].items():
            with self.assertRaisesRegex(AssertionError,'Unreviewed'):project_sources(ROOT,{name:row['current']+'\n'})
    def test_saved_quantity_credit_and_pool_corruptions_are_detected(self):
        from portable_backend import source_hashes
        from portable_specs import LIMITS as L
        from portable_damage_accum_observation import compare_final
        f=json.loads((ROOT/'tests/fixtures/portable-destructible-body-accum-raw.json').read_text());rows,_=a.prepare()
        from portable_attack_group_source_contract import retained_source_hashes
        self.assertEqual(retained_source_hashes(ROOT,'gpu/destructible_roster_accum_entry.slang'),f['source_sha256']);checked=0
        for r in f['records']:
            name,w,domain=rows[r['index']];self.assertEqual(name,r['name']);self.assertEqual(hashlib.sha256(array.array('I',w).tobytes()).hexdigest(),r['input_sha256'])
            block=array.array('I',[0])*f['output_words']
            for at,value in r['nonzero']:block[at]=value
            self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),r['output_sha256'])
            n=a.native_reference(domain)
            def compare(b):
                a.shared_compare(b,domain,copy.deepcopy(n));compare_final(b,domain[1],n['damage_accumulation'])
            compare(block);faults=[(0,1),(L['HEALTH_QUERY_BASE']+11,0x40000000)]
            for i in range(block[786433]):
                at=790000+i*1040
                if block[at+12]==3:
                    faults.extend([(at+9,0x40000000),(at+12,1),(at+20,1),(at+23,0x40000000)]);break
            for i in range(L['PROTECTION_OBJECTS']):
                at=L['PROTECTION_OBJECT_BASE']+i*L['PROTECTION_OBJECT_WORDS']
                if block[at+22]&255 in (13,14,16):faults.append((at+1,0x40000000));break
            for offset,mask in faults:
                bad=array.array('I',block);bad[offset]^=mask
                with self.subTest(name=name,offset=offset),self.assertRaises(AssertionError):compare(bad)
                checked+=1
        self.assertGreaterEqual(checked,20)
if __name__=='__main__':unittest.main()
