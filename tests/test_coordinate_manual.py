"""Manual control packing, canonical event ordering and strict wire boundaries."""
import copy,importlib.util,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from calculator import timeline
from portable_coordinate_manual_cases import fixtures
from world_coordinate_manual_native import observe
from portable_manual_control_specs import normalize,pack,check_layout,MAGIC
from portable_charge_control_specs import OWNER_BASE,SEQUENCE_BASE,WORDS
s=importlib.util.spec_from_file_location('manual_test_adapter',ROOT/'research/verify-coordinate-manual-short.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class PackingTests(unittest.TestCase):
    def test_all_literal_worlds_pack_without_simulation_and_restore_compiler(self):
        adapter=a.control_adapter();before=(adapter.normalize_static_controls,adapter.compile_policy)
        cases=fixtures();original=copy.deepcopy(cases)
        with patch.object(timeline,'simulate',side_effect=AssertionError('packing must not simulate')):
            for c in cases:
                w,m,b,d=a.compile_case(c);p=m['_control_policy']
                self.assertEqual((len(w),len(p),p[1],p[7]),(109528,WORDS,3,MAGIC));self.assertFalse(any(p[8:16]))
                self.assertEqual(p[OWNER_BASE+1],len(c['controls'][0]['sequence']))
        self.assertEqual(cases,original);self.assertEqual((adapter.normalize_static_controls,adapter.compile_policy),before)
    def test_time_zero_none_and_action_wire_are_distinct(self):
        for label,value in [('zero-at-zero',0.),('until-reload-full',-1.)]:
            c=next(c for c in fixtures() if c['name'].endswith('/'+label));_,m,*_=a.compile_case(c);p=m['_control_policy']
            self.assertEqual(struct.unpack('<d',struct.pack('<II',*p[SEQUENCE_BASE+2:SEQUENCE_BASE+4]))[0],value);self.assertEqual(p[SEQUENCE_BASE+4],1)
    def test_invalid_literals_capacity_and_policies_fail_without_simulation(self):
        base=fixtures()[0]
        changes=[]
        for value in (-1,float('nan'),float('inf'),True,181):
            changes.append({'sequence':[dict(action='cover',t=0,duration=value)]})
        changes += [{'sequence':[dict(action='reload',t=0)]},{'sequence':[dict(action='cover',t=True,duration=1)]},{'sequence':[dict(action='cover',t=0,duration=1,computed_end=1)]},{'sequence':[dict(action='cover',t=0)]*9},{'cover':{'policy':'x'}}]
        for control in changes:
            c=copy.deepcopy(base);c['controls'][0]=control
            with self.subTest(control=control),patch.object(timeline,'simulate',side_effect=AssertionError('simulation')):
                with self.assertRaises(ValueError):a.compile_case(c)
    def test_cli_rejects_inherited_wrong_gpu_source_before_preparation(self):
        from types import SimpleNamespace
        s=importlib.util.spec_from_file_location('manual_cli_test',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
        self.assertEqual(cli.SUITES['coordinate-manual']['source'],a.SOURCE)
        fake=SimpleNamespace(STRICT_WIRE_DIMENSIONS=True,SOURCE=a.SOURCE,suite=SimpleNamespace(OUTPUT=a.OUTPUT_WORDS))
        with patch.object(cli,'module',return_value=fake):
            self.assertIs(cli.open_suite({'suite':'coordinate-manual'}),fake)
            with patch.dict(cli.SUITES['coordinate-manual'],source=a.parent.SOURCE):
                with self.assertRaisesRegex(ValueError,'source'):cli.open_suite({'suite':'coordinate-manual'})
    def test_static_input_type_rejects_conflicting_minimum_cycle(self):
        c=next(c for c in fixtures() if c['name'].endswith('/hold-then-cover'));c['combat']['weapons'][0]['min_cycle']=.2
        with self.assertRaisesRegex(ValueError,'minimum cycle'):a.compile_case(c)
    def test_layout_uses_only_preexisting_unused_tail(self):
        x=check_layout(ROOT);self.assertEqual((x['words'],x['extra_runtime_bytes'],x['extra_output_words']),(80,0,0))
    def test_missing_cover_listener_uses_sentinel(self):
        c=fixtures()[0];c['effects'].pop();c['owners'].pop();_,m,*_=a.compile_case(c);self.assertEqual(m['_control_policy'][6],0xffffffff)
class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=fixtures();cls.original=copy.deepcopy(cls.cases);cls.n={c['name'].split('/')[-1]:observe(c)[0] for c in cls.cases}
    def ev(self,key,kind):return [e for e in self.n[key]['manual_actions']['events'] if e['kind']==kind]
    def test_native_inputs_unchanged_and_profile_restored(self):
        self.assertEqual(self.cases,self.original);self.assertIsNone(sys.getprofile());self.assertEqual(len(self.n),25)
    def test_zero_time_retains_raw_zero_but_later_zero_exits_next_frame(self):
        self.assertEqual(self.n['zero-at-zero']['manual_actions']['characters'][0]['until'],0.);self.assertFalse(self.ev('zero-at-zero','_exit_cover'))
        self.assertGreater(self.ev('zero-later','_exit_cover')[0]['time'],self.ev('zero-later','_enter_cover')[0]['time'])
    def test_none_consumes_entry_frame_before_leaving_full_magazine(self):
        self.assertGreater(self.ev('until-reload-full','_exit_cover')[0]['time'],self.ev('until-reload-full','_enter_cover')[0]['time'])
    def test_loaded_cancel_preserves_ammo_without_completion(self):
        start=self.ev('cancel-loaded','_enter_cover')[0];cancel=self.ev('cancel-loaded','_cancel_reload')[0]
        self.assertEqual(cancel['ammo'],start['ammo']);self.assertFalse(self.ev('cancel-loaded','_finish_reload'))
    def test_until_reload_exits_after_completion_and_clip_cancel_keeps_partial_ammo(self):
        finish=self.ev('clip-until-reload','_finish_reload');exit=self.ev('clip-until-reload','_exit_cover');self.assertEqual(exit[0]['time'],finish[-1]['time']);self.assertEqual(finish[-1]['ammo'],3)
        cancel=self.ev('clip-cancel','_cancel_reload');self.assertTrue(cancel);self.assertEqual(cancel[0]['ammo'],1);self.assertEqual(cancel[0]['reload_until'],-1.)
    def test_disabled_entry_and_mid_cover_drop(self):
        self.assertFalse(self.ev('disabled-entry','_enter_cover'));self.assertEqual(self.n['disabled-entry']['manual_actions']['characters'][0]['sequence_index'],1)
        self.assertLess(self.ev('disabled-during','_exit_cover')[0]['time'],.6)
    def test_camera_preemption_and_mode_paths_are_actual(self):
        n=self.n['camera-preempt'];self.assertTrue(any(n['battle']['manual_control']['preemptions']));self.assertEqual(self.ev('camera-preempt','_exit_cover')[0]['owner'],0)
        for k in ('mode-auto','mode-charge','entry-reload'):self.assertTrue(self.ev(k,'_enter_cover'));self.assertTrue(self.ev(k,'_exit_cover'))
    def test_cover_exit_preserves_later_authored_hold(self):
        n=self.n['cover-then-hold'];self.assertEqual(n['battle']['manual_control']['characters'][0]['release_time'],1.5)
        self.assertFalse(n['physical_pellets']);self.assertFalse(n['sampled_draws'])
        import random
        seed=next(c['seed'] for c in self.cases if c['name'].endswith('/cover-then-hold'));state=random.Random(seed).getstate()[1]
        self.assertEqual(n['physical_rng'],dict(index=state[-1],state=list(state[:-1])))
        from portable_coordinate_sampling_contracts import verify
        bad=copy.deepcopy(n);bad['physical_rng']['state'][0]^=1
        with self.assertRaises(AssertionError):verify(next(c for c in self.cases if c['name'].endswith('/cover-then-hold')),bad)
    def test_auto_base_preserves_mode_charge_phase_but_clears_visible_charging(self):
        for key in ('mode-charge','mode-charge-visibility','mode-charge-cover-visibility'):
            row=self.ev(key,'_enter_cover')[0];self.assertEqual(row['phase'],'charging');self.assertFalse(row['charging_visible'])
            starts=self.ev(key,'_charge_start');self.assertTrue(any(e['time']>row['time'] and e['charging_visible'] for e in starts))
    def test_same_frame_sequence_order_and_cover_damage(self):
        e=self.ev('same-frame-replace','_enter_cover');self.assertEqual([r['time'] for r in e],[0.,0.]);self.assertEqual(self.n['same-frame-replace']['manual_actions']['characters'][0]['sequence_index'],2)
        self.assertEqual(self.n['incoming-cover']['battle']['allies'][0]['hp'],10000);self.assertLess(self.n['incoming-cover']['battle']['covers'][0]['hp'],1000)
if __name__=='__main__':unittest.main()
