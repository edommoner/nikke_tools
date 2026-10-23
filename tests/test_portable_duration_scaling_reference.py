"""Native expiry semantics, full observers and unmodified portable rejection."""
import copy,importlib.util,sys,unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker,portable_backend
from calculator.buff_manager import BuffManager
from portable_duration_scaling_cases import fixtures,synthetic_fixtures,real_fixtures
from portable_duration_scaling_contracts import verify
from world_duration_scaling_native import observe
from world_projectile_native import observe as plain
from world_late_attack_random_native import capture_queries
from world_frame_native import roster_names

@contextmanager
def read_calls():
    expiry=BuffManager._expires_at;reference=BuffManager.ref_count;calls=[]
    def expires(bm,e,c,t):
        value=expiry(bm,e,c,t);calls.append(('expiry',e.get('name'),c,t,value));return value
    def ref(bm,c,key):
        value=reference(bm,c,key);calls.append(('reference',c,key,value));return value
    with patch.object(BuffManager,'_expires_at',expires),patch.object(BuffManager,'ref_count',ref):yield calls

class DurationScalingReferenceTests(unittest.TestCase):
    def test_all31_observers_preserve_original_battle_trace_and_all_reads(self):
        cases=fixtures();before=copy.deepcopy(cases);self.assertEqual(len(cases),31)
        s=importlib.util.spec_from_file_location('duration_test_real',ROOT/'research/verify-world-projectile-rosters.py');real=importlib.util.module_from_spec(s);s.loader.exec_module(real)
        with patch.object(portable_backend,'execute',side_effect=AssertionError('GPU forbidden')):
            for c in cases:
                with self.subTest(case=c['name']):
                    names=c['body']['squad'] if 'body' in c else roster_names(c)
                    with capture_queries(names) as (queries,samples),read_calls() as calls:n,t=observe(c)
                    verify(c,n);n.pop('duration_scaling')
                    with capture_queries(names) as (original_queries,original_samples),read_calls() as original_calls:
                        if 'body' in c:
                            battle,shots=real.native_reference(c['body']);expected=dict(battle=battle,projectile_shots=shots);trace=[]
                        else:expected,trace=plain(c)
                    self.assertEqual((n,t),(expected,trace));self.assertEqual(queries,original_queries);self.assertEqual(samples,original_samples);self.assertEqual(calls,original_calls)
        self.assertEqual(cases,before)

    def inspect(self,label):return observe(next(c for c in synthetic_fixtures() if c['name']=='duration-scaling-'+label))[0]['duration_scaling']
    def test_zero_missing_gauge_shadow_and_pre_increment_order(self):
        for label,values in [('missing',[None]*3),('zero-gauge-shadows-stack',[0]*3),('gauge-fraction',[2]*3),('growing-before',[1,2,3]),('growing-after',[None,1,2]),('ref-expired',[3,None,None])]:
            rows=self.inspect(label)['checks'];self.assertEqual([r['reads'][0]['value'] for r in rows],values)
        rows=self.inspect('self-reference-before-increment')['checks'];self.assertEqual([r['reads'][0]['value'] for r in rows],[None,1,2]);self.assertEqual([r['expires_at'] for r in rows],[0.,.5,1.])

    def test_duration_precedence_and_infinite_sentinels_are_not_negative_clamp(self):
        for label in ('infinite-sentinel','infinite-absent'):
            rows=self.inspect(label)['checks'];self.assertTrue(rows);self.assertTrue(all(not r['reads'] and r['expires_at']==float('inf') for r in rows))
        for label,seconds in [('negative-finite-duration',-6),('level-duration',.375),('explicit-duration-precedes-level',.15000000000000002),('zero-duration',0)]:
            row=self.inspect(label)['checks'][0];self.assertEqual(row['expires_at'],row['time']+seconds)

    def test_same_name_alias_uses_applying_definition_reference(self):
        rows=self.inspect('same-name-alias-distinct-reference')['checks'];self.assertEqual([r['reads'][0]['value'] for r in rows],[3,1]*3)
        self.assertEqual(len(self.inspect('same-name-alias-source-duration')['carriers']),1)

    def test_expiry_reference_owner_definition_carrier_and_trace_faults_are_rejected(self):
        c=synthetic_fixtures()[0];n,t=observe(c)
        faults=[lambda d:d['checks'][0].update(expires_at=9),lambda d:d['checks'][0]['reads'][0].update(value=0),lambda d:d['checks'][0]['reads'][0].update(owner=4),lambda d:d['checks'][0].update(reference='wrong'),lambda d:d['checks'][0].update(definition=99),lambda d:d['carriers'][0].update(stack=99),lambda d:d.update(trace_sha256='0'*64),lambda d:d.update(definitions=99)]
        for i,change in enumerate(faults):
            bad=copy.deepcopy(n);change(bad['duration_scaling'])
            with self.subTest(fault=i),self.assertRaises(AssertionError):verify(c,bad)

    def test_real_all80_definitions_need_shield_break_to_reach_handlers(self):
        for c in real_fixtures():
            n,t=observe(c);verify(c,n);data=n['duration_scaling'];self.assertEqual(data['definitions'],80)
            if c['name'].endswith('/baseline'):self.assertEqual(data['checks'],[])
            else:
                self.assertEqual([r['stat'] for r in data['checks']],['stealth','stun'])
                for r in data['checks']:self.assertEqual(r['expires_at'],r['time']+1);self.assertEqual(r['reads'][0]['value'],1)

    def test_reference_contract_does_not_open_portable_fields(self):
        from portable_runtime import validate_effect,UnsupportedPortable
        from portable_readiness_semantics import reference_readiness
        for stat in ('stealth','stun'):
            e=synthetic_fixtures()[0]['effects'][-1];e.update(stat=stat)
            with self.assertRaises(UnsupportedPortable):validate_effect(e,combat={},world_frame=False)
            validate_effect(e,combat={},world_frame=True)
            r=reference_readiness(dict(phase='effect',category='fields',kind='buff',stat=stat,target='self',fields=['duration_scaling','duration_scaling_ref']))
            self.assertEqual(r['reference_suites'],['duration-scaling','duration-scaling-mixed']);self.assertEqual(r['recorded_cases'],40)
            self.assertEqual(r['scoped_metal_validation']['expiry_checks'],160);self.assertTrue(r['scoped_metal_validation']['independently_audited'])
            for key in ('gpu_supported','gpu_admission_verified','full_character_verified','runtime_validation_performed'):self.assertIs(r[key],False)

if __name__=='__main__':unittest.main()
