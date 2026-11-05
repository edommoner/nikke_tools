"""The reviewed port preserves exact old seals; extra edits never inherit them."""
import hashlib,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'tests')]
from portable_weighted_incoming_source_contract import reference_engine_preimages,reference_engine_source_bytes,reference_engine_reviewed_bytes
from historical_engine_reference import source_preimage
HISTORY='tests/fixtures/reference-engine-burst-source-history-v1.json'
OLD_PINS={'gpu/combat_runtime.slang':'5b697f5687aa858f1bc6b86d8181cb10e9d80f2eb44c6b6130b52b7c4c0ad857','gpu/burst_control_policy.slang':'4dbd1dbd5b0711bcb9b1a0c8fb4d90d618e7392831ebab3977c0c95d1d1725e4','gpu/coordinate_aim_runtime.slang':'0479a8a60ca9f3921d9c150eee88d199faaa4406d10668dae07680918c7dae8f','app/portable_detail.py':'13657283b9c57ec587bedb0d1993090b301ba5a56e53285157398b359d77bbce','app/portable_cpu_tests.py':'be694e96dcfdb9b2e3426a08ef6fb64d952dfa1048eaebc19a6cbfa48600c807','app/detail_effects.cu':'af2cf0b2cef045e998abf3a469ea579301a3d8daa85751baeca5d4726b7e6e24'}

class ReviewedNewCharacterHistoryTests(unittest.TestCase):
    def test_old_seal_baselines_and_scope_are_unchanged(self):
        data=json.loads((ROOT/HISTORY).read_bytes())
        self.assertFalse(data['normalizer_changed']);self.assertFalse(data['current_product_equivalence_claim'])
        self.assertEqual(data['reviewed_port']['base_commit'],'1e2b8c38834ac4b7b703b4deda47959bd8b6ede0')
        for name,digest in OLD_PINS.items():
            from portable_removed_sources import REMOVED_SOURCES
            if name in REMOVED_SOURCES:continue
            self.assertEqual(data['files'][name]['baseline_sha256'],digest)
            self.assertEqual(hashlib.sha256(data['files'][name]['baseline'].encode()).hexdigest(),digest)

    def test_every_reviewed_current_file_returns_exact_old_bytes(self):
        data=json.loads((ROOT/HISTORY).read_bytes());projected=reference_engine_preimages(ROOT)
        self.assertEqual(set(projected),set(data['files'])-__import__('portable_removed_sources').REMOVED_SOURCES)
        for name,row in data['files'].items():
            from portable_removed_sources import REMOVED_SOURCES
            if name in REMOVED_SOURCES:continue
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256(reference_engine_reviewed_bytes(name,(ROOT/name).read_bytes())).hexdigest(),row['current_sha256'])
                self.assertEqual(reference_engine_source_bytes(ROOT,name),row['baseline'].encode())
                self.assertEqual(source_preimage(ROOT,name),row['baseline'].encode())
                self.assertEqual(projected[name],row['baseline'].replace('\r\n','\n'))

    def test_extra_source_edits_and_ledger_edits_cannot_borrow_history(self):
        names=('gpu/dispatch_phases.slang','app/engine_worker.py','app/portable_runtime.py','gpu/admission_definition_triggers.slang','gpu/event_runtime.slang','gpu/portable_schema.slang','gpu/revival_runtime.slang','gpu/world_actor_stacks.slang','app/portable_coordinate_original_enemy_stack_source_contract.py')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name in (HISTORY,*names):
                from portable_removed_sources import REMOVED_SOURCES
                if name in REMOVED_SOURCES:continue
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
            for name in names:
                from portable_removed_sources import REMOVED_SOURCES
                if name in REMOVED_SOURCES:continue
                target=root/name;original=target.read_bytes()
                target.write_bytes(original+b'\n// unreviewed additional change\n')
                with self.subTest(name=name),self.assertRaisesRegex(ValueError,'Unreviewed product source'):reference_engine_source_bytes(root,name)
                self.assertNotIn(name,reference_engine_preimages(root));target.write_bytes(original)
                self.assertEqual(reference_engine_source_bytes(root,name),source_preimage(ROOT,name))
            target=root/HISTORY;target.write_bytes(target.read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError,'history changed'):reference_engine_preimages(root)

    def test_historical_compiler_child_keeps_current_engine_and_forbids_devices(self):
        code="import sys;sys.path[:0]=['tests','app'];import historical_engine_reference as h;r=h.install_compiler();import engine_worker;assert engine_worker.ENGINE.name=='nikke-calc-master';assert r.__historical_source_sha256__==h.hashlib.sha256(h.source_preimage(h.ROOT,'app/portable_runtime.py')).hexdigest();r.execute('forbidden',b'')"
        result=subprocess.run([sys.executable,'-W','ignore::ResourceWarning','-c',code],cwd=ROOT,text=True,capture_output=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Device execution forbidden in historical compiler reference',result.stderr)
        self.assertNotIn('AssertionError',result.stderr)

if __name__=='__main__':unittest.main()
