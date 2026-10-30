"""Strict source history survives; current weighted source requires a new seal."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_weighted_incoming_source_contract import project_sources,historical_hashes
from portable_slang_generation import source_hashes
class WeightedSourceContract(unittest.TestCase):
    def test_exact_preimage_and_closure_match_historical_cover_seal(self):
        before=project_sources(ROOT);golden=json.loads((ROOT/'research/portable-cover-defense-modifiers-v1-expected.json').read_text())
        self.assertEqual(historical_hashes(ROOT,'gpu/world_cover_defense_entry.slang'),golden['source_sha256'])
        self.assertNotEqual(source_hashes(ROOT,'gpu/world_cover_defense_entry.slang'),golden['source_sha256'])
        self.assertNotEqual(before['gpu/dispatch_phases.slang'],(ROOT/'gpu/dispatch_phases.slang').read_text())
    def test_unreviewed_current_dependency_cannot_be_projected(self):
        ledger=json.loads((ROOT/'tests/fixtures/portable-weighted-incoming-source-delta.json').read_text())
        with tempfile.TemporaryDirectory() as folder:
            r=Path(folder)
            for name in [*ledger['files'],*ledger['added_sources'],'tests/fixtures/portable-weighted-incoming-source-delta.json']:
                target=r/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
            project_sources(r)
            target=r/'gpu/weighted_incoming_runtime.slang';target.write_text(target.read_text()+'\n// unreviewed mutation\n')
            with self.assertRaisesRegex(ValueError,'Unreviewed weighted dependency'):project_sources(r)
if __name__=='__main__':unittest.main()
