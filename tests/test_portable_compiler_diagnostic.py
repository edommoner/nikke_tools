"""Compiler-only source packages cannot turn an uninitialized phase into a battle."""
import copy,json,os,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
import portable_backend as backend
import test_portable_compile_cli as producer
cli=producer.cli
PTX=b'.version 8.4\n.target sm_86\n.address_size 64\n.visible .entry portableEvents() { ret; }\n'


class CompilerDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.base=producer.CompileCLITests();self.base.setUp();self.addCleanup(self.base.doCleanups)
        self.m=copy.deepcopy(self.base.m);self.m.update(suite='compiler-commands',purpose='compiler-diagnostic')
        self.m['golden'].update(proof_kind='compiler-source-only',calculation_verified=False,executable_battle_verified=False,entries=[])
        self.base.native.payload=PTX

    def proof(self):
        def compile_ptx(source):
            native=backend.C.WinDLL('nvrtc64_dummy.dll')
            artifact,receipt=backend.compile_cuda_artifact(native,source.read_bytes(),[self.base.dll],artifact_kind='ptx')
            source.with_suffix('.ptx').write_bytes(artifact);return artifact,receipt
        def copied(capture,suite):
            for path,name in [(self.base.cuda,'generated.cu'),(self.base.metal,'generated.metal'),(self.base.cuda.with_suffix('.ptx'),'compiled.ptx')]:
                (capture/name).write_bytes(path.read_bytes())
        env=dict(NIKKE_CUDA_ARTIFACT='ptx',NIKKE_VALIDATION_JOB_MEMORY_MB='2048')
        with self.base.context(compile_ptx),patch.object(cli,'copy_generated',copied),patch.dict(os.environ,env):
            cli.compile_child(self.m,self.base.capture,'cuda')
        cli.write(self.base.capture/'run.json',dict(package_id=self.m['package_id'],backend='cuda',mode='compile-only',artifact_kind='ptx',ptxas_level=None,memory_limit_mb=2048))
        import time
        stamp=time.time_ns();cli.write(self.base.capture/'execution.json',dict(passed=True,timeout_seconds=60,observation_error=None,wait_completed_unix_ns=stamp))
        pre=dict(child_pid=os.getpid(),child_ppid=17,job_members=[os.getpid()],child_creation_filetime_ticks='100',observed_unix_ns=1,job_memory_limit_bytes=2147483648)
        cli.write(self.base.capture/'job.json',dict(records=[dict(child_pid=os.getpid(),wrapper_pid=17,pre_gate_verified=True,inspection_error=None,pre_gate=pre,post_wait=dict(pre,job_members=[],observed_unix_ns=stamp))]))

    def audit(self):
        with patch.object(cli,'module',return_value=types.SimpleNamespace(normalized=cli.sha)):
            return cli.audit_compile_capture(self.m,self.base.capture,verify_artifacts=False)

    def test_shared_compile_and_audit_use_real_cache_receipts_but_never_certify_calculation(self):
        self.proof();r=self.audit()
        self.assertTrue(r['compiler_verified']);self.assertTrue(r['containment_verified'])
        self.assertFalse(r['calculation_verified']);self.assertFalse(r['preservation_verified'])
        self.assertEqual(self.base.native.calls.count('compile'),1)
        self.assertEqual(self.base.loader.call_args.args,('nvrtc64_dummy.dll',))

    def test_source_certificate_drift_rejects_before_nvrtc(self):
        self.m['golden']['generated_normalized']['cuda']='changed'
        with self.base.context(),patch.dict(os.environ,dict(NIKKE_CUDA_ARTIFACT='ptx',NIKKE_VALIDATION_JOB_MEMORY_MB='2048')):
            with self.assertRaisesRegex(ValueError,'source certificate'):cli.compile_child(self.m,self.base.capture,'cuda')
        self.base.loader.assert_not_called()

    def test_diagnostic_cache_check_is_a_file_only_hit_and_detects_source_corruption(self):
        binary=self.base.root/'cuda/bin';binary.mkdir(parents=True)
        self.base.dll=binary/'nvrtc64_dummy.dll';self.base.dll.write_bytes(b'compiler')
        self.proof();capture=self.base.capture;cli.collect(capture,capture/'artifacts.json')
        env=dict(CUDA_PATH=str(self.base.root/'cuda'),NIKKE_CUDA_COMPILE_CACHE=str(self.base.root/'cache'))
        with patch.object(cli,'verify_package',return_value=self.m),patch.dict(os.environ,env),cli.forbid_gpu(),patch.object(backend.C,'WinDLL',side_effect=AssertionError('No DLL loads'),create=True):
            result=cli.check_compile_cache(capture,self.base.root/'cache-result.json')
            self.assertTrue(result['passed']);self.assertTrue(result['cache']['hit'])
            self.assertFalse(result['calculation_verified']);self.assertEqual(result['nvrtc_compile_calls'],0)
            self.assertEqual(self.base.native.calls.count('compile'),1)
            (capture/'generated.cu').write_bytes(b'corrupt diagnostic source')
            with self.assertRaisesRegex(RuntimeError,'Cache miss'):cli.check_compile_cache(capture,self.base.root/'corrupt-result.json')

    def test_normal_run_adapter_module_and_development_are_forbidden_before_execution(self):
        out=self.base.root/'forbidden'
        with patch.object(cli,'verify_package',return_value=self.m),patch.object(cli,'run_job',side_effect=AssertionError('No Job allowed')):
            with self.assertRaisesRegex(ValueError,'cannot execute a battle'):cli.run_capture(out,'metal',60)
            with self.assertRaisesRegex(ValueError,'no battle adapter'):cli.open_suite(self.m)
            with self.assertRaisesRegex(ValueError,'sealed CUDA battle'):cli.module_child(self.m,out,'cuda')
            with self.assertRaisesRegex(ValueError,'cannot load'):cli.audit_module_capture(self.m,out)
            fake=types.SimpleNamespace(name='nt',environ={'NIKKE_CUDA_COMPILE_CACHE':'dedicated'})
            with patch.object(cli,'os',fake):
                with self.assertRaisesRegex(ValueError,'sealed Metal battle'):cli.module_capture(out,60,Path('original'))
        for develop,cases in ((True,()),(False,('x',))):
            with self.assertRaisesRegex(ValueError,'no battle development'):cli.make_package('compiler-commands',out,develop=develop,cases=cases)
        self.assertFalse(out.exists())

    def test_expanded_memory_cubin_or_ptxas_sweep_rejects_before_capture(self):
        out=self.base.root/'forbidden';fake=types.SimpleNamespace(name='nt',environ={'NIKKE_CUDA_COMPILE_CACHE':'dedicated'})
        with patch.object(cli,'os',fake),patch.object(cli,'verify_package',return_value=self.m):
            for kind,level,memory in (('cubin',None,2048),('ptx',None,4096),('ptx',None,1024),('cubin',1,2048)):
                with self.subTest(kind=kind,level=level,memory=memory),self.assertRaises(ValueError):
                    cli.compile_capture(out,60,Path('original'),kind,level,memory)
        self.assertFalse(out.exists())

    def test_auditor_rejects_diagnostic_budget_or_artifact_change(self):
        self.proof();path=self.base.capture/'run.json';original=cli.load(path)
        for field,value in (('memory_limit_mb',4096),('artifact_kind','cubin'),('ptxas_level',1)):
            changed=dict(original);changed[field]=value;cli.write(path,changed)
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'diagnostic proof'):self.audit()

    def test_child_rejects_wrong_artifact_or_missing_budget_before_build(self):
        with self.base.context(),patch.dict(os.environ,dict(NIKKE_CUDA_ARTIFACT='cubin',NIKKE_VALIDATION_JOB_MEMORY_MB='2048')):
            with self.assertRaisesRegex(ValueError,'child requires'):cli.compile_child(self.m,self.base.capture,'cuda')
        self.base.loader.assert_not_called()

    def test_purpose_and_battle_claims_cannot_be_forged_in_a_valid_hash_packet(self):
        root=self.base.root/'packet';root.mkdir();(root/'gpu').mkdir();(root/'research').mkdir()
        shader=root/'gpu/compiler_commands_entry.slang';shader.write_text('// fixture')
        base_shader=root/'gpu/base.slang';base_shader.write_text('// fixed shared fixture')
        baseline=root/cli.SUITES['compiler-commands']['support_files'][0]
        cli.write(baseline,dict(source_sha256={'gpu/base.slang':cli.sha(base_shader.read_bytes())}))
        certificate=root/cli.SUITES['compiler-commands']['golden']
        m=copy.deepcopy(self.m);m['schema']=cli.SCHEMA;m['golden']['source_sha256']={'gpu/compiler_commands_entry.slang':cli.sha(shader.read_bytes()),'gpu/base.slang':cli.sha(base_shader.read_bytes())}
        m['golden']['baseline_golden_sha256']=cli.sha(baseline.read_bytes())
        def save():
            cli.write(certificate,m['golden']);m['files']=cli.file_records(root,['gpu/compiler_commands_entry.slang','gpu/base.slang',certificate.relative_to(root).as_posix(),baseline.relative_to(root).as_posix()])
            m['package_id']=cli.package_id(m);cli.write(root/'gpu-package.json',m)
        save();self.assertEqual(cli.verify_package(root)['purpose'],'compiler-diagnostic')
        for field,value in (('purpose','sealed'),('calculation_verified',True),('executable_battle_verified',True),('proof_kind','battle'),('entries',[{}]),('baseline_golden_sha256','wrong')):
            original=copy.deepcopy(m)
            if field=='purpose':m[field]=value
            else:m['golden'][field]=value
            save()
            with self.subTest(field=field),self.assertRaises(ValueError):cli.verify_package(root)
            m=original
        save();m['files']=[r for r in m['files'] if r['path']!=baseline.relative_to(root).as_posix()]
        m['package_id']=cli.package_id(m);cli.write(root/'gpu-package.json',m)
        with self.assertRaisesRegex(ValueError,'baseline absent'):cli.verify_package(root)

    def test_historical_compiler_records_bind_original_certificate_and_baseline(self):
        root=self.base.root/'historical-packet';(root/'gpu').mkdir(parents=True);(root/'research').mkdir()
        shader=root/'gpu/compiler_commands_entry.slang';shader.write_text('// prior entry')
        base_shader=root/'gpu/old.slang';base_shader.write_text('// prior shared body')
        baseline=root/'research/old-baseline.json';cli.write(baseline,dict(source_sha256={'gpu/old.slang':cli.sha(base_shader.read_bytes())}))
        certificate=root/'research/old-source-certificate.json'
        m=copy.deepcopy(self.m);m['schema']=cli.SCHEMA
        m['golden']['source_sha256']={'gpu/compiler_commands_entry.slang':cli.sha(shader.read_bytes()),'gpu/old.slang':cli.sha(base_shader.read_bytes())}
        m['golden']['baseline_golden_sha256']=cli.sha(baseline.read_bytes());cli.write(certificate,m['golden'])
        names=['gpu/compiler_commands_entry.slang','gpu/old.slang','research/old-baseline.json','research/old-source-certificate.json']
        def save():
            m['files']=cli.file_records(root,names);m['package_id']=cli.package_id(m);cli.write(root/'gpu-package.json',m)
        save();before={name:(root/name).read_bytes() for name in names};manifest=(root/'gpu-package.json').read_bytes()
        with self.assertRaises(FileNotFoundError):cli.verify_package(root)
        self.assertEqual(cli.verify_package(root,historical_compiler=True),m)
        self.assertEqual({name:(root/name).read_bytes() for name in names},before);self.assertEqual((root/'gpu-package.json').read_bytes(),manifest)
        duplicate=root/'research/duplicate-certificate.json';duplicate.write_bytes(certificate.read_bytes());names.append('research/duplicate-certificate.json');save()
        with self.assertRaisesRegex(ValueError,'one immutable owner'):cli.verify_package(root,historical_compiler=True)
        names.pop();save();original=baseline.read_bytes();baseline.write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError,'bytes/SHA/size'):cli.verify_package(root,historical_compiler=True)
        baseline.write_bytes(original);names.remove('research/old-baseline.json');save()
        with self.assertRaisesRegex(ValueError,'baseline absent'):cli.verify_package(root,historical_compiler=True)

    def test_historical_mode_cannot_admit_battle_or_invented_calculation(self):
        root=self.base.root/'historical-rejected';root.mkdir()
        m=copy.deepcopy(self.m);m['schema']=cli.SCHEMA;m['files']=[];m['purpose']='sealed';m['package_id']=cli.package_id(m);cli.write(root/'gpu-package.json',m)
        with self.assertRaises(ValueError):cli.verify_package(root,historical_compiler=True)
        m['purpose']='compiler-diagnostic';m['golden']['calculation_verified']=True
        (root/'research').mkdir();certificate=root/'research/claim.json';cli.write(certificate,m['golden'])
        # Even a fully self-consistent record layout cannot bless calculation.
        baseline=root/'research/base.json';cli.write(baseline,dict(source_sha256={}))
        m['golden']['baseline_golden_sha256']=cli.sha(baseline.read_bytes());cli.write(certificate,m['golden'])
        m['files']=cli.file_records(root,['research/claim.json','research/base.json']);m['package_id']=cli.package_id(m);cli.write(root/'gpu-package.json',m)
        with self.assertRaisesRegex(ValueError,'cannot claim a battle'):cli.verify_package(root,historical_compiler=True)

    def test_full_entry_certificate_reuses_exact_saved_metal_closure_and_generated_code(self):
        suite=cli.SUITES['compiler-full'];certificate=cli.load(ROOT/suite['golden'])
        baseline_path=ROOT/suite['support_files'][0];baseline=cli.load(baseline_path)
        # This is a historical certificate, not an automatic promotion of
        # later shared GPU features. Its owner is the exact saved Metal proof.
        self.assertIn(suite['source'],certificate['source_sha256'])
        self.assertEqual(certificate['source_sha256'],baseline['source_sha256'])
        self.assertEqual(certificate['generated_normalized'],baseline['generated_normalized'])
        self.assertEqual(certificate['baseline_golden_sha256'],cli.sha(baseline_path.read_bytes()))
        self.assertEqual(certificate['entries'],[]);self.assertFalse(certificate['calculation_verified'])

    def test_stale_full_entry_cannot_publish_a_current_compiler_packet(self):
        suite=cli.SUITES['compiler-full'];sources=backend.source_hashes(suite['source']);sources=dict(sources);sources[suite['source']]='0'*64
        names=set(sources)|{'scripts/nikke_gpu.py',suite['golden'],*suite['support_files'],*('tests/'+p for p in suite['tests'])}
        tracked=('\0'.join(sorted(names))+'\0').encode();output=self.base.root/'stale-compiler.zip'
        # This synthetic inventory tests the source gate, not the complete CPU
        # test payload. Real audit-data admission has its own negative tests.
        with patch.dict(cli.SUITES,{'compiler-full':dict(suite,tests=[])}),patch.object(cli,'SMOKE_TESTS',[]),\
             patch('portable_reference.validate_reference_payload'),\
             patch.object(cli.subprocess,'check_output',return_value=tracked),patch.object(backend,'source_hashes',return_value=sources),\
             patch.object(backend,'build',side_effect=AssertionError('No compiler')),\
             patch.object(cli,'development_baseline',side_effect=AssertionError('No native baseline')):
            with self.assertRaisesRegex(ValueError,'source closure is stale'):cli.make_package('compiler-full',output)
        self.assertFalse(output.exists())

    def test_registered_current_full_entry_reuses_shared_compile_and_audit(self):
        self.m['suite']='compiler-full--max-ammo-scaling-retention'
        self.m['golden']['baseline_suite']='max-ammo-scaling-retention'
        self.proof();result=self.audit()
        self.assertTrue(result['compiler_verified']);self.assertFalse(result['calculation_verified'])
        with self.assertRaisesRegex(ValueError,'no battle adapter'):cli.open_suite(self.m)

    def test_full_entry_uses_shared_compile_audit_and_cannot_execute_a_battle(self):
        self.m['suite']='compiler-full';self.proof();result=self.audit()
        self.assertTrue(result['compiler_verified']);self.assertFalse(result['calculation_verified'])
        self.assertEqual(self.base.native.calls.count('compile'),1)
        with patch.object(cli,'verify_package',return_value=self.m),patch.object(cli,'run_job',side_effect=AssertionError('No Job')):
            with self.assertRaisesRegex(ValueError,'cannot execute a battle'):
                cli.run_capture(self.base.root/'forbidden-full','cuda',60)
            with self.assertRaisesRegex(ValueError,'no battle adapter'):cli.open_suite(self.m)

    def test_full_entry_packet_requires_entry_and_generated_fingerprints_in_exact_baseline(self):
        root=self.base.root/'full-packet';(root/'gpu').mkdir(parents=True);(root/'research').mkdir()
        suite=cli.SUITES['compiler-full'];entry=suite['source'];(root/entry).write_bytes(b'// full fixture')
        baseline_path=root/suite['support_files'][0];certificate_path=root/suite['golden']
        sources={entry:cli.sha((root/entry).read_bytes())}
        baseline=dict(source_sha256=sources,generated_normalized=dict(cuda='cuda',metal='metal'))
        cli.write(baseline_path,baseline);m=copy.deepcopy(self.m);m.update(schema=cli.SCHEMA,suite='compiler-full')
        m['golden'].update(source_sha256=sources,generated_normalized=baseline['generated_normalized'],baseline_golden_sha256=cli.sha(baseline_path.read_bytes()))
        def save():
            cli.write(certificate_path,m['golden']);m['files']=cli.file_records(root,[entry,suite['golden'],suite['support_files'][0]])
            m['package_id']=cli.package_id(m);cli.write(root/'gpu-package.json',m)
        save();self.assertEqual(cli.verify_package(root),m)
        self.assertEqual(cli.verify_package(root,historical_compiler=True),m)
        original=copy.deepcopy(m)
        # Rehashing the whole packet cannot hide removing the full entry from baseline.
        baseline['source_sha256']={};cli.write(baseline_path,baseline)
        m['golden']['baseline_golden_sha256']=cli.sha(baseline_path.read_bytes());save()
        with self.assertRaisesRegex(ValueError,'changed the shared baseline'):cli.verify_package(root)
        baseline['source_sha256']=sources;cli.write(baseline_path,baseline);m=copy.deepcopy(original)
        m['golden']['generated_normalized']['cuda']='different-generated-code';save()
        with self.assertRaisesRegex(ValueError,'changed the shared baseline'):cli.verify_package(root)
        with self.assertRaisesRegex(ValueError,'changed the shared baseline'):cli.verify_package(root,historical_compiler=True)

    def test_shared_source_closure_and_phase_entry_are_fixed_without_math_changes(self):
        from portable_phase_codegen import PHASES
        from portable_weapon_phase_contract import tokens
        source=(ROOT/'gpu/compiler_commands_entry.slang').read_text()
        body=source[source.index('void portableEvents'):]
        self.assertIn('executePortableCommands(runtimeStates[id.x],input,output,queries);',body)
        self.assertNotIn('initializeRuntime(',body);self.assertNotIn('initializePortableProgram(',body);self.assertNotIn('writePortableProgram(',body)
        expected='void portableEvents(uint3 id : SV_DispatchThreadID) { if(id.x>=commands[0]) return; uint input=1+id.x*P_INPUT_WORDS,output=id.x*P_OUTPUT_WORDS; WORLD_TEAM_INPUT(input,output) '+PHASES['commands']+' }'
        self.assertEqual(tokens(body),tokens(expected))


if __name__=='__main__':unittest.main()
