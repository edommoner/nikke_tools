import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from portable_product_fixed import lower


class FixedCopyTests(unittest.TestCase):
    def test_only_config_path_is_copied_and_original_is_not_mutated(self):
        prepared=dict(policies=dict(config=dict(burst_gauge_mode='fixed',first_burst_time=3),other=['policy']),
                      chars=[dict(name=str(i)) for i in range(5)],effects=[{'effect':{'stat':'atk'}}],enemy={'patterns':[]})
        before=copy.deepcopy(prepared)
        result,values=lower(prepared)
        self.assertEqual(prepared,before)
        self.assertEqual(values,(3,[2.]*5))
        self.assertIsNot(result,prepared)
        self.assertIsNot(result['policies'],prepared['policies'])
        self.assertIsNot(result['policies']['config'],prepared['policies']['config'])
        for key in ('chars','effects','enemy'):self.assertIs(result[key],prepared[key])
        result['policies']['config']['first_burst_time']=5
        self.assertEqual(prepared,before)
