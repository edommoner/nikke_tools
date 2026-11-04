"""Coarse-only admission/omissions, complete candidate accounting and verifier flow."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
import engine_worker as engine
import gpu_combat
from engine_gpu_admission import UnsupportedEngineKeys
from calculator.buff_manager import BuffManager

UNIT=ROOT.parent/'proofs/claude-product-standard-phase0-v1-20261102/optimizer-metal-v1'


def verifier():
    spec=importlib.util.spec_from_file_location('prefilter_v3_verifier',UNIT/'verify-metal-prefilter.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class CoarsePreparationTests(unittest.TestCase):
    def test_all_three_new_character_squads_prepare_with_individual_issues(self):
        bodies=json.loads((ROOT/'tests/fixtures/gpu-new-characters-product-v1.json').read_text())
        self.assertEqual({b['squad'][0] for b in bodies},{'마리안 : 퀸','라푼젤 : 생츄어리','홍련 : 신살'})
        with patch.object(engine.sim,'execute',side_effect=AssertionError('Coarse preparation cannot run combat')):
            for body in bodies:
                for backend in ('cpu','metal_detail','cuda_detail'):
                    with self.subTest(character=body['squad'][0],backend=backend):
                        model=engine.evaluate(dict(copy.deepcopy(body),_compile_gpu=True,compute_backend=backend))
                        self.assertEqual(model['names'],body['squad']);self.assertEqual(len(model['chars']),220)
                        self.assertTrue(any(i['character']==body['squad'][0] for i in model['issues']))
                        self.assertTrue(all(isinstance(i['effect'],str) and i['reason'] for i in model['issues']))
                # Detail admission remains the legacy refusal, including when
                # both internal flags are present. No CUDA device is touched.
                for flags in ({'_compile_gpu_detail':True},{'compute_backend':'cuda_detail'},{'_compile_gpu':True,'_compile_gpu_detail':True}):
                    with self.subTest(character=body['squad'][0],detail_flags=flags),self.assertRaises(UnsupportedEngineKeys):
                        engine.evaluate(dict(copy.deepcopy(body),**flags))

    def test_actual_demo_list_target_omits_only_that_effect(self):
        squad=['메어리','벨로타 : 펌킨 위치','E.H.','브리드','소다 : 트윙클링 바니']
        body=dict(profile=engine.demo(True)['profile'],squad=squad,duration=180,level=400,_compile_gpu=True)
        with patch.object(engine.sim,'execute',side_effect=AssertionError('No battle')):
            model=engine.evaluate(body)
        self.assertEqual(model['names'],squad)
        self.assertTrue(any("['self', 'allies_top_atk_excl:1']" in i['reason'] and '対象' in i['reason'] for i in model['issues']))
        self.assertTrue(model['effects'])

    def test_nested_string_fields_are_issues_not_string_operation_exceptions(self):
        demo=engine.detail_demo();body=dict(profile=demo['profile'],squad=demo['squad'],duration=1,_compile_gpu=True)
        original=BuffManager.__init__
        bads=[dict(target=['self','all_allies']),dict(trigger=dict(timing=[['passive']])),dict(trigger=dict(condition=[['during_full_burst']])),dict(stat=['atk_pct']),dict(source=['S1'])]
        for bad in bads:
            def inject(manager,*args,**kwargs):
                original(manager,*args,**kwargs)
                effect=dict(name='unsupported-shape',source='S1',type='buff',stat='atk_pct',target='self',fixed_value=999,trigger=dict(timing=['passive']),duration=-1)
                effect.update(bad);manager._effects.append((effect,body['squad'][0]))
            with self.subTest(bad=bad),patch.object(BuffManager,'__init__',inject):
                result=engine.evaluate(copy.deepcopy(body))
            self.assertTrue(any(i['effect']=='unsupported-shape' for i in result['issues']))

    def test_prefilter_retains_errors_indices_counts_even_with_no_prepared_models(self):
        squads=[list('abcde'),list('fghij')]
        model=dict(names=squads[0],issues=[dict(character='a',effect='omitted',reason='not supported')],enemy=[1,0,0,0,0])
        class Device:
            def run(self,models):
                return dict(backend='metal',scores=[dict(squad=m['names'],damage=123) for m in models])
        with patch.object(engine,'evaluate',side_effect=[model,ValueError('bad candidate')]):
            result=gpu_combat.prefilter(dict(backend='metal',evaluation={},squads=squads),None,Device())
        self.assertEqual(result['prepared_candidates'],1);self.assertEqual(result['scored_candidates'],1)
        self.assertEqual(result['unscored_candidates'],1);self.assertEqual(result['unscored_indices'],[1])
        self.assertEqual(result['errors'],[dict(index=1,squad=squads[1],error='bad candidate')])
        self.assertEqual(result['scores'][0]['index'],0)
        with patch.object(engine,'evaluate',side_effect=ValueError('bad candidate')),patch.object(gpu_combat,'Combat') as device:
            result=gpu_combat.prefilter(dict(backend='metal',evaluation={},squads=squads),None)
        device.assert_not_called();self.assertEqual(result['scores'],[])
        self.assertEqual(result['backend'],'cpu');self.assertEqual(result['requested'],'metal')
        self.assertEqual(result['unscored_candidates'],2);self.assertEqual(result['unscored_indices'],[0,1])


class PrefilterVerifierTests(unittest.TestCase):
    def test_actual_standard0_records_burst_quota_refusal_without_device(self):
        module=verifier()
        body=json.loads((ROOT.parent/'proofs/product-standard180-run-v5-20261102/api-v1/requests.json').read_text())[0]['body']
        with patch.object(module.MetalCombat,'run',side_effect=AssertionError('No device for unusable profile')):
            result=module.verify_profile('standard-0',body,1)
        self.assertEqual(result['status'],'unusable');self.assertEqual(result['stage'],'candidate_pool')
        self.assertEqual(result['available_characters'],5);self.assertTrue(result['reason'])
        self.assertEqual(sum('3' in c['burst'] for c in result['burst_stages']),1)

    def test_unusable_profile_does_not_abort_later_profile_and_publication(self):
        module=verifier();published=[]
        outputs=[dict(profile='small',status='unusable',reason='not enough III',stage='candidate_pool'),dict(profile='valid',status='verified',stage='complete')]
        with patch.object(module,'verify_profile',side_effect=outputs) as verify,contextlib.redirect_stdout(io.StringIO()):
            rows=module.run_profiles([('small',{},1),('valid',{},5)],lambda partial:published.append(copy.deepcopy(partial)))
        self.assertEqual(verify.call_count,2);self.assertEqual([len(r) for r in published],[1,2])
        summary=module.summarize(rows);self.assertTrue(summary['completed']);self.assertTrue(summary['passed'])
        self.assertEqual(summary['profile_counts'],dict(verified=1,unusable=1,failed=0,not_run=0))

    def test_subprocess_failure_reports_stderr_and_metal_failure_is_not_retried(self):
        module=verifier()
        with patch.object(module.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'','node startup failed')):
            with self.assertRaisesRegex(RuntimeError,'node startup failed'):module.candidate_pool(dict(characters=[],templates=[]),1)
        with patch.object(module,'verify_profile',return_value=dict(profile='first',status='failed',stage='metal',error='AGX failure')) as verify,contextlib.redirect_stdout(io.StringIO()):
            rows=module.run_profiles([('first',{},1),('second',{},1)])
        verify.assert_called_once();self.assertEqual(rows[1]['status'],'not_run')
        self.assertFalse(module.summarize(rows)['passed'])


class CoarseAdmissionHistoryTests(unittest.TestCase):
    def test_only_exact_coarse_condition_delta_can_use_prior_source_history(self):
        import hashlib
        import portable_weighted_incoming_source_contract as contract
        raw=(ROOT/'app/engine_worker.py').read_bytes()
        restored=contract.reference_engine_reviewed_bytes('app/engine_worker.py',raw)
        self.assertEqual(hashlib.sha256(restored).hexdigest(),contract.COARSE_ADMISSION_BEFORE_SHA256)
        self.assertEqual(contract.reference_engine_reviewed_bytes('app/engine_worker.py',restored),restored)
        mutations=[raw+b'\n',raw.replace(b"body.get('_compile_gpu_detail') or not",b"False or not",1),raw.replace(b"== 'cuda_detail'",b"== 'cuda_shared_detail'",1)]
        for mutation in mutations:
            self.assertNotEqual(mutation,raw)
            self.assertEqual(contract.reference_engine_reviewed_bytes('app/engine_worker.py',mutation),mutation)
            self.assertNotEqual(hashlib.sha256(mutation).hexdigest(),contract.COARSE_ADMISSION_BEFORE_SHA256)

if __name__=='__main__':unittest.main()
