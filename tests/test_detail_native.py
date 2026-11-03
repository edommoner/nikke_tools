"""Committed legacy images stay hash-bound and reject the new burst source."""
import unittest,json,hashlib,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from detail_gpu import module_image,UnsupportedDetail
class NativeModuleIntegrityTests(unittest.TestCase):
 def test_architecture_matching_and_hashes(self):
  path=ROOT/'app/detail_effects-sm86.cubin'
  if not path.exists():self.skipTest('Optional architecture binary was not built')
  meta=json.loads(path.with_suffix('.json').read_text())
  self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),meta['binary_sha256'])
  source=ROOT/'app/detail_effects.cu'
  self.assertNotEqual(hashlib.sha256(source.read_bytes()).hexdigest(),meta['source_sha256'])
  # Retain successful historical binary loading under its exact recorded source.
  from portable_weighted_incoming_source_contract import reference_engine_source_bytes
  old=reference_engine_source_bytes(ROOT,'app/detail_effects.cu')
  self.assertEqual(hashlib.sha256(old).hexdigest(),meta['source_sha256'])
  original=Path.read_bytes
  with patch.object(Path,'read_bytes',lambda p:old if p==source else original(p)):
   blob,digest,kind=module_image(SimpleNamespace(compute_capability=(8,6)))
   self.assertEqual(kind,'cubin-sm86');self.assertEqual(blob,path.read_bytes());self.assertEqual(digest,meta['binary_sha256'])
  with self.assertRaises(UnsupportedDetail):module_image(SimpleNamespace(compute_capability=(8,6)),'native')
  with self.assertRaises(UnsupportedDetail):module_image(SimpleNamespace(compute_capability=(8,6)))
 def test_other_architecture_rejects_stale_portable_ptx(self):
  source=ROOT/'app/detail_effects.cu';original=Path.read_bytes
  from portable_weighted_incoming_source_contract import reference_engine_source_bytes
  old=reference_engine_source_bytes(ROOT,'app/detail_effects.cu')
  with patch.object(Path,'read_bytes',lambda p:old if p==source else original(p)):
   _,_,kind=module_image(SimpleNamespace(compute_capability=(9,0)));self.assertEqual(kind,'ptx')
  with self.assertRaises(UnsupportedDetail):module_image(SimpleNamespace(compute_capability=(9,0)))
  with self.assertRaises(UnsupportedDetail):module_image(SimpleNamespace(compute_capability=(9,0)),'native')
  with self.assertRaises(ValueError):module_image(SimpleNamespace(),'unknown')
 def test_stale_ptx_is_rejected_before_loading(self):
  original=Path.read_bytes
  with patch.object(Path,'read_bytes',lambda p:b'stale PTX' if p.name=='detail_effects.ptx' else original(p)):
   with self.assertRaises(UnsupportedDetail):module_image(SimpleNamespace(),'ptx')
if __name__=='__main__':unittest.main()
