"""Original DoT stack changes retain original identities, membership and phase."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('original_enemy_stack_test',ROOT/'research/verify-coordinate-original-enemy-stack-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class EnemyStackTests(unittest.TestCase):
    def test_wire_timer_infinity(self):
        import json, struct
        from portable_specs import LIMITS as L
        words = [0] * 159744
        at = L['STATE_BASE'] + 10 + 2
        words[at:at + 2] = [0, 2146435072]
        self.assertEqual(a.source.timer_expiry(words, 1), float('inf'))
        words[at:at + 2] = struct.unpack('<II', struct.pack('<d', 1e+30))
        self.assertEqual(a.source.timer_expiry(words, 1), 1e+30)
    def test_actual_lethal_cap_and_clock_witness_rejects_changed_state(self):
        _,_,domain=a.prepare()[0][2];n=a.native_reference(domain);self.assertTrue(a.verify_witness(domain[0],n))
        for kind in ('stack','clock','expiry','membership'):
            bad=copy.deepcopy(n);after=bad['original_enemy_stacks']['dispatches'][0]['after'][0]
            if kind=='stack':after['stack']=21
            elif kind=='clock':after['dot']['next']+=1
            elif kind=='expiry':after['end']=10.
            else:bad['original_enemy_stacks']['dispatches'][0]['before'][0]['members']=[]
            with self.subTest(kind=kind),self.assertRaises(AssertionError):a.verify_witness(domain[0],bad)
    def test_selected_observer_restores_after_exception(self):
        from calculator.buff_manager import BuffManager
        from world_original_stack_native import capture
        methods=('_register_all','_dispatch_instant','_apply_buff_max_stack_add','notify');before=[getattr(BuffManager,k) for k in methods]
        with self.assertRaisesRegex(RuntimeError,'probe failed'):
            with capture({},selected_rows={3}):raise RuntimeError('probe failed')
        self.assertEqual(before,[getattr(BuffManager,k) for k in methods])
if __name__=='__main__':unittest.main()
