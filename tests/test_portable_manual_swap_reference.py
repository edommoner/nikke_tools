"""Manual mode input must survive preparation or fail explicitly, never vanish."""
import copy,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,detail_gpu
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_manual_swap_cases import fixtures
from portable_manual_swap_contracts import verify
from world_manual_swap_native import observe,data_context
from world_projectile_native import observe as plain_observe
from portable_weapon_input import normalize_static_weapon
from portable_runtime import UnsupportedPortable
from portable_readiness import issue
from portable_readiness_semantics import reference_readiness
spec=importlib.util.spec_from_file_location('manual_swap_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


class ManualSwapReferenceTests(unittest.TestCase):
    def test_literal_contracts_without_gpu_or_packing(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('No battle during factory')):cases=fixtures()
        self.assertEqual(len(cases),24);before=copy.deepcopy(cases)
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No packing')),patch.object(detail_gpu,'compile_effects',side_effect=AssertionError('No legacy packing')):
            for case in cases:
                with self.subTest(case['name']):self.assertTrue(verify(case,observe(case)[0])['verified'])
        self.assertEqual(cases,before)

    def test_observer_preserves_all_native_fields_trace_and_query_count(self):
        from calculator.buff_manager import BuffManager
        for case in fixtures():
            with self.subTest(case['name']):
                original=BuffManager.get_buffs;counts=[]
                def counted(*a,**kw):counts[-1]+=1;return original(*a,**kw)
                with patch.object(BuffManager,'get_buffs',counted):
                    counts.append(0)
                    with data_context(case):plain,trace=plain_observe(case)
                    counts.append(0);native,observed_trace=observe(case)
                native.pop('manual_swap');self.assertEqual(native,plain);self.assertEqual(trace,observed_trace);self.assertEqual(counts[0],counts[1])

    def test_roster_reference_cli_bootstraps_native_dependencies_in_fresh_process(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'rosters.json'
            completed=subprocess.run([sys.executable,str(ROOT/'scripts/nikke_gpu.py'),'reference','--suite','manual-swap-rosters','--out',str(out)],cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(completed.returncode,0,completed.stderr)
            report=json.loads(out.read_text());self.assertTrue(report['passed']);self.assertEqual(report['case_count'],2)
            self.assertEqual(report['packing_calls'],0);self.assertEqual(report['gpu_calls'],dict(build=0,execute=0))

    def test_full_original_rosters_and_read_only_observation(self):
        from portable_manual_swap_roster_cases import fixtures as real_fixtures
        from world_manual_swap_roster_native import observe as real_observe,plain_observe as real_plain
        from portable_manual_swap_roster_contracts import verify as real_verify
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No packing')):
            for case in real_fixtures():
                with self.subTest(case['name']):
                    native,trace=real_observe(case);self.assertTrue(real_verify(case,native)['verified'])
                    for fault in ('ready','dispatches','shots'):
                        changed=copy.deepcopy(native);w=changed['manual_swap_roster']
                        if fault=='ready':w['ready'].append(-1)
                        elif fault=='dispatches':w['calls'].append(dict(time=0,caster='wrong',name='wrong',value=0))
                        else:w['physical_shots']+=1
                        with self.assertRaises(AssertionError):real_verify(case,changed)
                    native.pop('manual_swap_roster');plain,ptrace=real_plain(case)
                    self.assertEqual(native,plain);self.assertEqual(trace,ptrace)

    def test_faults_in_ready_calls_start_latch_conditions_and_tick_order_reject(self):
        case=fixtures()[0];native,_=observe(case)
        for fault in ('ready','owner','start','finish','latch','tick','ammo','condition'):
            changed=copy.deepcopy(native);obs=changed['manual_swap']
            if fault=='ready':obs['queries'][0]['result']=False
            elif fault=='owner':obs['queries'][0]['owner']=4
            elif fault=='start':changed['reload_events'].pop(0)
            elif fault=='finish':changed['reload_events'].pop()
            elif fault=='latch':obs['ticks'][0]['after']['reload_until']=0
            elif fault=='tick':obs['ticks'][0]['hits']=1
            elif fault=='ammo':changed['ammo'][0]-=1
            else:obs['conditions'][0]['result']=False
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(case,changed)

    def test_flag_is_rejected_before_character_or_battle_execution(self):
        with patch.object(timeline.CharState,'__init__',side_effect=AssertionError('No constructor on rejected flag')):
            for value in (1,None,'yes'):
                with self.subTest(value=value),self.assertRaises(UnsupportedPortable) as caught:normalize_static_weapon(dict(name='미란다',weapon_mode_swap=value),1,{})
                self.assertEqual(caught.exception.reason,'control');self.assertEqual(caught.exception.fields,['weapon_mode_swap'])
        char=dict(name='미란다',skill_levels={'1':10,'2':10,'3':10});before=copy.deepcopy(char)
        self.assertEqual(normalize_static_weapon(char,1,{}),normalize_static_weapon(dict(char,weapon_mode_swap=False),1,{}));self.assertEqual(char,before)

    def test_real_prepared_true_flag_reaches_explicit_shared_wire_without_battle(self):
        from detail_coverage import body_for
        from portable_projectile_roster_input import compile_projectile_battle
        from portable_specs import LIMITS as L
        names=['미란다','도라','N102','메어리','드레이크']
        body=dict(body_for(names,3,grown=True),burst_gauge_mode='accumulate',_portable_static_inputs=True)
        with cli.forbid_gpu(),patch.object(timeline,'simulate',side_effect=AssertionError('No battle')):
            disabled=engine_worker.evaluate(dict(body,weapon_mode_swap=False));old,_=compile_projectile_battle(disabled)
            prepared=engine_worker.evaluate(dict(body,weapon_mode_swap=True));before=copy.deepcopy(prepared)
            self.assertTrue(all(c['weapon_mode_swap'] is True for c in prepared['chars']))
            words,_=compile_projectile_battle(prepared)
        self.assertEqual(prepared,before);at=L['WORLD_RELOAD_INPUT_BASE']
        self.assertEqual(words[at+3:at+5],[31,0x574d5331])
        self.assertEqual([i for i,(a,b) in enumerate(zip(old,words)) if a!=b],[at+3,at+4])
        blocker=dict(phase='program',category='control',fields=['weapon_mode_swap'])
        r=reference_readiness(blocker);self.assertEqual(r['recorded_cases'],len(fixtures())+2)
        self.assertEqual(r['lane'],'reference_review')
        self.assertFalse(r['gpu_supported']);self.assertFalse(r['runtime_validation_performed'])


if __name__=='__main__':unittest.main()
