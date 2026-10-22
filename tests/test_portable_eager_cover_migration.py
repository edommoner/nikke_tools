"""Old bytes remain independently anchored; only four recorded lazy bits may change."""
import hashlib,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_eager_cover_migration import historical_words,wire
from portable_specs import LIMITS as L


class EagerCoverMigrationTests(unittest.TestCase):
    def test_all30_inputs_reconstruct_the_existing_golden_exactly(self):
        s=importlib.util.spec_from_file_location('cover_migration_test',ROOT/'research/verify-world-ally-random-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        entries,current=m.prepare();gold=json.loads((ROOT/'research/portable-world-ally-random-short-expected.json').read_text())
        old=len(entries).to_bytes(4,'little');changed=0
        for (name,words,domain),expected in zip(entries,gold['entries'],strict=True):
            restored=historical_words(ROOT,'ally-random-gpu/'+name,words)
            self.assertEqual(hashlib.sha256(wire(restored)).hexdigest(),expected['input_sha256'])
            changed+=restored!=list(words);old+=wire(restored)
        self.assertEqual(changed,4);self.assertEqual(hashlib.sha256(old).hexdigest(),gold['input_sha256'])

    def test_unrelated_input_changes_and_legacy_flags_are_rejected(self):
        data=json.loads((ROOT/'tests/fixtures/portable-eager-cover-input-migration.json').read_text())
        s=importlib.util.spec_from_file_location('cover_migration_bad',ROOT/'research/verify-world-ally-random-short.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        for name,words,domain in m.prepare()[0]:
            key='ally-random-gpu/'+name
            if key not in data['changed_cases']:continue
            at=data['changed_cases'][key]['changes'][0]['word']
            for target in (at,3,L['HEALTH_BASE'],L['DEFINITION_BASE']):
                bad=list(words);bad[target]^=1
                with self.subTest(name=name,target=target),self.assertRaises(AssertionError):historical_words(ROOT,key,bad)


if __name__=='__main__':unittest.main()
