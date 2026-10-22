"""Fault injection for immutable proof packets, transport integrity and containment hooks."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('nikke_gpu_cli',ROOT/'scripts/nikke_gpu.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


class PacketTests(unittest.TestCase):
    def test_source_edit_during_native_baseline_cannot_publish_a_mixed_snapshot(self):
        import portable_backend
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve()
            for directory in ('gpu','app','scripts','research/upstream/nikke-calc-master/data'):(root/directory).mkdir(parents=True)
            (root/'gpu/main.slang').write_text('// kernel\n');(root/'app/model.py').write_text('before')
            (root/'scripts/nikke_gpu.py').write_text('# fixture CLI\n')
            upstream=root/'research/upstream/nikke-calc-master';(upstream/'LICENSE').write_text('fixture license');(upstream/'data/parsed_nikke.json').write_text('{}')
            def changed(*args):
                (root/'app/model.py').write_text('after')
                return dict(source_sha256={'gpu/main.slang':cli.sha((root/'gpu/main.slang').read_bytes())})
            with patch.object(cli,'ROOT',root),patch.object(portable_backend,'ROOT',root),\
                 patch.dict(cli.SUITES,fixture=dict(source='gpu/main.slang',golden='golden.json',tests=[])),\
                 patch.object(cli.subprocess,'check_output',return_value=b'gpu/main.slang\0app/model.py\0scripts/nikke_gpu.py\0'),\
                 patch.object(cli,'development_baseline',side_effect=changed),cli.forbid_gpu():
                with self.assertRaisesRegex(ValueError,'sources changed during native baseline'):
                    cli.make_package('fixture',root/'package.zip',develop=True)
            self.assertFalse((root/'package.zip').exists())

    def test_untracked_gpu_include_stops_packaging_before_native_baseline_or_archive(self):
        import portable_backend
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();(root/'gpu').mkdir();(root/'gpu/main.slang').write_text('#include "new.slang"\n')
            (root/'gpu/new.slang').write_text('// new shared helper\n');out=root/'package.zip'
            config=dict(source='gpu/main.slang',golden='golden.json',tests=[])
            with patch.object(cli,'ROOT',root),patch.object(portable_backend,'ROOT',root),patch.dict(cli.SUITES,fixture=config),\
                 patch.object(cli.subprocess,'check_output',return_value=b'gpu/main.slang\0'),\
                 patch.object(cli,'development_baseline',side_effect=AssertionError('Native baseline must not start')) as native,cli.forbid_gpu():
                with self.assertRaisesRegex(ValueError,'GPU source missing from tracked payload: gpu/new.slang'):
                    cli.make_package('fixture',out,develop=True)
            native.assert_not_called();self.assertFalse(out.exists())

    def test_package_gpu_source_requires_manifest_membership_and_matching_golden_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'gpu').mkdir();(root/'gpu/main.slang').write_text('#include "new.slang"\n');(root/'gpu/new.slang').write_text('// helper\n')
            names=['gpu/main.slang','gpu/new.slang'];records=cli.file_records(root,names)
            m=dict(schema=cli.SCHEMA,suite='fixture',purpose='development',files=records[:1],golden=dict(source_sha256={r['path']:r['sha256'] for r in records}))
            def saved():m['package_id']=cli.package_id(m);cli.write(root/'gpu-package.json',m)
            with patch.dict(cli.SUITES,fixture=dict(source='gpu/main.slang')),cli.forbid_gpu():
                saved()
                with self.assertRaisesRegex(ValueError,'GPU source missing from immutable payload'):cli.verify_package(root)
                m['files']=records;saved();self.assertEqual(cli.verify_package(root)['package_id'],m['package_id'])
                m['golden']['source_sha256']['gpu/new.slang']='0'*64;saved()
                with self.assertRaisesRegex(ValueError,'GPU source record differs'):cli.verify_package(root)

    def test_status_shows_child_and_parent_journals_without_promoting_stale_run_status(self):
        with tempfile.TemporaryDirectory() as folder:
            capture=Path(folder);cli.write(capture/'run.json',dict(status='preflight'))
            child=dict(stage='shared_gpu_execute',state='returned',pid=123)
            parent=dict(stage='shared_native_compare',state='entered',pid=456)
            (capture/'phases.jsonl').write_text(json.dumps(child)+'\n')
            (capture/'audit-phases.jsonl').write_text(json.dumps(parent)+'\n{"incomplete":')
            with cli.forbid_gpu():status=cli.capture_status(capture)
            self.assertEqual(status['run']['status'],'preflight')
            self.assertEqual(status['observations']['phases.jsonl']['last_event'],child)
            self.assertEqual(status['observations']['audit-phases.jsonl']['last_event'],parent)
            self.assertIsNone(status['result']);self.assertFalse(status['liveness_verified'])
            self.assertFalse(status['journal_integrity_verified'])
            failed=dict(calculation_verified=False,passed=False)
            cli.write(capture/'result.json',failed)
            self.assertEqual(cli.capture_status(capture)['result'],failed)

    def test_status_with_missing_journals_never_infers_a_stopped_or_successful_run(self):
        with tempfile.TemporaryDirectory() as folder:
            capture=Path(folder);cli.write(capture/'run.json',dict(status='preflight'))
            with cli.forbid_gpu():status=cli.capture_status(capture)
            self.assertEqual(status['observations'],{});self.assertIsNone(status['result'])
            self.assertFalse(status['liveness_verified'])

    def test_child_saves_transport_bytes_without_running_native_comparison(self):
        from types import SimpleNamespace
        import portable_backend
        with tempfile.TemporaryDirectory() as folder:
            capture=Path(folder);cli.write(capture/'start.json',{})
            data=b'literal packed input';raw=b'fake transport bytes'
            adapter=SimpleNamespace(suite=SimpleNamespace(INPUT=1))
            manifest=dict(suite='projectile',golden=dict(input_sha256=cli.sha(data)))
            def transport(*args,readback_path,**kwargs):
                self.assertEqual(readback_path,capture/'readback.bin');readback_path.write_bytes(raw)
                return None,dict(transport='fixture')
            def copied(*args,**kwargs):
                self.assertEqual((capture/'readback.bin').read_bytes(),raw)
                self.assertEqual(cli.load(capture/'evidence.json'),dict(transport='fixture'))
            with patch.object(cli,'verify_package',return_value=manifest),patch.object(cli,'open_suite',return_value=adapter),\
                 patch.object(cli,'prepare_entries',return_value=([],data)),patch.object(cli,'copy_generated',side_effect=copied),\
                 patch.object(cli,'compare_readback',side_effect=AssertionError('Child native comparison forbidden')) as compare,\
                 patch.object(portable_backend,'execute',side_effect=transport) as execute:
                cli.child(capture,'metal')
            execute.assert_called_once();compare.assert_not_called()
            self.assertFalse((capture/'comparison.json').exists())
            rows=[json.loads(line) for line in (capture/'phases.jsonl').read_text().splitlines()]
            self.assertEqual([(r['stage'],r['state']) for r in rows],[('shared_gpu_execute','entered'),('shared_gpu_execute','returned')])

    def test_run_uses_one_parent_audit_and_preserves_failed_calculation(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);capture=root/'capture'
            failed=dict(passed=False,calculation_verified=False,first_difference=dict(reason='Native differs'))
            with patch.object(cli,'ROOT',root),patch.object(cli,'verify_package',return_value=dict(suite='projectile',package_id='transport-test')),\
                 patch.object(cli,'SUITES',dict(projectile=dict(tests=[]))),patch.object(cli,'cpu_preflight',return_value=dict(passed=True)),\
                 patch.object(cli,'os',SimpleNamespace(**dict(vars(os),name='nt'))),\
                 patch.object(cli,'run_job',return_value=dict(passed=True)) as job,patch.object(cli,'copy_generated'),\
                 patch.object(cli,'audit_capture',return_value=failed) as audit:
                result=cli.run_capture(capture,'cuda',180)
            self.assertEqual(result,failed);job.assert_called_once()
            audit.assert_called_once_with(capture,verify_artifacts=False,record_comparison=True)
            self.assertFalse(cli.load(capture/'result.json')['passed'])
            self.assertTrue((root/'gpu-claimed-cuda.json').exists())
            self.assertTrue((capture/'artifacts.json').exists())

    def test_missing_metal_compiler_stops_before_native_and_gpu_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);capture=root/'capture'
            with patch.object(cli,'ROOT',root),patch.dict(os.environ,{'NIKKE_SLANG_ROOT':str(root/'missing')}),\
                 patch.object(cli,'verify_package',return_value=dict(suite='regression',purpose='development',package_id='missing-compiler')),\
                 patch.object(cli,'cpu_preflight',side_effect=AssertionError('Native work forbidden')) as native,\
                 patch.object(cli,'run_job',side_effect=AssertionError('GPU forbidden')) as job:
                with self.assertRaisesRegex(ValueError,'specify --slang-root'):
                    cli.run_capture(capture,'metal',180)
            native.assert_not_called();job.assert_not_called()
            self.assertFalse((root/'gpu-claimed-metal.json').exists())
            self.assertTrue((capture/'run.json').is_file())

    def test_status64_alone_cannot_satisfy_a_suite_execution_rejection_contract(self):
        import array
        from types import SimpleNamespace
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as folder:
            capture=Path(folder);data=bytes.fromhex('0100000007000000')
            words=array.array('I',[64]+[0]*786431)
            if sys.byteorder!='little':words.byteswap()
            raw=words.tobytes();native=dict(status=64)
            digest=lambda value:cli.sha(json.dumps(value,sort_keys=True).encode())
            reject=Mock(side_effect=ValueError('Cache was never warmed'))
            adapter=SimpleNamespace(suite=SimpleNamespace(INPUT=1),
                prepare=lambda:([('reject/late',[7],None)],data),validate_rejection=reject,
                cross=SimpleNamespace(digest=digest,normalized=cli.sha))
            golden=dict(input_sha256=cli.sha(data),source_sha256={},
                entries=[dict(name='reject/late',input_sha256=cli.sha(data[4:]),native_sha256=digest(native))])
            (capture/'input.bin').write_bytes(data);(capture/'readback.bin').write_bytes(raw)
            cli.write(capture/'evidence.json',dict(input_sha256=cli.sha(data),output_sha256=cli.sha(raw),source_sha256={},gpu_execution_verified=True,backend='metal'))
            for suffix in ('cu','metal'):(capture/('generated.'+suffix)).write_bytes(b'generated')
            m=dict(purpose='development',suite='lazy-bank',golden=golden)
            result=cli.compare_readback(m,capture,adapter)
            self.assertFalse(result['calculation_verified']);self.assertIn('never warmed',result['mismatches'][0]['reason'])
            reject.assert_called_once()
            reject.side_effect=None
            self.assertTrue(cli.compare_readback(m,capture,adapter)['calculation_verified'])

    def test_controller_smoke_never_prepares_native_battles_or_runs_numeric_groups(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as folder:
            capture=Path(folder)/'smoke'
            def job(capture,*args,**kwargs):
                cli.write(capture/'smoke.json',dict(pid=123,ppid=12,gpu_calls=0))
                return dict(passed=True)
            with patch.object(cli,'verify_package',return_value=dict(suite='regression',purpose='sealed',package_id='smoke-test')),\
                 patch.object(cli,'os',SimpleNamespace(**dict(vars(os),name='posix'))),\
                 patch.object(cli,'cpu_preflight',side_effect=AssertionError('Native battle forbidden')) as native,\
                 patch.object(cli.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=b'',stderr=b'')) as tests,\
                 patch.object(cli,'run_job',side_effect=job):
                result=cli.run_capture(capture,'cuda',30,smoke=True)
            native.assert_not_called()
            self.assertTrue(result['smoke_verified']);self.assertFalse(result['calculation_verified'])
            self.assertEqual([c.args[0][-1] for c in tests.call_args_list],cli.SMOKE_TESTS)
            self.assertEqual(cli.load(capture/'cpu.json')['native_oracles'],0)
            self.assertIn('test_portable_compile_cache.py',cli.SMOKE_TESTS)
            self.assertIn('test_portable_cuda_artifact.py',cli.SMOKE_TESTS)

    def test_missing_smoke_test_cannot_silently_pass_with_zero_discovered_tests(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(cli,'verify_package',return_value=dict(suite='regression',purpose='sealed',package_id='missing-test')),\
                 patch.object(cli,'SMOKE_TESTS',['missing-required-test.py']),\
                 patch.object(cli,'cpu_preflight',side_effect=AssertionError('Native battle forbidden')),\
                 patch.object(cli.subprocess,'run') as tests,patch.object(cli,'run_job') as job:
                with self.assertRaisesRegex(ValueError,'CPU test file missing'):
                    cli.run_capture(Path(folder)/'capture','cuda',30,smoke=True)
            tests.assert_not_called();job.assert_not_called()

    def test_windows_temporary_environment_reaches_child_without_changing_parent(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);parent=dict(os.environ,TEMP='unwritable-default',TMP='unwritable-default',
                                        TMPDIR='unwritable-default',__PYVENV_LAUNCHER__='stale')
            before=dict(parent)
            with patch.object(cli,'os',SimpleNamespace(name='nt',environ=parent)):
                env=cli.validation_environment(root)
                self.assertEqual(cli.validation_environment(root),env)
            self.assertEqual(parent,before);self.assertNotIn('__PYVENV_LAUNCHER__',env)
            temporary=(root/'temporary').resolve()
            self.assertTrue(temporary.is_dir())
            self.assertTrue(all(env[k]==str(temporary) for k in ('TEMP','TMP','TMPDIR')))
            child=subprocess.run([sys.executable,'-c','import pathlib,tempfile;print(pathlib.Path(tempfile.gettempdir()).resolve())'],
                                 env=env,capture_output=True,text=True,check=True)
            self.assertEqual(child.stdout.strip(),str(temporary))

    def test_required_shared_auditor_helpers_are_available_before_native_work(self):
        from portable_typed_cuda_proof_audit import verify_cpu_gpu_calls
        from portable_phase_audit import verify_cuda_trace
        verify_cpu_gpu_calls(dict(build=0,execute=0))
        with self.assertRaises(AssertionError):verify_cpu_gpu_calls(dict(build=1,execute=0))
        self.assertFalse(verify_cuda_trace([]))

    def test_paths_reject_traversal_windows_drives_and_backslashes(self):
        for path in ('../x','/x','C:/x','a/../x','a\\x','a//b','a/./b'):
            with self.subTest(path=path),self.assertRaises(ValueError):cli.safe_name(path)
        self.assertEqual(cli.safe_name('research/report.json'),'research/report.json')

    def test_collection_export_import_preserves_exact_bytes_without_raw(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);capture=root/'capture';capture.mkdir()
            raw=b'{"passed":true}\r\n';(capture/'evidence.json').write_bytes(raw)
            (capture/'input.bin').write_bytes(b'private raw')
            receipt=cli.collect(capture,capture/'artifacts.json')
            self.assertEqual([r['path'] for r in receipt['files']],['evidence.json'])
            archive=root/'results.zip';cli.export_results(capture,archive)
            result=cli.import_results(archive,root/'import')
            self.assertEqual((root/'import/evidence.json').read_bytes(),raw)
            self.assertEqual(result['gpu_calls'],0);self.assertFalse((root/'import/input.bin').exists())

    def test_export_rejects_changed_original_result(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'result.json').write_text('{}')
            cli.collect(root,root/'artifacts.json');(root/'result.json').write_text('{"passed":true}')
            with self.assertRaises(ValueError):cli.export_results(root,root/'bad.zip')
            self.assertFalse((root/'bad.zip').exists())

    def test_import_rejects_tampering_before_destination_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);receipt=dict(files=[dict(path='x.json',bytes=2,sha256=cli.sha(b'{}'))])
            with zipfile.ZipFile(root/'bad.zip','w') as z:
                z.writestr('artifacts.json',json.dumps(receipt));z.writestr('x.json','[]')
            with self.assertRaises(ValueError):cli.import_results(root/'bad.zip',root/'dest')
            self.assertFalse((root/'dest').exists())

    def test_import_rejects_unlisted_file_and_traversal(self):
        for extra in ('unlisted.json','../escape'):
            with self.subTest(extra=extra),tempfile.TemporaryDirectory() as folder:
                root=Path(folder)
                with zipfile.ZipFile(root/'bad.zip','w') as z:
                    z.writestr('artifacts.json',json.dumps(dict(files=[])));z.writestr(extra,'x')
                with self.assertRaises(ValueError):cli.import_results(root/'bad.zip',root/'dest')
                self.assertFalse((root/'dest').exists())

    def test_unpack_unknown_suite_is_transfer_only_and_never_executes_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);raw=b'raise AssertionError("Must never execute during unpack")'
            row=dict(path='scripts/future.py',bytes=len(raw),sha256=cli.sha(raw))
            m=dict(schema=cli.SCHEMA,suite='future-suite',files=[row],golden={})
            m['package_id']=cli.package_id(m)
            with zipfile.ZipFile(root/'future.zip','w') as z:
                z.writestr('gpu-package.json',json.dumps(m));z.writestr(row['path'],raw)
            self.assertEqual(cli.unpack(root/'future.zip',root/'dest'),m['package_id'])
            self.assertEqual((root/'dest/scripts/future.py').read_bytes(),raw)
            with self.assertRaises(ValueError):cli.verify_package(root/'dest')

    def test_unknown_schema_is_rejected_before_creating_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);m=dict(schema=cli.SCHEMA+1,suite='future',files=[])
            m['package_id']=cli.package_id(m)
            with zipfile.ZipFile(root/'future.zip','w') as z:z.writestr('gpu-package.json',json.dumps(m))
            with self.assertRaises(ValueError):cli.unpack(root/'future.zip',root/'dest')
            self.assertFalse((root/'dest').exists())

    def test_partial_failure_capture_preserves_generated_and_binary_artifacts(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);capture=root/'capture';capture.mkdir()
            build=root/'research/portable-build';build.mkdir(parents=True)
            (build/'world_projectile_entry.cu').write_bytes(b'cuda source')
            (build/'world_projectile_entry.cubin').write_bytes(b'\x7fELF\x00binary')
            with patch.object(cli,'ROOT',root):cli.copy_generated(capture,'readiness',partial=True)
            self.assertEqual((capture/'compiled.cubin').read_bytes(),b'\x7fELF\x00binary')
            self.assertEqual((capture/'generated.cu').read_bytes(),b'cuda source')
            self.assertFalse((capture/'generated.metal').exists())

    def test_file_records_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'a').write_text('{}')
            try:(root/'b').symlink_to(root/'a')
            except OSError:self.skipTest('symlink privilege unavailable')
            with self.assertRaises(ValueError):cli.file_records(root,['b'])

    def test_package_identity_covers_golden_and_source_manifest(self):
        m=dict(schema=1,suite='projectile',files=[],golden=dict(output_sha256='good'))
        identity=cli.package_id(m);m['package_id']=identity
        self.assertEqual(cli.package_id(m),identity)
        m['golden']['output_sha256']='bad';self.assertNotEqual(cli.package_id(m),identity)

    def test_collect_and_import_do_not_import_gpu_backend(self):
        script="""import importlib.util,sys,tempfile,pathlib
s=importlib.util.spec_from_file_location('cli',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 p=pathlib.Path(d);(p/'result.json').write_text('{}');m.collect(p,p/'artifacts.json');m.export_results(p,p/'r.zip');m.import_results(p/'r.zip',p/'import')
assert 'portable_backend' not in sys.modules
"""
        result=subprocess.run([sys.executable,'-c',script,str(ROOT/'scripts/nikke_gpu.py')],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)


class BoundedHooks(unittest.TestCase):
    def module(self):return cli.bounded_module()

    def test_after_wait_runs_inside_wrapper_after_child_exit(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);events=[]
            def before():
                events.append('before');self.assertFalse((root/'start.json').exists())
            def after():
                events.append('after');self.assertTrue((root/'done').exists())
                self.assertFalse((root/'execution.json').exists())
            command=[sys.executable,'-c',"import pathlib,time,sys;p=pathlib.Path(sys.argv[1]);\nwhile not (p/'start.json').exists():time.sleep(.01)\n(p/'done').write_text('done')",str(root)]
            facts=self.module().run_bounded(command,root,10,before_gate=before,after_wait=after)
            self.assertTrue(facts['passed']);self.assertEqual(events,['before','after']);self.assertIsNone(facts['observation_error'])

    def test_snapshot_failure_cannot_skip_cleanup_or_erase_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            def fail():raise OSError('snapshot unavailable')
            facts=self.module().run_bounded([sys.executable,'-c','pass'],root,10,after_wait=fail)
            self.assertEqual(facts['final_child_exit_code'],0);self.assertIsNone(facts['cleanup_error'])
            self.assertIn('snapshot unavailable',facts['observation_error']);self.assertTrue((root/'execution.json').exists())

    def test_before_gate_failure_never_releases_child_and_still_observes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);observed=[]
            def fail():raise RuntimeError('preflight failed')
            facts=self.module().run_bounded([sys.executable,'-c','import time;time.sleep(30)'],root,1,before_gate=fail,after_wait=lambda:observed.append(1))
            self.assertFalse((root/'start.json').exists());self.assertFalse(facts['passed'])
            self.assertIsNotNone(facts['final_child_exit_code']);self.assertEqual(observed,[1])

    def test_timeout_still_observes_after_cleanup(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);observed=[]
            facts=self.module().run_bounded([sys.executable,'-c','import time;time.sleep(30)'],root,1,after_wait=lambda:observed.append(1))
            self.assertTrue(facts['timed_out']);self.assertIsNone(facts['cleanup_error']);self.assertEqual(observed,[1])


class TraceTests(unittest.TestCase):
    def rows(self):
        rows=[]
        for stage in ('nvrtcCompileProgram','cuLaunchKernel','cuCtxSynchronize','cuMemcpyDtoH_v2'):
            rows.extend([dict(stage=stage,state='entered',pid=7),dict(stage=stage,state='returned',return_code=0,pid=7)])
        for i,row in enumerate(rows):row['monotonic_ns']=i
        return rows

    def test_success_requires_ordered_complete_native_returns(self):
        from portable_phase_audit import verify_cuda_trace
        rows=self.rows();self.assertTrue(verify_cuda_trace(rows,pid=7))
        self.assertFalse(verify_cuda_trace(rows[:-1],pid=7))
        rows[3]['return_code']=700;self.assertFalse(verify_cuda_trace(rows,pid=7))

    def test_wrong_pid_and_duplicate_launch_cannot_pass(self):
        from portable_phase_audit import verify_cuda_trace
        rows=self.rows();self.assertFalse(verify_cuda_trace(rows,pid=8))
        rows.extend([dict(rows[2],monotonic_ns=8),dict(rows[3],monotonic_ns=9)])
        self.assertFalse(verify_cuda_trace(rows,pid=7))

    def test_reordered_native_stages_and_reversed_clock_cannot_pass(self):
        from portable_phase_audit import verify_cuda_trace
        rows=self.rows();rows[0:2],rows[2:4]=rows[2:4],rows[0:2]
        for i,row in enumerate(rows):row['monotonic_ns']=i
        self.assertFalse(verify_cuda_trace(rows,pid=7))
        rows=self.rows();rows[-1]['monotonic_ns']=0;self.assertFalse(verify_cuda_trace(rows,pid=7))


class CaptureAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        cli.write(self.root/'run.json',dict(package_id='fixture',backend='cuda'))
        cli.write(self.root/'execution.json',dict(passed=True,wait_completed_unix_ns=1_000_000_000,observation_error=None))
        cli.write(self.root/'evidence.json',dict(backend='cuda',transport=dict(command_status='completed',cases=63)))
        (self.root/'readback.bin').write_bytes(b'isolated comparator fixture')
        rows=TraceTests().rows()
        for i,row in enumerate(rows):row['wall_time_ns']=200+i
        (self.root/'phases.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
        pre=dict(child_pid=7,child_ppid=17,job_members=[7],child_creation_filetime_ticks='100',observed_unix_ns=100)
        post=dict(pre,job_members=[],observed_unix_ns=300)
        cli.write(self.root/'job.json',dict(records=[dict(child_pid=7,wrapper_pid=17,pre_gate_verified=True,inspection_error=None,pre_gate=pre,post_wait=post)]))
        self.observation=dict(before=dict(processes=[],service_status='absent',observed_unix_ns=0),after=dict(processes=[],service_status='absent',observed_unix_ns=2_000_000_000))
        self.save_observation()

    def save_observation(self):
        from windows_validation_observer import compare_snapshots
        self.observation['comparison']=compare_snapshots(self.observation['before'],self.observation['after'])
        cli.write(self.root/'observation.json',self.observation)

    def audit(self,*,comparison=None,error=None,record=False):
        comparison=comparison if comparison is not None else dict(calculation_verified=True,mismatches=[])
        with patch.object(cli,'verify_package',return_value=dict(package_id='fixture',suite='projectile',golden=dict(entries=[{}]*63))),patch.object(cli,'compare_readback',return_value=comparison,side_effect=error) as compare:
            result=cli.audit_capture(self.root,verify_artifacts=False,record_comparison=record)
        compare.assert_called_once()
        return result

    def test_parent_records_fresh_comparison_once_and_keeps_transport_trace_separate(self):
        original=(self.root/'phases.jsonl').read_bytes()
        cli.write(self.root/'comparison.json',dict(calculation_verified=False,stale=True))
        comparison=dict(calculation_verified=True,mismatches=[],entries=[dict(native_sha256='fresh')])
        result=self.audit(comparison=comparison,record=True)
        self.assertTrue(result['passed'])
        self.assertEqual(cli.load(self.root/'comparison.json'),comparison)
        self.assertEqual((self.root/'phases.jsonl').read_bytes(),original)
        rows=[json.loads(line) for line in (self.root/'audit-phases.jsonl').read_text().splitlines()]
        self.assertEqual([(r['stage'],r['state']) for r in rows],[('shared_native_compare','entered'),('shared_native_compare','returned')])

    def test_successful_transport_cannot_hide_mismatch_or_comparator_exception(self):
        for error in (None,ValueError('Saved raw changed')):
            with self.subTest(error=error):
                cli.write(self.root/'comparison.json',dict(calculation_verified=True,stale=True))
                mismatch=dict(calculation_verified=False,mismatches=[dict(reason='Native differs')])
                result=self.audit(comparison=mismatch,error=error,record=True)
                self.assertFalse(result['passed']);self.assertFalse(result['calculation_verified'])
                saved=cli.load(self.root/'comparison.json');self.assertFalse(saved['calculation_verified'])
                self.assertTrue(cli.load(self.root/'execution.json')['passed'])
                self.assertTrue((self.root/'readback.bin').exists())
                if error:self.assertIn('Saved raw changed',saved['comparison_error'])
                else:self.assertEqual(result['first_difference'],mismatch['mismatches'][0])

    def test_independent_audit_never_reuses_or_overwrites_comparison_receipt(self):
        original=b'{"calculation_verified":false,"stale":true}\n'
        (self.root/'comparison.json').write_bytes(original)
        self.assertTrue(self.audit()['passed'])
        self.assertEqual((self.root/'comparison.json').read_bytes(),original)
        self.assertFalse((self.root/'audit-phases.jsonl').exists())

    def test_missing_readback_cannot_keep_an_old_success_receipt(self):
        (self.root/'readback.bin').unlink()
        cli.write(self.root/'comparison.json',dict(calculation_verified=True))
        with patch.object(cli,'verify_package',return_value=dict(package_id='fixture',suite='projectile',golden=dict(entries=[{}]*63))),patch.object(cli,'compare_readback') as compare:
            result=cli.audit_capture(self.root,verify_artifacts=False,record_comparison=True)
        compare.assert_not_called();self.assertFalse(result['calculation_verified'])
        self.assertEqual(cli.load(self.root/'comparison.json'),dict(calculation_verified=False,comparison_error='Missing readback.bin'))

    def test_calculation_and_environment_success_remain_distinct(self):
        result=self.audit();self.assertTrue(result['passed']);self.assertTrue(result['calculation_verified'])
        self.observation['after']['observed_unix_ns']=32_000_000_001;self.save_observation()
        result=self.audit();self.assertTrue(result['calculation_verified']);self.assertFalse(result['preservation_verified']);self.assertFalse(result['passed'])

    def test_missing_existing_process_never_becomes_environment_success(self):
        self.observation['before']['processes']=[dict(pid=99,path='C:/python.exe',creation_filetime_ticks='90',role='unrelated')]
        self.save_observation();result=self.audit()
        self.assertTrue(result['calculation_verified']);self.assertFalse(result['preservation_verified']);self.assertFalse(result['passed'])

    def test_foreign_api_pid_cannot_prove_contained_calculation(self):
        rows=[dict(r,pid=8) for r in TraceTests().rows()]
        for i,row in enumerate(rows):row['wall_time_ns']=200+i
        (self.root/'phases.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
        result=self.audit();self.assertFalse(result['containment_verified']);self.assertFalse(result['calculation_verified'])

    def test_post_snapshot_failure_cannot_hide_behind_successful_gpu(self):
        self.observation.pop('after');self.observation.pop('comparison')
        cli.write(self.root/'observation.json',self.observation)
        result=self.audit();self.assertTrue(result['calculation_verified']);self.assertFalse(result['preservation_verified']);self.assertFalse(result['passed'])


if __name__=='__main__':unittest.main()
