"""Data-only packet repair never edits frozen calculation/controller bytes."""
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','scripts')]
import nikke_gpu as cli
from portable_test_golden_supplement import supplement


class GoldenSupplement(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'source';self.donor=self.root/'donor';self.capture=self.root/'units'
        for p in (self.source,self.donor,self.capture):p.mkdir()
        self.name='research/portable-retained-expected.json'
        def record(root,name,raw):
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            return dict(path=name,bytes=len(raw),sha256=cli.sha(raw))
        self.original=b'calculation and controller remain frozen\n'
        source_row=record(self.source,'app/frozen.py',self.original)
        golden=dict(entries=[dict(name='old')],source_sha256={'gpu/old.slang':'a'*64})
        self.golden_raw=json.dumps(golden).encode();donor_row=record(self.donor,self.name,self.golden_raw)
        self.m=dict(schema=1,suite='candidate',purpose='development',selected_cases=[],files=[source_row],golden=dict(entries=[dict(native_sha256='b'*64)]))
        self.d=dict(schema=1,suite='donor',purpose='sealed',files=[donor_row])
        for root,m in ((self.source,self.m),(self.donor,self.d)):
            m['package_id']=cli.package_id(m);(root/'gpu-package.json').write_text(json.dumps(m))
        (self.capture/'result.json').write_text(json.dumps(dict(schema='unit-check-v1',package_id=self.m['package_id'],passed=False,gpu_calls=0)))
        cli.collect(self.capture,self.capture/'artifacts.json')
        def verify(root):
            m=cli.load(root/'gpu-package.json');cli.check_records(root,m['files']);return m
        self.api=SimpleNamespace(verify_saved_package=verify,load=cli.load,check_records=cli.check_records,safe_name=cli.safe_name,sha=cli.sha,package_id=cli.package_id,write=cli.write)

    def run_repair(self):
        with patch('portable_test_golden_supplement.configured_golden',return_value=self.name):
            return supplement(self.api,self.source,self.capture,self.donor,'retained',self.root/'new.zip')

    def test_addition_is_only_sealed_json_and_preserves_expectations(self):
        result=self.run_repair()
        with zipfile.ZipFile(self.root/'new.zip') as archive:
            new=json.loads(archive.read('gpu-package.json'))
            self.assertEqual(archive.read('app/frozen.py'),self.original)
            self.assertEqual(archive.read(self.name),self.golden_raw)
        self.assertEqual(new['golden'],self.m['golden'])
        self.assertNotEqual(new['package_id'],self.m['package_id'])
        self.assertEqual(len(new['files']),len(self.m['files'])+1)
        self.assertFalse((self.source/self.name).exists())
        self.assertEqual(result['native_battle_calls'],0)
        self.assertTrue(result['fresh_native_preflight_required'])
        self.assertTrue(result['independent_seal_required'])

    def test_claimed_source_is_rejected(self):
        (self.source/'gpu-claimed-metal.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'claim'):self.run_repair()

    def test_non_json_or_unregistered_file_is_rejected(self):
        self.name='app/inject.py'
        with self.assertRaisesRegex(ValueError,'registered test golden'):self.run_repair()

    def test_source_bytes_changed_since_manifest_are_rejected(self):
        (self.source/'app/frozen.py').write_bytes(b'changed')
        with self.assertRaises(ValueError):self.run_repair()

    def test_donor_bytes_changed_since_manifest_are_rejected(self):
        (self.donor/self.name).write_bytes(b'changed')
        with self.assertRaises(ValueError):self.run_repair()

    def test_capture_cannot_be_relabelled_as_matching(self):
        (self.capture/'result.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'failed CPU unit'):self.run_repair()

    def test_existing_output_is_never_overwritten(self):
        (self.root/'new.zip').write_bytes(b'retain')
        with self.assertRaises(FileExistsError):self.run_repair()
        self.assertEqual((self.root/'new.zip').read_bytes(),b'retain')


if __name__=='__main__':unittest.main()
