"""Synthetic capture boundaries; no CUDA device or real Windows Job."""
import json,os,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_prepared_audit as audit
import test_portable_prepared_execution as fixture
import test_portable_generation_cache as generation_fixture
from windows_validation_observer import compare_snapshots


class PreparedAuditTests(unittest.TestCase):
    def setUp(self):
        f=fixture.PreparedExecutionTests();f.setUp();self.addCleanup(f.doCleanups);self.f=f
        f.child();self.capture=f.capture;self.cli=f.cli;self.m=f.manifest
        rows=[json.loads(line) for line in (self.capture/'phases.jsonl').read_text().splitlines()]
        self.pid=rows[0]['pid'];first=rows[0]['wall_time_ns'];last=rows[-1]['wall_time_ns']
        self.save('job.json',dict(records=[dict(child_pid=self.pid,wrapper_pid=777,pre_gate_verified=True,inspection_error=None,
            pre_gate=dict(child_pid=self.pid,child_ppid=777,job_members=[self.pid],child_creation_filetime_ticks='identity',observed_unix_ns=first-1,job_memory_limit_bytes=2147483648),
            post_wait=dict(child_pid=self.pid,child_ppid=777,job_members=[],child_creation_filetime_ticks='identity',observed_unix_ns=last+1,job_memory_limit_bytes=2147483648))]))
        self.save('execution.json',dict(passed=True,timed_out=False,child_exit_code=0,final_child_exit_code=0,below_normal_priority=True,timeout_seconds=60,error=None,cleanup_error=None,observation_error=None,wait_completed_unix_ns=last+2))
        python=str(audit.base_python())
        self.save('command.json',dict(base_python=python,argv=[python,str(self.cli.ROOT/'scripts/nikke_gpu.py'),'_prepared_child','--capture',str(self.capture),'--claim-sha256',f.claim_sha],cwd=str(self.cli.ROOT),shell=False,timeout_seconds=60))
        before=dict(processes=[],service_status='unverified',observed_unix_ns=first-2)
        after=dict(processes=[],service_status='unverified',observed_unix_ns=last+3)
        self.save('observation.json',dict(before=before,after=after,comparison=compare_snapshots(before,after)))
        for name in ('runtime.json','generation-cache.json','generated.cu.reflection.json','generated.metal.reflection.json'):self.save(name,{})
        (self.capture/'generated.metal').write_bytes(b'metal fixture')
        evidence=self.cli.load(self.capture/'evidence.json');evidence['transport']['compile_artifact']=f.f.f.cert['linked_receipt'];self.save('evidence.json',evidence)
        self.save('artifacts.json',dict(files=self.cli.file_records(self.capture,['dispatch.json','run.json','execution.json','job.json','observation.json','evidence.json'])))
    def save(self,name,value):(self.capture/name).write_text(json.dumps(value))
    def change(self,name,**values):
        value=self.cli.load(self.capture/name);value.update(values);self.save(name,value)
    def envelope(self):return audit.envelope(self.cli,self.m,self.capture,self.f.claim_sha)
    def test_real_shared_job_and_trace_parsers_keep_unknown_service_false(self):
        _,r=self.envelope();self.assertTrue(r['transport_core_verified']);self.assertTrue(r['containment_verified'])
        self.assertFalse(r['preservation_verified']);self.assertFalse(r['transport_verified']);self.assertFalse(r['calculation_verified']);self.assertFalse(r['passed'])
        self.assertEqual((self.capture/'input.bin').read_bytes(),self.f.f.f.input)
    def test_failed_boolean_exit_and_excessive_budget_are_rejected(self):
        for fields in (dict(child_exit_code=False),dict(timeout_seconds=61),dict(timed_out=True),dict(observation_error='failed')):
            old=(self.capture/'execution.json').read_bytes()
            with self.subTest(fields=fields):
                self.change('execution.json',**fields)
                with self.assertRaisesRegex(ValueError,'within its bound'):self.envelope()
            (self.capture/'execution.json').write_bytes(old)
    def test_job_limit_and_native_trace_cannot_be_replaced_by_success_flags(self):
        value=self.cli.load(self.capture/'job.json');value['records'][0]['post_wait']['job_memory_limit_bytes']=1073741824;self.save('job.json',value)
        with self.assertRaisesRegex(ValueError,'Job/native trace'):self.envelope()
    def test_child_marker_and_retained_failure_prevent_promotion(self):
        self.change('prepared-child-started.json',pid=12345)
        with self.assertRaisesRegex(ValueError,'ownership marker'):self.envelope()
        self.change('prepared-child-started.json',pid=self.pid);self.save('prepared-child-failure.json',dict(error='interrupted'))
        with self.assertRaisesRegex(ValueError,'remain failed'):self.envelope()
    def test_late_or_forged_observation_is_rejected(self):
        o=self.cli.load(self.capture/'observation.json');o['after']['observed_unix_ns']+=31_000_000_000;self.save('observation.json',o)
        with self.assertRaisesRegex(ValueError,'immediate observation'):self.envelope()
    def test_foreign_command_or_missing_ownership_journal_is_rejected(self):
        old=(self.capture/'command.json').read_bytes();self.change('command.json',shell=True)
        with self.assertRaisesRegex(ValueError,'command identity'):self.envelope()
        (self.capture/'command.json').write_bytes(old)
        rows=[json.loads(line) for line in (self.capture/'phases.jsonl').read_text().splitlines()]
        (self.capture/'phases.jsonl').write_text('\n'.join(json.dumps(r) for r in rows if r['stage']!='prepared_child_ownership')+'\n')
        with self.assertRaisesRegex(ValueError,'journal incomplete'):self.envelope()
    def test_ownership_changed_after_dispatch_is_rejected(self):
        (self.f.f.f.tx/'gpu-execution-claimed.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'mirrors'):self.envelope()
    def compare(self,mutate=None,failed=False):
        # Only native numeric comparison is doubled here; real ownership,
        # Handoff, capture hashes, Job and trace parsers still execute.
        namespace=dict(self.cli.compare_readback.__globals__)
        exec('def compare(m,capture,*,case_indices):\n audit_generation_capture(m,capture)\n audit_saved_linked_artifact(m,capture,load(capture/"evidence.json")["transport"]["compile_artifact"])\n return callback(m,capture,case_indices)\n',namespace)
        def callback(m,capture,indices):
            if mutate:mutate()
            return dict(calculation_verified=False,comparison_subset_verified=not failed,mismatches=['different'] if failed else [],case_indices=indices,audit_gpu_calls=0)
        namespace['callback']=callback
        cli=SimpleNamespace(**{**vars(self.cli),'compare_readback':namespace['compare']})
        previous=(namespace['audit_generation_capture'],namespace['audit_saved_linked_artifact'])
        try:
            with patch.object(audit,'generation',return_value=dict(verified=True)),patch.object(audit,'current_pid',return_value=self.pid+1):
                return audit.compare_group(cli,self.capture,self.f.claim_sha,[0])
        finally:self.assertEqual(previous,(namespace['audit_generation_capture'],namespace['audit_saved_linked_artifact']))
    def test_frozen_link_adapter_preserves_partial_scope_and_restores_callbacks(self):
        r=self.compare();self.assertTrue(r['comparison']['comparison_subset_verified']);self.assertFalse(r['audit']['calculation_verified'])
        self.assertFalse(r['live_parent_receipt_present']);self.assertEqual(self.f.gpu_calls,1)
    def test_comparison_failure_and_capture_mutation_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'partial native comparison'):self.compare(failed=True)
        with self.assertRaises(ValueError):self.compare(mutate=lambda:(self.capture/'readback.bin').write_bytes(b'changed'))
    def test_frozen_cubin_mismatch_rejected_before_comparison(self):
        (self.capture/'compiled.cubin').write_bytes(b'not the saved image')
        with self.assertRaisesRegex(ValueError,'CUBIN differs'):self.compare()
    def test_owning_gpu_process_cannot_certify_independence(self):
        with self.assertRaisesRegex(ValueError,'Fresh independent CPU process'):
            audit.compare_group(self.cli,self.capture,self.f.claim_sha,[0])
    def test_partial_indices_must_be_explicit_unique_and_in_range(self):
        for indices in (None,[],[True],[0,0],[1]):
            with self.subTest(indices=indices),self.assertRaises(ValueError):
                audit.compare_group(self.cli,self.capture,self.f.claim_sha,indices)
    def test_existing_cli_group_route_uses_snapshot_audit_without_legacy_admission(self):
        result=dict(audit=dict(calculation_verified=False),comparison=dict(comparison_subset_verified=True))
        with patch.object(audit,'compare_group',return_value=result) as compare:
            actual=self.cli.audited_battle_comparison_group(self.cli,self.capture,[0],'cuda')
        self.assertEqual(actual,(result['audit'],result['comparison']))
        compare.assert_called_once_with(self.cli,self.capture,self.f.claim_sha,[0])


class PreparedGenerationAuditTests(unittest.TestCase):
    def setUp(self):
        f=generation_fixture.GenerationCacheTests();f.setUp();self.addCleanup(f.doCleanups);self.f=f
        f.build();paths,hashes=f.build(True);self.capture=next(iter(paths.values())).parent
        self.cli=SimpleNamespace(load=lambda p:json.loads(Path(p).read_bytes()))
        for target,suffix in (('cuda','cu'),('metal','metal')):
            for ext in ('','.reflection.json'):(self.capture/('generated.'+suffix+ext)).write_bytes(Path(str(paths[target])+ext).read_bytes())
        self.receipt=f.receipt();(self.capture/'generation-cache.json').write_text(json.dumps(self.receipt))
        self.runtime=dict(generation_cache_enabled=True,generation_cache_required=True,cuda_artifact_kind='cubin')
        (self.capture/'runtime.json').write_text(json.dumps(self.runtime));self.m=dict(golden=dict(source_sha256=hashes))
        self.rows=[dict(stage='slang_generation_cache',state='verified',receipt=self.receipt)]
    def check(self):return audit.generation(self.cli,self.m,self.capture,self.rows)
    def test_existing_reflection_and_full_artifact_verifier_is_used(self):
        self.assertTrue(self.check()['verified']);self.assertEqual(self.f.calls,['cuda','metal'])
        (self.capture/'generated.cu.reflection.json').write_text('{}')
        with self.assertRaises(ValueError):self.check()
    def test_cache_miss_or_compiler_trace_cannot_pass(self):
        self.rows.append(dict(stage='slang_compiler',state='entered'))
        with self.assertRaisesRegex(ValueError,'invoked Slang'):self.check()
        self.rows.pop();self.receipt['hit']=False;(self.capture/'generation-cache.json').write_text(json.dumps(self.receipt))
        with self.assertRaisesRegex(ValueError,'paired generation hit'):self.check()


if __name__=='__main__':unittest.main()
