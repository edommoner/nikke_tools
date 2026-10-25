"""Original DoT stack changes retain original identities, membership and phase."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import nikke_gpu
s=importlib.util.spec_from_file_location('original_enemy_stack_test',ROOT/'research/verify-coordinate-original-enemy-stack-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class EnemyStackTests(unittest.TestCase):
    def test_exact_dot_membership_inverse_and_wire_timer_infinity(self):
        from portable_coordinate_original_enemy_stack_source_contract import project_sources
        import json,struct
        from portable_specs import LIMITS as L
        data=json.loads((ROOT/'tests/fixtures/portable-coordinate-original-enemy-stack-source-delta.json').read_text());out=project_sources(ROOT)
        for name,row in data['sources'].items():self.assertEqual(out[name],row['baseline'])
        name='gpu/world_actor_stacks.slang'
        with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\n'})
        words=[0]*159744;at=L['STATE_BASE']+10+2
        words[at:at+2]=[0,0x7ff00000];self.assertEqual(a.source.timer_expiry(words,1),float('inf'))
        words[at:at+2]=struct.unpack('<II',struct.pack('<d',1e30));self.assertEqual(a.source.timer_expiry(words,1),1e30)
    def test_original_complete_rosters_no_cpu_schedule_and_same_gpu_source(self):
        from calculator import timeline
        from portable_coordinate_kind_admission import KindAdmission
        from portable_parent_oracles import provider
        with patch.object(timeline,'simulate',side_effect=AssertionError('No simulated input')):rows,_=a.prepare()
        self.assertEqual(len(rows),4);self.assertEqual(a.SOURCE,nikke_gpu.SUITES['coordinate-original-shared']['source'])
        for _,words,(c,m,b,d) in rows:
            self.assertEqual(len(c['names']),5);self.assertEqual(set(m['binding_source_indices']),set(range(len(c['effects']))))
            self.assertEqual(c['effects'],[e['effect'] for e in c['original_run']['prepared']['effects']]);self.assertEqual(c['sequence'],[])
            self.assertEqual(KindAdmission(ROOT,a.SOURCE).inspect(words)['unsupported'],[]);self.assertIs(provider(a,(c,m,b,d))[2],a.native_reference)
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
