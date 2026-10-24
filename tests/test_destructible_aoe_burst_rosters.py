"""Full original AoE/ally modifier rosters without CPU event input to the GPU."""
import array,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('aoe_roster_tests',ROOT/'research/verify-destructible-aoe-burst-rosters-short.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)


class AoEBurstRosterTests(unittest.TestCase):
    def test_all_original_definitions_survive_static_input_without_simulation(self):
        from calculator import timeline
        originals=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text())
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU event input')):
            rows,raw=adapter.prepare()
        self.assertEqual((len(rows),sum(d is not None for _,_,d in rows)),(18,16));self.assertEqual(len(raw),4+18*110112*4)
        from portable_readiness_semantics import reference_readiness
        readiness=reference_readiness(dict(phase='effect',category='effect',kind='buff',stat='shield_dmg_pct',target='all_allies'))
        proof=readiness['typed_aoe_burst_shield_validation'];self.assertTrue(proof['aoe_burst_positive_case_verified'])
        self.assertEqual((proof['inputs'],proof['native_cases'],proof['aoe_specific_modifier']),(18,16,435.6))
        self.assertFalse(readiness['gpu_supported']);self.assertFalse(readiness['gpu_admission_verified']);self.assertFalse(proof['cuda_device_verified'])
        for _,words,domain in rows[:16]:
            case,meta,prepared,_=domain
            for owner in case['body']['squad']:
                actual=[r['effect'] for r in prepared['effects'] if r['owner']==owner and r['effect'].get('source') in ('스킬1','스킬2','스킬3')]
                # The authored base profile has favorite_stage=0. Miranda's
                # favorite-only replacement definitions are a different profile.
                self.assertEqual(actual,[r for r in originals[owner] if not r.get('favorite',0)])
            self.assertEqual(len(meta['effects']),case['contract']['prepared_definitions'])

    def test_all_native_aoe_hp_credit_slot_order_and_body_fallback_contracts(self):
        positive=0
        for case in adapter.fixtures():
            with self.subTest(case=case['name']):
                before=copy.deepcopy(case);native,_=adapter.observe(case);result=adapter.verify(case,native)
                self.assertEqual(case,before);positive+=result['positive_aoe_burst'];self.assertFalse(result['gpu_connected']);self.assertFalse(result['full_character_verified'])
        self.assertEqual(positive,12)

    def test_invalid_aoe_family_bits_are_distinct_minimal_mutations(self):
        rows,_=adapter.prepare();base=rows[0][1]
        for _,words,domain in rows[16:]:
            self.assertIsNone(domain);delta=[i for i,(a,b) in enumerate(zip(base,words,strict=True)) if a!=b]
            self.assertEqual(len(delta),1)
            for value in (0,1):
                block=[0]*16;block[0]=value
                with self.assertRaises(AssertionError):adapter.validate_rejection(block,'reject/destructible-aoe-burst/test')
        adapter.validate_rejection([64],'reject/destructible-aoe-burst/test')

    def test_saved_trina_hp_and_hit_outputs_detect_factor_flag_and_receipt_corruption(self):
        from portable_backend import source_hashes
        fixture=json.loads((ROOT/'tests/fixtures/portable-destructible-aoe-burst-rosters-raw.json').read_text());rows,_=adapter.prepare()
        from portable_destructible_lifesteal_source_contract import verify_retained_sources
        verify_retained_sources(ROOT,'gpu/destructible_roster_skill_entry.slang',fixture['source_sha256'])
        checked=0
        for record in fixture['records']:
            name,words,domain=rows[record['index']];self.assertEqual(name,record['name'])
            self.assertEqual(hashlib.sha256(array.array('I',words).tobytes()).hexdigest(),record['input_sha256'])
            block=array.array('I',[0])*fixture['output_words']
            for at,value in record['nonzero']:block[at]=value
            self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),record['output_sha256'])
            # Mutations change only saved GPU output, never its CPU input.
            # Calculate this independent oracle once, then check every altered
            # block against a fresh copy. Retain all cases and fault probes.
            native=adapter.native_reference(domain);before=copy.deepcopy(native)
            adapter.shared_compare(block,domain,copy.deepcopy(native))
            packet=790000+record['aoe_packet']*1040
            self.assertEqual(block[packet+14],4097)
            for offset in (0,adapter.L['HEALTH_QUERY_BASE'],packet+8,packet+11,packet+13,packet+14,packet+15,packet+16):
                bad=array.array('I',block);bad[offset]^=1
                with self.subTest(name=name,offset=offset),self.assertRaises(AssertionError):adapter.shared_compare(bad,domain,copy.deepcopy(native))
                checked+=1
            self.assertEqual(native,before)
        self.assertEqual(checked,16)


if __name__=='__main__':unittest.main()
