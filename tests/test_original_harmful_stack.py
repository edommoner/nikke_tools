"""Complete original auto inputs and observer recovery for harmful-stack removal."""
import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import nikke_gpu
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
    def test_case_listing_uses_the_actual_suite_and_never_simulates(self):
        from calculator import timeline
        with patch.object(timeline,'simulate',side_effect=AssertionError('Listing must not simulate')):result=nikke_gpu.case_names('coordinate-original-harmful-stack')
        self.assertEqual(result['suite'],'coordinate-original-harmful-stack');self.assertEqual(len(result['cases']),2);self.assertEqual(result['gpu_calls'],0)
    def test_complete_original_auto_rosters_without_cpu_schedule(self):
        from calculator import timeline
        from portable_parent_oracles import provider
        from portable_coordinate_kind_admission import KindAdmission
        with patch.object(timeline,'simulate',side_effect=AssertionError('No CPU schedule in input')):rows,_=a.prepare()
        self.assertEqual(len(rows),2);self.assertEqual(a.SOURCE,nikke_gpu.SUITES['coordinate-original-enemy-stack']['source'])
        for duration,(_,words,domain) in zip((6,86),rows):
            c,m,_,_=domain;self.assertEqual(c['duration'],duration);self.assertEqual(c['original_run']['body']['burst_policy'],'auto');self.assertEqual(len(c['effects']),82)
            self.assertEqual(c['coordinate_packet_history'],'ordered-sha256-v1')
            self.assertEqual(set(m['binding_source_indices']),set(range(82)));self.assertEqual(c['effects'],[r['effect'] for r in c['original_run']['prepared']['effects']]);self.assertEqual(c['sequence'],[])
            self.assertEqual(KindAdmission(ROOT,a.SOURCE).inspect(words)['unsupported'],[]);self.assertIs(provider(a,domain)[2],a.native_reference)
    def test_observers_restore_after_native_failure(self):
        from calculator.buff_manager import BuffManager
        from world_original_stack_native import capture
        methods=('_register_all','_dispatch_instant','_apply_buff_max_stack_add','notify');before=[getattr(BuffManager,k) for k in methods]
        with self.assertRaisesRegex(RuntimeError,'native stopped'):
            with capture({}):raise RuntimeError('native stopped')
        self.assertEqual(before,[getattr(BuffManager,k) for k in methods])
if __name__=='__main__':unittest.main()
