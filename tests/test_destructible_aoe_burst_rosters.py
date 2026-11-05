"""Full original AoE/ally modifier rosters without CPU event input to the GPU."""
import array,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('aoe_roster_tests',ROOT/'research/verify-destructible-aoe-burst-rosters-short.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)


from historical_engine_reference import historical_reference

class AoEBurstRosterTests(unittest.TestCase):

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

    @historical_reference
    def test_saved_trina_hp_and_hit_outputs_detect_factor_flag_and_receipt_corruption(self):
        from portable_backend import source_hashes
        fixture = json.loads((ROOT / 'tests/fixtures/portable-destructible-aoe-burst-rosters-raw.json').read_text())
        (rows, _) = adapter.prepare()
        checked = 0
        for record in fixture['records']:
            (name, words, domain) = rows[record['index']]
            self.assertEqual(name, record['name'])
            self.assertEqual(hashlib.sha256(array.array('I', words).tobytes()).hexdigest(), record['input_sha256'])
            block = array.array('I', [0]) * fixture['output_words']
            for (at, value) in record['nonzero']:
                block[at] = value
            self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(), record['output_sha256'])
            native = adapter.native_reference(domain)
            before = copy.deepcopy(native)
            adapter.shared_compare(block, domain, copy.deepcopy(native))
            packet = 790000 + record['aoe_packet'] * 1040
            self.assertEqual(block[packet + 14], 4097)
            for offset in (0, adapter.L['HEALTH_QUERY_BASE'], packet + 8, packet + 11, packet + 13, packet + 14, packet + 15, packet + 16):
                bad = array.array('I', block)
                bad[offset] ^= 1
                with self.subTest(name=name, offset=offset), self.assertRaises(AssertionError):
                    adapter.shared_compare(bad, domain, copy.deepcopy(native))
                checked += 1
            self.assertEqual(native, before)
        self.assertEqual(checked, 16)


if __name__=='__main__':unittest.main()
