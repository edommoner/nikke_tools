"""Strict numeric predicate contracts before shared host/GPU admission."""
import copy,hashlib,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,detail_gpu
from calculator import timeline
from calculator.buff_manager import BuffManager
from portable_accuracy_predicate_cases import fixtures
from portable_accuracy_predicate_contracts import verify
from world_accuracy_predicate_native import observe,plain_observe
from portable_readiness_semantics import reference_readiness
s=importlib.util.spec_from_file_location('accuracy_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)


class AccuracyPredicateReferenceTests(unittest.TestCase):
    def test_twenty_six_literal_contracts_without_packing_or_gpu(self):
        with patch.object(timeline,'simulate',side_effect=AssertionError('No factory battle')):cases=fixtures()
        self.assertEqual(len(cases),26);before=copy.deepcopy(cases)
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No packing')),patch.object(detail_gpu,'compile_effects',side_effect=AssertionError('No legacy packing')):
            for case in cases:
                with self.subTest(case['name']):self.assertTrue(verify(case,observe(case)[0])['verified'])
        self.assertEqual(cases,before)

    def test_all_native_fields_trace_and_buff_query_count_are_preserved(self):
        original=BuffManager.get_buffs
        for case in fixtures():
            counts=[]
            def counted(*a,**kw):counts[-1]+=1;return original(*a,**kw)
            with self.subTest(case['name']),patch.object(BuffManager,'get_buffs',counted):
                counts.append(0);plain,trace=plain_observe(case)
                counts.append(0);native,recorded=observe(case)
                native.pop('accuracy_predicate');self.assertEqual(native,plain);self.assertEqual(recorded,trace)
                self.assertEqual(counts[0],counts[1])

    def test_wrong_condition_value_owner_order_damage_stack_or_ammo_reject(self):
        case=fixtures()[1];native,_=observe(case)
        for fault in ('result','value','owner','target','time','stack','damage','total','ammo'):
            changed=copy.deepcopy(native);obs=changed['accuracy_predicate']
            if fault=='result':obs['checks'][0]['result']=False
            elif fault=='value':obs['checks'][0]['queries'][0]['value']=0
            elif fault=='owner':obs['checks'][0]['owner']=4
            elif fault=='target':obs['checks'][0]['queries'][0]['target']='wrong'
            elif fault=='time':obs['checks'][0]['time']=10
            elif fault=='stack':obs['carriers'][0]['stack']=2
            elif fault=='damage':changed['projectile_shots'][0]['damage']+=1
            elif fault=='total':changed['damage'][0]+=1
            else:changed['ammo'][0]-=1
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(case,changed)

    def test_whole_original_profile_contract_and_transparent_observation(self):
        from portable_accuracy_predicate_roster_cases import fixtures as real_fixtures
        from world_accuracy_predicate_roster_native import observe as real_observe,plain_observe as real_plain
        from portable_accuracy_predicate_roster_contracts import verify as real_verify
        with cli.forbid_gpu(),patch.object(portable_runtime,'compile_program',side_effect=AssertionError('No packing')):
            for case in real_fixtures():
                native,trace=real_observe(case);self.assertTrue(real_verify(case,native)['verified'])
                native.pop('accuracy_predicate_roster');plain,other=real_plain(case);self.assertEqual(native,plain);self.assertEqual(trace,other)

    def test_standalone_real_reference_initializes_dependencies_and_never_claims_gpu(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'real.json'
            result=subprocess.run([sys.executable,str(ROOT/'scripts/nikke_gpu.py'),'reference','--suite','accuracy-predicate-rosters','--out',str(output)],cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr);report=json.loads(output.read_text());self.assertEqual(report['case_count'],2)
            self.assertTrue(report['cpu_reference_verified']);self.assertFalse(report['gpu_supported']);self.assertFalse(report['calculation_verified'])
            self.assertEqual(report['gpu_calls'],dict(build=0,execute=0));self.assertEqual(report['packing_calls'],0)

    def test_specific_blocker_maps_to_native_contracts_without_admission_claim(self):
        row=dict(phase='effect',category='trigger',kind='buff',stat='atk_pct',target='self',operator=dict(domain='condition',descriptor='self_stat_above:accuracy_pct:0'))
        result=reference_readiness(row);self.assertEqual(result['recorded_cases'],28);self.assertEqual(result['lane'],'gpu_lowering_candidate')
        self.assertFalse(result['gpu_supported']);self.assertFalse(result['runtime_validation_performed'])
        for changed in (dict(kind='damage'),dict(target='all_allies'),dict(operator=dict(domain='condition',descriptor='unknown'))):
            self.assertEqual(reference_readiness(dict(row,**changed))['lane'],'reference_review')

    def test_native_reference_does_not_open_unverified_host_admission(self):
        effect=fixtures()[1]['effects'][-1];before=copy.deepcopy(effect)
        with self.assertRaises(ValueError) as caught:portable_runtime.validate_effect(effect,combat={},world_frame=True)
        self.assertEqual(caught.exception.reason,'trigger')
        self.assertEqual(caught.exception.operator,dict(domain='condition',descriptor='self_stat_above:accuracy_pct:0'))
        self.assertEqual(effect,before)

    def test_deferred_differential_split_is_not_aliased_to_equal_distribution(self):
        evidence=json.loads((ROOT/'tests/fixtures/portable-differential-split-model-gap.json').read_text())
        source=evidence['row'];self.assertTrue(source.startswith('| `received_dmg_split` |'))
        self.assertIn('구현 규격 미정',source);self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),evidence['row_sha256'])
        original=ROOT/evidence['source_path']
        if original.is_file():
            self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),evidence['document_sha256'])
            self.assertIn(source,original.read_text().splitlines())
        from portable_runtime import validate_effect,UnsupportedPortable
        for target in ('all_allies','self_cover'):
            row=dict(phase='effect',category='effect',kind='buff',stat='received_dmg_split',target=target)
            result=reference_readiness(row);self.assertEqual(result['lane'],'reference_model_gap')
            self.assertEqual(result['native_consumer'],'specification_deferred_in_pinned_source');self.assertFalse(result['gpu_supported'])
            effect=dict(name='differential',type='buff',stat='received_dmg_split',target=target,duration=-1,trigger=dict(timing=['battle_start'],condition=[]))
            with self.assertRaises(UnsupportedPortable):validate_effect(effect,combat={},world_frame=True)


if __name__=='__main__':unittest.main()
