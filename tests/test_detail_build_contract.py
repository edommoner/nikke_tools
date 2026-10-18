import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from detail_build_contract import checked_detail_abi
class DetailedBuildContractTests(unittest.TestCase):
 def test_current_sources_and_manifest_abi_agree_without_loading_cuda(self):
  import json
  abi=checked_detail_abi((ROOT/'app/detail_effects.cu').read_bytes(),(ROOT/'app/detail_gpu.py').read_bytes())
  self.assertEqual(abi,json.loads((ROOT/'app/detail_effects-build.json').read_text())['abi'])
 def test_missing_ambiguous_and_stale_exports_fail_before_compilation(self):
  cuda=b'extern "C" __global__ void detail_example() {}'
  host=b'DETAIL_ABI="detail_example"\n'
  for shader,python in ((b'',host),(cuda,b''),(cuda+cuda,host),(cuda,host+host),(cuda,b'DETAIL_ABI="detail_stale"\n')):
   with self.subTest(shader=shader,host=python),self.assertRaises(ValueError):checked_detail_abi(shader,python)
if __name__=='__main__':unittest.main()
