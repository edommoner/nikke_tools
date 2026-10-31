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
        boss_name='tests/fixtures/portable-product-boss-debuff-source-delta.json'
        boss=json.loads((ROOT/boss_name).read_bytes())
        names={'gpu/attack_group_runtime.slang','gpu/counter_landing_runtime.slang',*ledger['files'],*ledger['added_sources'],*product['files'],*product['added_sources'],*boss['files'],boss_name,'tests/fixtures/portable-weighted-incoming-source-delta.json','tests/fixtures/portable-product-source-delta.json'}
        for name in names:
            target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
        return ledger

    def test_exact_later_product_inverse_keeps_original_ledger_and_old_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);ledger=self.copy_sources(root)
            current=project_sources(root)
            product=json.loads((root/'tests/fixtures/portable-product-source-delta.json').read_text())
            for name,text in product_sources(root).items():
                path=root/name;path.write_bytes(text.encode('utf-8'))
                self.assertEqual(path.read_bytes(),text.encode('utf-8'))
                self.assertEqual(hashlib.sha256(path.read_text().encode()).hexdigest(),product['files'][name]['baseline_sha256'] if name in product['files'] else product['added_sources'][name])
            self.assertEqual(project_sources(root),current)

    def test_changed_product_route_guard_and_arithmetic_are_rejected(self):
        cases=[('gpu/destructible_weapon_runtime.slang','commands[actorBinding(s,slot)]!=1','commands[actorBinding(s,slot)]!=5'),
               ('gpu/attack_group_runtime.slang','commands[input+1]==2&&commands[actorBinding(s,slot)]==1','commands[actorBinding(s,slot)]==1'),
               ('app/portable_backend.py',"source.replace('gpu/product_fixed_','gpu/product_',1)","source.replace('gpu/product_fixed_','gpu/product_group_',1)"),
               ('gpu/event_runtime.slang','uint64_t fixedGaugeReadyAt;','uint fixedGaugeReadyAt;'),
               ('gpu/world_actor_fields.slang','#ifdef PORTABLE_PRODUCT_OUTLINED_HELPERS','#if 1'),
               ('gpu/combat_runtime.slang','s.fixedGaugeReadyAt = f64Add(when,','s.fixedGaugeReadyAt = f64Sub(when,'),
               ('gpu/world_charge_control_runtime.slang','|| defined(PORTABLE_PRODUCT_OUTLINED_HELPERS)','|| defined(PORTABLE_WORLD_FRAME)'),
               ('gpu/event_runtime.slang','(PARTIAL_IS_FULL(w)?H_CHARGE:0U)','H_CHARGE'),
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

    def test_product_part_boundary_inverse_accepts_only_exact_current_and_preimage(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.copy_sources(root)
            current=project_sources(root);name='gpu/counter_landing_runtime.slang'
            original=current[name].encode('utf-8');path=root/name
            self.assertEqual(hashlib.sha256(original).hexdigest(),'d84aeea5965ffd318c409f38b5a1562293ac445ad11d3ee113f539726ba733e5')
            self.assertNotEqual(path.read_bytes(),original)
            path.write_bytes(original)
            self.assertEqual(project_sources(root),current)
            for mutation in (original+b'\n', (ROOT/name).read_bytes().replace(b'[noinline]',b'[ForceInline]',1),
                             (ROOT/name).read_bytes().replace(b'uint shot=s.resourceOutput+',b'uint shot=1+s.resourceOutput+',1)):
                path.write_bytes(mutation)
                with self.assertRaisesRegex(ValueError,'Unreviewed product source'):project_sources(root)
    def test_unreviewed_current_dependency_cannot_be_projected(self):
        with tempfile.TemporaryDirectory() as folder:
            r=Path(folder);self.copy_sources(r);project_sources(r)
            target=r/'gpu/weighted_incoming_runtime.slang';target.write_text(target.read_text()+'\n// unreviewed mutation\n')
            with self.assertRaisesRegex(ValueError,'Unreviewed weighted dependency'):project_sources(r)

    def test_boss_history_recovers_exact_preimages_and_rejects_unreviewed_bytes(self):
        from portable_weighted_incoming_source_contract import boss_source_preimages
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.copy_sources(root)
            before=project_sources(root);old=boss_source_preimages(root)
            for name,text in old.items():(root/name).write_bytes(text.encode('utf-8'))
            self.assertEqual(project_sources(root),before)
            path=root/'gpu/world_frame_addresses.slang';path.write_bytes(path.read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError,'Unreviewed product source'):project_sources(root)
            path.write_bytes(old['gpu/world_frame_addresses.slang'].encode('utf-8'))
            ledger=root/'tests/fixtures/portable-product-boss-debuff-source-delta.json';ledger.write_bytes(ledger.read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError,'history ledger changed'):project_sources(root)

    def test_product_history_and_added_helper_cannot_be_edited(self):
        for name,message in [('tests/fixtures/portable-product-source-delta.json','history ledger changed'),
                             ('gpu/admission_definition_types.slang','Unreviewed product source'),
                             ('gpu/product_group_target_battle_entry.slang','Unreviewed product dependency')]:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);self.copy_sources(root);target=root/name
                target.write_bytes(target.read_bytes()+b'\n')
                with self.assertRaisesRegex(ValueError,message):project_sources(root)

if __name__=='__main__':unittest.main()
