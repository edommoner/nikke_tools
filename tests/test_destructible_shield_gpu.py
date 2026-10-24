"""Shared Frame provider, original positive/rejection tables and raw decoder."""
import array,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('shield_gpu_tests',ROOT/'research/verify-destructible-shield-battle-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class ShieldGPUTests(unittest.TestCase):
    def test_input_is_definitions_and_routes_without_a_cpu_attack_list(self):
        with patch.object(a.battle,'observe',side_effect=AssertionError('No oracle')),patch.object(a,'native_reference',side_effect=AssertionError('No oracle')):rows,raw=a.prepare()
        self.assertEqual((len(rows),sum(c is not None for _,_,c in rows)),(88,58));self.assertEqual(len(raw),4+88*110112*4)
        for _,words,domain in rows:
            if domain is not None:self.assertFalse(any(words[104400:104400+2320]))

    def test_old_44_and_modifier18_native_fingerprints_are_retained(self):
        rows,_=a.prepare();by_name={n:c for n,w,c in rows}
        self.assertEqual(len(by_name),88)
        self.assertEqual([r[0] for r in rows[:44]],[r[0] for r in a.battle.prepare()[0]])
        for golden in ['portable-destructible-battle-short-expected.json','portable-destructible-modifier-battle-short-expected.json']:
            expected=json.loads((ROOT/'research'/golden).read_text())
            for r in expected['entries']:
                with self.subTest(name=r['name']):
                    domain=by_name[r['name']];value=dict(status=64) if domain is None else a.native_reference(domain)
                    self.assertEqual(a.cross.digest(value),r['native_sha256'])

    def test_shield_provider_uses_shared_frame_and_strict_historical_inverse(self):
        from portable_destructible_shield_source_contract import project_sources
        data=json.loads((ROOT/'tests/fixtures/portable-destructible-shield-source-delta.json').read_text());self.assertEqual(len(data['sources']),1)
        project_sources(ROOT)
        for name,row in data['sources'].items():
            with self.assertRaisesRegex(AssertionError,'Unreviewed'):project_sources(ROOT,{name:row['current']+'\n'})
        entry=(ROOT/'gpu/destructible_shield_battle_entry.slang').read_text()
        self.assertIn('#include "destructible_frame_runtime.slang"',entry)
        self.assertIn('#include "destructible_modifier_runtime.slang"',entry)
        self.assertNotIn('advanceDestructibleSkillFrame(',entry)

    def test_actual_metal_shield_blocks_detect_owner_source_scalar_and_receipt_corruption(self):
        from portable_backend import source_hashes
        f=json.loads((ROOT/'tests/fixtures/portable-destructible-shield-battle-raw.json').read_text())
        self.assertEqual(f['source_sha256'],source_hashes('gpu/destructible_shield_battle_entry.slang'))
        rows,_=a.prepare()
        for record in f['records']:
            name,words,domain=rows[record['index']];self.assertEqual(name,record['name'])
            self.assertEqual(hashlib.sha256(array.array('I',words).tobytes()).hexdigest(),record['input_sha256'])
            block=array.array('I',[0])*f['output_words']
            for at,value in record['nonzero']:block[at]=value
            self.assertEqual(hashlib.sha256(block.tobytes()).hexdigest(),record['output_sha256'])
            if domain is None:
                a.validate_rejection(block,name);block[0]=0
                with self.assertRaises(AssertionError):a.validate_rejection(block,name)
                continue
            a.compare(block,domain)
            for at in (0,787466,789248,790001,790006,790008,790020,790022):
                changed=array.array('I',block);changed[at]^=1
                with self.subTest(name=name,offset=at),self.assertRaises(AssertionError):a.compare(changed,domain)

if __name__=='__main__':unittest.main()
