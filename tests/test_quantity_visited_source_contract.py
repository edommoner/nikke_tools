"""Historical projection cannot hide arithmetic changes or missing dependencies."""
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from portable_quantity_visited_source_contract import historical_hashes,SOURCE,HELPER,BEFORE_SHA256
LEDGER='tests/fixtures/quantity-visited-source-change-v1.json'

class QuantityVisitedSourceContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        for name in (SOURCE,HELPER,LEDGER):
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,path)
        self.hashes={n:hashlib.sha256((self.root/n).read_bytes()).hexdigest() for n in (SOURCE,HELPER)}
        self.hashes['gpu/unrelated.slang']='f'*64

    def test_exact_inverse_preserves_other_sources_and_does_not_mutate_input(self):
        original=dict(self.hashes);result=historical_hashes(self.root,self.hashes)
        self.assertEqual(result,{SOURCE:BEFORE_SHA256,'gpu/unrelated.slang':'f'*64})
        self.assertEqual(self.hashes,original)
        self.assertEqual(historical_hashes(self.root,result),result)

    def test_changed_raw_source_or_helper_is_rejected(self):
        for name in (SOURCE,HELPER):
            path=self.root/name;raw=path.read_bytes();path.write_bytes(raw+b'\n')
            with self.subTest(name=name),self.assertRaises(ValueError):historical_hashes(self.root,self.hashes)
            path.write_bytes(raw)

    def test_incorrect_hashes_and_missing_helper_are_rejected(self):
        for name in (SOURCE,HELPER):
            wrong=dict(self.hashes);wrong[name]='0'*64
            with self.subTest(name=name),self.assertRaises(ValueError):historical_hashes(self.root,wrong)
        absent=dict(self.hashes);del absent[HELPER]
        with self.assertRaises(ValueError):historical_hashes(self.root,absent)

    def test_unknown_contract_normalizer_and_baseline_cannot_be_added(self):
        path=self.root/LEDGER;raw=path.read_bytes()
        for fault in ('schema','normalizer','baseline','extra-helper','empty-hunk'):
            data=json.loads(raw)
            if fault=='schema':data['schema']='unknown'
            elif fault=='normalizer':data['normalizer_changed']=True
            elif fault=='baseline':data['files'][SOURCE]['before_sha256']='0'*64
            elif fault=='extra-helper':data['added_sources']['gpu/other.slang']='0'*64
            else:data['files'][SOURCE]['hunks'][0]['after']=''
            path.write_bytes(json.dumps(data).encode())
            with self.subTest(fault=fault),self.assertRaises(ValueError):historical_hashes(self.root,self.hashes)
        path.write_bytes(raw)

    def test_updated_current_hash_cannot_hide_changed_arithmetic(self):
        path=self.root/SOURCE;raw=path.read_bytes();needle=b'result.percent = f64Add(result.percent,value)'
        self.assertEqual(raw.count(needle),1)
        path.write_bytes(raw.replace(needle,b'result.percent = value',1))
        sha=hashlib.sha256(path.read_bytes()).hexdigest();self.hashes[SOURCE]=sha
        ledger=self.root/LEDGER;data=json.loads(ledger.read_bytes());data['files'][SOURCE]['after_sha256']=sha
        ledger.write_bytes(json.dumps(data).encode())
        with self.assertRaisesRegex(ValueError,'inverse differs'):historical_hashes(self.root,self.hashes)

if __name__=='__main__':unittest.main()
