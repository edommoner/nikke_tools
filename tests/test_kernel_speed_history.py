"""Unit 7 exact inverse composition and mutation rejection."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_kernel_speed_source_contract import ledger,preimages,historical_bytes
from portable_optimizer_six_source_contract import preimages as six_preimages

class KernelSpeedHistoryTests(unittest.TestCase):
 def test_every_kernel_and_dependency_inverse_is_exact_and_rejects_extra_bytes(self):
  data=ledger(ROOT);old=preimages(ROOT);self.assertEqual(set(old),set(data['files']));self.assertEqual(len(old),11)
  for name,text in old.items():
   self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),data['files'][name]['before_sha256'])
   self.assertEqual(historical_bytes(ROOT,name,text.encode()),text.encode())
   with self.assertRaisesRegex(ValueError,'Unreviewed Unit 7'):historical_bytes(ROOT,name,(ROOT/name).read_bytes()+b' ')
 def test_composes_before_unit_six_and_keeps_all_prior_digests(self):
  data=json.loads((ROOT/'tests/fixtures/portable-optimizer-six-source-delta.json').read_text());old=six_preimages(ROOT)
  for name,row in data['files'].items():self.assertEqual(hashlib.sha256(old[name].encode()).hexdigest(),row['before_sha256'])
 def test_changed_ledger_is_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'tests/fixtures';p.mkdir(parents=True);(p/'portable-kernel-speed-source-delta.json').write_text('{}')
   with self.assertRaisesRegex(ValueError,'ledger changed'):ledger(tmp)
