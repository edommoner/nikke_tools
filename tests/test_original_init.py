"""Original level-dependent initialization, consume/refill and exact source reuse."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('original_init_test',ROOT/'research/verify-coordinate-original-init-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class OriginalInitTests(unittest.TestCase):
    def test_actual_initialization_spending_and_refill_witness_rejects_corruption(self):
        _,_,domain=a.prepare()[0][0];n=a.native_reference(domain);self.assertTrue(a.verify_witness(domain[0],n))
        for target in ('initial','spent','final','notification'):
            bad=copy.deepcopy(n);o=bad['original_stacks']
            if target=='initial':o['dispatches'][0]['after'][0]['stack']+=1
            elif target=='spent':o['dispatches'][1]['after'][0]['stack']+=1
            elif target=='final':o['final'][0]['end']=240.
            else:o['notifications'].append(dict(owner=0,event='stack_reach:'+domain[0]['effects'][1]['name']+':40',time=0.))
            with self.subTest(target=target),self.assertRaises(AssertionError):a.verify_witness(domain[0],bad)
if __name__=='__main__':unittest.main()
