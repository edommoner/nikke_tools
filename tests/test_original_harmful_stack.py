"""Complete original auto inputs and observer recovery for harmful-stack removal."""
import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('original_harmful_stack_test',ROOT/'research/verify-coordinate-original-harmful-stack-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class HarmfulStackTests(unittest.TestCase):
    def test_real_observed_witness_rejects_stack_lifetime_and_dispatch_corruption(self):
        import array,copy,hashlib,json
        data=json.loads((ROOT/'tests/fixtures/portable-original-harmful-stack-observations.json').read_text())
        rows,_=a.prepare()
        for record,(name,words,domain) in zip(data['rows'],rows,strict=True):
            self.assertEqual(record['name'],name);self.assertEqual(record['input_words_sha256'],hashlib.sha256(array.array('I',words).tobytes()).hexdigest())
            self.assertTrue(a.verify_witness(domain[0],record))
        domain=rows[-1][2];record=data['rows'][-1]
        for kind in ('stack','lifetime','membership','dispatch'):
            bad=copy.deepcopy(record);o=bad['original_harmful_stacks'];event=o['dispatches'][0]
            if kind=='stack':event['after'][0]['stack']=1
            elif kind=='lifetime':event['after'][0]['activated']+=1
            elif kind=='membership':event['after'][0]['members']=[]
            else:o['dispatches']=[]
            with self.subTest(kind=kind),self.assertRaises(AssertionError):a.verify_witness(domain[0],bad)
    def test_observers_restore_after_native_failure(self):
        from calculator.buff_manager import BuffManager
        from world_original_stack_native import capture
        methods=('_register_all','_dispatch_instant','_apply_buff_max_stack_add','notify');before=[getattr(BuffManager,k) for k in methods]
        with self.assertRaisesRegex(RuntimeError,'native stopped'):
            with capture({}):raise RuntimeError('native stopped')
        self.assertEqual(before,[getattr(BuffManager,k) for k in methods])
if __name__=='__main__':unittest.main()
