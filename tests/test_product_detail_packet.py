"""Product packet admission and full response comparison without GPU calls."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
spec=importlib.util.spec_from_file_location('product_packet',ROOT/'research/verify-product-detail.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class ProductPacket(unittest.TestCase):
    def test_same_original_static_input_and_source_without_battle(self):
        with patch.object(adapter.product.engine_worker.sim,'execute',side_effect=AssertionError('No CPU battle in preparation')):
            rows,raw=adapter.prepare()
        self.assertEqual(len(rows),1)
        self.assertEqual(len(raw),4*(1+adapter.suite.INPUT))
        self.assertFalse(rows[0][2][1]['cpu_battle_executed'])
        self.assertEqual(adapter.SOURCE,'gpu/product_battle_entry.slang')
    def test_full_comparison_includes_provenance_and_all_product_fields(self):
        for field in ('total_damage','warnings','burst_timeline','evaluator'):
            expected={field:1};actual={field:2}
            with patch.object(adapter,'native_reference',return_value=expected),patch.object(adapter.product,'decode_payload',return_value=actual):
                with self.assertRaisesRegex(ValueError,field):adapter.compare([0]*adapter.suite.OUTPUT,({},None,None,None))
        with patch.object(adapter,'native_reference') as native:
            with self.assertRaisesRegex(ValueError,'Complete'):adapter.compare([],None)
            native.assert_not_called()
        for expected,actual in [({'control':None},{}),({}, {'control':None})]:
            with patch.object(adapter,'native_reference',return_value=expected),patch.object(adapter.product,'decode_payload',return_value=actual):
                with self.assertRaisesRegex(ValueError,'control'):adapter.compare([0]*adapter.suite.OUTPUT,({},None,None,None))
    def test_persistent_hash_ignores_only_environment_vcs_stamp(self):
        a={'evaluator':{'commit':'a'},'total_damage':42,'warnings':['original']}
        b=copy.deepcopy(a);b['evaluator']['commit']='unpacked'
        self.assertEqual(adapter.fingerprint(a),adapter.fingerprint(b))
        for field,value in [('total_damage',43),('warnings',[])]:
            b=copy.deepcopy(a);b[field]=value
            self.assertNotEqual(adapter.fingerprint(a),adapter.fingerprint(b))

if __name__=='__main__':unittest.main()
