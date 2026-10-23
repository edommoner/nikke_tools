"""Native selection/cleanse witnesses and transparent observation contracts."""
import copy,random,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker,portable_runtime,portable_backend,detail_gpu
from calculator.buff_manager import BuffManager
from portable_random_cleanse_cases import fixtures
from portable_random_cleanse_mixed_cases import fixtures as mixed
from portable_random_cleanse_mixed_contracts import verify as verify_mixed
from portable_random_cleanse_budget_cases import fixtures as budget_cases
from portable_random_cleanse_contracts import verify
from world_random_cleanse_native import observe,plain
from portable_readiness_semantics import reference_readiness


class RandomCleanseTests(unittest.TestCase):
    def test18_native_contracts_without_packing_or_gpu(self):
        cases=fixtures();before=copy.deepcopy(cases);self.assertEqual(len(cases),18)
        def no(*a,**kw):raise AssertionError('No packing or GPU')
        with patch.object(portable_runtime,'compile_program',no),patch.object(portable_backend,'build',no),patch.object(portable_backend,'execute',no),patch.object(detail_gpu,'compile_effects',no):
            for c in cases:
                with self.subTest(case=c['name']):self.assertTrue(verify(c,observe(c)[0])['verified'])
        self.assertEqual(before,cases)

    def test_native_battle_trace_random_and_query_counts_unchanged(self):
        for c in fixtures()+mixed()+budget_cases():
            def measured(fn):
                with patch.object(random,'sample',side_effect=random.sample) as sample,patch.object(BuffManager,'_resolve_target_raw',autospec=True,side_effect=BuffManager._resolve_target_raw) as resolve,patch.object(BuffManager,'get_buffs',autospec=True,side_effect=BuffManager.get_buffs) as get,patch.object(BuffManager,'_has_harmful',autospec=True,side_effect=BuffManager._has_harmful) as harmful:
                    result=fn(c);return result,(sample.call_count,resolve.call_count,get.call_count,harmful.call_count),random.getstate()
            with self.subTest(case=c['name']):
                (n,t),counts,state=measured(observe);n.pop('random_cleanse');(p,trace),old,previous=measured(plain)
                self.assertEqual((n,t,counts,state),(p,trace,old,previous))

    def test_pool_self_exclusion_rng_limit_and_membership_faults_rejected(self):
        c=fixtures()[7];base=observe(c)[0]
        for fault in ('pool','picked','k','rng','before_rng','after_rng','owner','before','after','count','boss'):
            n=copy.deepcopy(base);o=n['random_cleanse'];s=o['samples'][0];call=o['calls'][0]
            if fault=='pool':s['pool']=s['pool'][1:]
            elif fault=='picked':s['picked']=[1,4]
            elif fault=='k':s['k']=1
            elif fault=='rng':s['state_changed']=False
            elif fault=='before_rng':s['before_index']=0
            elif fault=='after_rng':s['after_index']=624
            elif fault=='owner':call['owner']=4
            elif fault=='before':call['before']['first'].pop()
            elif fault=='after':call['after']['second']=[1,2,3]
            elif fault=='count':o['calls'].append(copy.deepcopy(call))
            else:n['rng']['draws']=1
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify(c,n)
        c=fixtures()[3];n=observe(c)[0];n['random_cleanse']['calls'][0]['after'].pop('locked')
        with self.assertRaises(AssertionError):verify(c,n)

    def test_private_host_admission_and_readiness_remains_only_recorded_scope(self):
        from portable_reference import REFERENCES
        self.assertIn('random-cleanse',REFERENCES)
        c=fixtures()[0];effect=c['effects'][-1]
        portable_runtime.validate_effect(effect,combat={},world_frame=True)
        for combat,world in ((None,True),({},False)):
            with self.assertRaises(ValueError):portable_runtime.validate_effect(effect,combat=combat,world_frame=world)
        for target in ('allies_random_with_debuff:6','allies_random_with_debuff:-1',['self',effect['target']]):
            with self.assertRaises(ValueError):portable_runtime.validate_effect(dict(effect,target=target),combat={},world_frame=True)
        issue=dict(phase='effect',category='recipient',kind='instant',stat='debuff_cleanse',target='allies_random_with_debuff:2')
        r=reference_readiness(issue);self.assertEqual(r['reference_suites'],['random-cleanse','random-cleanse-mixed','random-cleanse-budget','random-cleanse-rosters']);self.assertEqual(r['recorded_cases'],38)
        self.assertEqual(r['lane'],'native_contract_extension')
        for k in ('gpu_supported','gpu_admission_verified','full_character_verified','runtime_validation_performed'):self.assertFalse(r[k])
        for extra in (dict(target='allies_random_with_debuff:6'),dict(fields=['future']),dict(scaling='stack_count'),dict(kind='buff')):
            self.assertEqual(reference_readiness(dict(issue,**extra))['lane'],'reference_review')

    def test_live_expiry_down_revive_reselection_and_count_boundaries(self):
        self.assertEqual(len(mixed()),12)
        for c in mixed():
            with self.subTest(case=c['name']):self.assertTrue(verify_mixed(c,observe(c)[0])['verified'])
        c=mixed()[4];native=observe(c)[0]
        for fault in ('down','pool','members','state','time'):
            n=copy.deepcopy(native);o=n['random_cleanse']
            if fault=='down':o['calls'][1]['down']=[]
            elif fault=='pool':o['samples'][1]['pool']=[4]
            elif fault=='members':o['calls'][2]['after']['locked']=[]
            elif fault=='state':o['samples'][2]['after_sha256']='0'*64
            else:o['calls'][2]['time']=0
            with self.subTest(fault=fault),self.assertRaises(AssertionError):verify_mixed(c,n)

    def test_shared_input_layout_typed_rejections_and_retained_prefix(self):
        import importlib.util
        def load(name):
            s=importlib.util.spec_from_file_location('random_cleanse_test_'+name,ROOT/'research'/('verify-world-'+name+'-short.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
        m=load('random-cleanse');rows,data=m.prepare();self.assertEqual((len(rows),sum(d is None for _,_,d in rows)),(50,12))
        self.assertEqual(len(data),4+50*104400*4)
        for _,_,domain in rows[:38]:self.assertIn(domain[0]['contract']['owner'],range(5))
        for name,_,domain in rows[38:]:self.assertIsNone(domain);m.validate_rejection([64],name)
        old,before=load('burst1-ally-retention').prepare();current,after=load('random-cleanse-retention').prepare()
        self.assertEqual(len(current),175);self.assertEqual(sum(d is None for _,_,d in current),43);self.assertEqual(before[4:],after[4:4+len(before)-4])

    def test_exact_source_delta_rejects_broadened_eligibility_and_admission(self):
        from portable_definition_view_contract import verify as all_sources
        from portable_random_cleanse_source_contract import project_sources
        all_sources(ROOT);project_sources(ROOT)
        for name in ('gpu/recipient_runtime.slang','gpu/revival_runtime.slang'):
            source=(ROOT/name).read_text()
            with self.subTest(source=name),self.assertRaises(AssertionError):project_sources(ROOT,{name:source.replace('PORTABLE_RANDOM_CLEANSE','PORTABLE_RANDOM_CLEANSE_BYPASS',1)})
        source=(ROOT/'gpu/recipient_runtime.slang').read_text()
        for a,b in [('s.alive[slot]!=0','true'),('count<=5','true'),('commands[at+7]==0','true'),('alliedHasHarmful(s,who)','true')]:
            with self.subTest(change=a),self.assertRaises(AssertionError):project_sources(ROOT,{'gpu/recipient_runtime.slang':source.replace(a,b,1)})

    def test_budget_probes_exhaustion_empty_and_late_candidates(self):
        from portable_random_cleanse_budget_cases import fixtures as budget
        from portable_random_cleanse_budget_contracts import verify as check
        self.assertEqual(len(budget()),6)
        for c in budget():self.assertTrue(check(c,observe(c)[0])['verified'])
        c=budget()[1];n=observe(c)[0];n['random_cleanse']['samples'].pop()
        with self.assertRaises(AssertionError):check(c,n)

if __name__=='__main__':unittest.main()
