"""Literal friendly PRNG contracts and untouched native sampling behavior."""
import copy,importlib.util,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,detail_gpu
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_ally_random_reference_cases import fixtures
from portable_ally_random_reference_contracts import verify
from world_ally_random_reference_native import observe,plain_observe
s=importlib.util.spec_from_file_location('ally_reference_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)


class AllyRandomReferenceTests(unittest.TestCase):
    def test_eighteen_literal_cases_without_packing_or_gpu(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('No factory battle')):cases=fixtures()
        self.assertEqual(len(cases),18);before=copy.deepcopy(cases)
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No packing')),patch.object(detail_gpu,'compile_effects',side_effect=AssertionError('No compiler')):
            for c in cases:
                with self.subTest(case=c['name']):self.assertTrue(verify(c,observe(c)[0])['verified'])
        self.assertEqual(cases,before)

    def test_all_native_fields_trace_rng_state_and_call_counts_preserved(self):
        original=random.sample;resolver=BuffManager._resolve_target_raw
        for c in fixtures():
            counts=[]
            def sampled(*args,**kwargs):counts[-1][0]+=1;return original(*args,**kwargs)
            def resolved(*args,**kwargs):counts[-1][1]+=1;return resolver(*args,**kwargs)
            with self.subTest(case=c['name']),patch.object(random,'sample',sampled),patch.object(BuffManager,'_resolve_target_raw',resolved):
                counts.append([0,0]);plain,trace=plain_observe(c);state=random.getstate()
                counts.append([0,0]);native,recorded=observe(c);native.pop('ally_random_reference')
                self.assertEqual(native,plain);self.assertEqual(recorded,trace);self.assertEqual(counts[0],counts[1]);self.assertEqual(random.getstate(),state)

    def test_friendly_stream_is_independent_of_boss_draws(self):
        cases=fixtures();a=observe(cases[0])[0];b=observe(next(c for c in cases if c['name'].endswith('boss-random-independent')))[0]
        self.assertEqual(a['ally_random_reference'],b['ally_random_reference']);self.assertEqual(a['rng']['draws'],0);self.assertEqual(b['rng']['draws'],6)

    def test_empty_pool_summary_is_zero_and_singleton_consumes_rng(self):
        cases=fixtures()
        for suffix,advance in [('empty',0),('singleton',8)]:
            case=next(c for c in cases if c['name']=='ally-random-'+suffix)
            self.assertEqual(verify(case,observe(case)[0])['global_rng_index_advance_mod624'],advance)

    def test_faults_in_pool_order_rng_or_resolution_are_rejected(self):
        c=fixtures()[0];base,_=observe(c)
        for fault in ['pool','picked','before_index','after_index','state_chain','caster','boss_rng']:
            n=copy.deepcopy(base);obs=n['ally_random_reference'];sample=obs['samples'][0]
            if fault=='pool':sample['pool']=[0,1,2,3]
            elif fault=='picked':sample['picked']=[4]
            elif fault=='before_index':sample['before_index']=0
            elif fault=='after_index':sample['after_index']=624
            elif fault=='state_chain':obs['samples'][1]['before_sha256']='0'*64
            elif fault=='caster':obs['resolutions'][0]['caster']=4
            else:n['rng']['draws']=1
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(c,n)

    def test_unported_random_shapes_remain_rejected(self):
        effect=fixtures()[0]['effects'][-1]
        for target in ['allies_random_with_debuff:1','allies_random:6','allies_random:-1','allies_broken_cover_random:-1']:
            with self.subTest(target=target),self.assertRaises(ValueError):portable_runtime.validate_effect(dict(effect,target=target),combat={},world_frame=True)


if __name__=='__main__':unittest.main()
