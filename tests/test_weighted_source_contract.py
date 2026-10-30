"""Strict source history survives; current weighted source requires a new seal."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_weighted_incoming_source_contract import project_sources,historical_hashes,product_sources
from portable_slang_generation import source_hashes
class WeightedSourceContract(unittest.TestCase):
    def copy_sources(self, root):
        ledger=json.loads((ROOT/'tests/fixtures/portable-weighted-incoming-source-delta.json').read_text())
        product=json.loads((ROOT/'tests/fixtures/portable-product-source-delta.json').read_text())
        names={*ledger['files'],*ledger['added_sources'],*product['files'],*product['added_sources'],'tests/fixtures/portable-weighted-incoming-source-delta.json','tests/fixtures/portable-product-source-delta.json'}
        for name in names:
            target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
        return ledger

    def test_exact_later_product_inverse_keeps_original_ledger_and_old_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);ledger=self.copy_sources(root)
            current=project_sources(root)
            product=json.loads((root/'tests/fixtures/portable-product-source-delta.json').read_text())
            for name,text in product_sources(root).items():
                path=root/name;path.write_text(text)
                self.assertEqual(hashlib.sha256(path.read_text().encode()).hexdigest(),product['files'][name]['baseline_sha256'])
            self.assertEqual(project_sources(root),current)

    def test_changed_product_route_guard_and_arithmetic_are_rejected(self):
        cases=[('app/portable_backend.py',"source.replace('gpu/product_fixed_','gpu/product_',1)","source.replace('gpu/product_fixed_','gpu/product_group_',1)"),
               ('gpu/event_runtime.slang','uint64_t fixedGaugeReadyAt;','uint fixedGaugeReadyAt;'),
               ('gpu/world_actor_fields.slang','#ifdef PORTABLE_PRODUCT_OUTLINED_HELPERS','#if 1'),
               ('gpu/combat_runtime.slang','s.fixedGaugeReadyAt = f64Add(when,','s.fixedGaugeReadyAt = f64Sub(when,'),
               ('gpu/world_charge_control_runtime.slang','|| defined(PORTABLE_PRODUCT_OUTLINED_HELPERS)','|| defined(PORTABLE_WORLD_FRAME)'),
               ('gpu/event_runtime.slang','uint count, error, timerClock','uint count, changedError, timerClock')]
        for name,before,after in cases:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);self.copy_sources(root);path=root/name;text=path.read_text();self.assertIn(before,text);path.write_text(text.replace(before,after,1))
                with self.assertRaisesRegex(ValueError,'Unreviewed product source'):project_sources(root)

    def test_exact_preimage_and_closure_match_historical_cover_seal(self):
        before=project_sources(ROOT);golden=json.loads((ROOT/'research/portable-cover-defense-modifiers-v1-expected.json').read_text())
        self.assertEqual(historical_hashes(ROOT,'gpu/world_cover_defense_entry.slang'),golden['source_sha256'])
        self.assertNotEqual(source_hashes(ROOT,'gpu/world_cover_defense_entry.slang'),golden['source_sha256'])
        self.assertNotEqual(before['gpu/dispatch_phases.slang'],(ROOT/'gpu/dispatch_phases.slang').read_text())
    def test_unreviewed_current_dependency_cannot_be_projected(self):
        with tempfile.TemporaryDirectory() as folder:
            r=Path(folder);self.copy_sources(r);project_sources(r)
            target=r/'gpu/weighted_incoming_runtime.slang';target.write_text(target.read_text()+'\n// unreviewed mutation\n')
            with self.assertRaisesRegex(ValueError,'Unreviewed weighted dependency'):project_sources(r)

    def test_product_history_and_added_helper_cannot_be_edited(self):
        for name,message in [('tests/fixtures/portable-product-source-delta.json','history ledger changed'),
                             ('gpu/admission_definition_types.slang','Unreviewed product dependency')]:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);self.copy_sources(root);target=root/name
                target.write_bytes(target.read_bytes()+b'\n')
                with self.assertRaisesRegex(ValueError,message):project_sources(root)

if __name__=='__main__':unittest.main()
