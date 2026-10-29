"""Support witnesses cannot pass with missing casts, reentry, or an absent actor."""
import copy,hashlib,importlib.util,json,sys,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('support_contract_test',ROOT/'research/verify-original-catalogue-support.py')
support=importlib.util.module_from_spec(spec);spec.loader.exec_module(support)

class SupportContractTests(unittest.TestCase):
    def test_real_cli_selection_and_wire_pack_without_battle(self):
        import nikke_gpu
        manifest=dict(suite='original-catalogue-support',purpose='development',selected_cases=[])
        adapter=nikke_gpu.open_suite(manifest)
        with patch('calculator.timeline.simulate',side_effect=AssertionError('No battle during packing')):
            rows,data=nikke_gpu.prepare_entries(adapter,manifest)
        self.assertEqual([r[0] for r in rows],list(support.COHORT))
        self.assertEqual(len(data),4+2*adapter.suite.INPUT*4)
        self.assertTrue(all(r[2] is not None for r in rows))

    def test_frozen_cohort_reuses_existing_complete_catalogue_and_source(self):
        import nikke_gpu
        config=nikke_gpu.SUITES['original-catalogue-support'];parent=nikke_gpu.SUITES['original-catalogue']
        from portable_recipient_order_observation import SOURCE,check_layout
        self.assertEqual(config['source'],SOURCE);check_layout(ROOT)
        self.assertEqual(set(config['frozen_cases']),set(support.COHORT))
        self.assertEqual((config['inputs'],config['native']),(2,2));self.assertFalse(config['selection_required'])
        self.assertIn('research/upstream/nikke-calc-master/docs/IMPL-STATUS.md',config['upstream_documents'])
        self.assertIs(support.NATIVE_COMPARISON_CONTEXT,support.base.NATIVE_COMPARISON_CONTEXT)
        for names in ([],[next(iter(support.COHORT))],list(support.COHORT)*2):
            with self.assertRaises(ValueError):support.prepare_selected(names)

    def test_burst_witness_rejects_missing_or_reordered_reentry_and_owner(self):
        for name,expected in support.COHORT.items():
            trace=[dict(event=event,owner=owner) for event,owner in expected['casts']]
            support.verify_casts(name,trace)
            for fault in ('missing','owner','stage','order'):
                bad=copy.deepcopy(trace)
                if fault=='missing':bad.pop(0)
                elif fault=='owner':bad[0]['owner']=4
                elif fault=='stage':bad[0]['event']=3
                else:bad[:2]=reversed(bad[:2])
                with self.subTest(name=name,fault=fault),self.assertRaises(AssertionError):support.verify_casts(name,bad)

    def test_native_witness_rejects_uncharged_party_wrong_stage_and_no_own_shots(self):
        for name,expected in support.COHORT.items():
            native=dict(burst_controls=dict(ticks=[dict(stages=[expected['stage']],cycles=1)]),coordinate_typed_weapon=dict(attacks=[dict(owner=0)]))
            self.assertIs(support.verify_native(dict(name=name),native),native)
            for fault in ('cycle','stage','shots'):
                bad=copy.deepcopy(native)
                if fault=='cycle':bad['burst_controls']['ticks'][0]['cycles']=0
                elif fault=='stage':bad['burst_controls']['ticks'][0]['stages'][0]=3
                else:bad['coordinate_typed_weapon']['attacks']=[dict(owner=1)]
                with self.subTest(name=name,fault=fault),self.assertRaises(AssertionError):support.verify_native(dict(name=name),bad)

    def test_reentry_requires_the_shared_runtime_reentry_event(self):
        name=next(n for n in support.COHORT if '티아' in n)
        trace=[dict(event=e,owner=o) for e,o in support.COHORT[name]['casts']]
        self.assertEqual(trace[1],dict(event=7,owner=3))
        trace[1]['event']=1
        with self.assertRaises(AssertionError):support.verify_casts(name,trace)
        self.assertIn('stage+(s.reentrySlot != 0 ? 6 : 0)',(ROOT/'gpu/combat_runtime.slang').read_text())

    def test_readiness_document_is_required_before_native_preparation(self):
        from portable_cpu_tests import AUDIT_FILES,validate_dependency_files
        pattern='test_portable_readiness_semantics.py'
        name='research/upstream/nikke-calc-master/docs/IMPL-STATUS.md'
        self.assertIn(name,AUDIT_FILES[pattern])
        with self.assertRaisesRegex(ValueError,'missing from immutable payload'):
            validate_dependency_files(ROOT,[pattern],included=set(AUDIT_FILES[pattern])-{name})

    def test_sealed_inputs_source_and_cache_only_profile_are_the_same_contract(self):
        import nikke_gpu as cli
        from portable_backend import source_hashes
        config=cli.SUITES['original-catalogue-support'];cached=cli.SUITES['original-catalogue-support-cache-only']
        self.assertFalse(config['development_only']);self.assertTrue(cached['require_paired_generation'])
        self.assertEqual(cached['cuda_cache_profile'],'compile-cache-only-v1')
        for key in ('script','source','golden','frozen_cases','inputs','native','input_words','output_words'):
            self.assertEqual(config[key],cached[key])
        m=dict(suite='original-catalogue-support',purpose='sealed',selected_cases=[])
        adapter=cli.open_suite(m);rows,data=cli.prepare_entries(adapter,m)
        raw=(ROOT/config['golden']).read_bytes();golden=json.loads(raw)
        self.assertEqual(hashlib.sha256(data).hexdigest(),golden['input_sha256'])
        self.assertEqual([r[0] for r in rows],[r['name'] for r in golden['entries']])
        self.assertEqual(source_hashes(config['source']),golden['source_sha256'])
        certificate=json.loads((ROOT/cli.SUITES[cli.compiler_alias('original-catalogue-support')]['golden']).read_text())
        self.assertEqual(certificate['baseline_golden_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(certificate['source_sha256'],golden['source_sha256'])
        self.assertEqual(certificate['generated_normalized'],golden['generated_normalized'])
        self.assertFalse(certificate['calculation_verified']);self.assertFalse(certificate['executable_battle_verified'])
        receipt=json.loads((ROOT/'tests/fixtures/original-catalogue-support-independent-v1.json').read_text())
        self.assertEqual((receipt['input_count'],receipt['native_cases'],receipt['gpu_calls']),(2,2,0))
        self.assertFalse(receipt['live_parent_receipt_present'])
        for key in ('input_sha256','output_sha256'):self.assertEqual(receipt[key],golden[key])

if __name__=='__main__':unittest.main()
