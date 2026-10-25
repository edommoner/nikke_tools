"""Fresh Metal audits feed registered compiler packets without compiler/cache promotion."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,Mock
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','tests')]
spec=importlib.util.spec_from_file_location('certificate_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
import portable_backend as backend
from portable_compiler_certificate import alias,certificate,full_family

class CompilerCertificateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.package=self.root/'saved';self.capture=self.root/'capture'
        self.package.mkdir();self.capture.mkdir();self.suite='max-ammo-scaling-retention';self.config=cli.SUITES[self.suite]
        self.baseline=dict(source_sha256={self.config['source']:'a'*64},generated_normalized=dict(cuda='c'*64,metal='d'*64),entries=[dict(name='example')],input_sha256='i'*64,output_sha256='o'*64)
        self.path=self.root/self.config['golden'];self.path.parent.mkdir(parents=True);cli.write(self.path,self.baseline)
        self.m=dict(suite=self.suite,package_id='saved',purpose='development',selected_cases=[],golden=copy.deepcopy(self.baseline));cli.write(self.package/'gpu-package.json',self.m)
        cli.write(self.capture/'run.json',dict(package_id='saved',backend='metal'));cli.write(self.capture/'artifacts.json',dict(files=[]))
        self.audit=Mock(return_value=dict(package_id='saved',golden=self.baseline,audit=dict(calculation_verified=True)))
    def make(self,*,audit=None,sources=None,output=None):
        with patch.object(cli,'ROOT',self.root),patch.object(cli,'verify_package',return_value=self.m),patch.object(cli,'audit_saved_metal',audit or self.audit),patch.object(backend,'source_hashes',return_value=sources or self.baseline['source_sha256']),cli.forbid_gpu():
            return cli.make_compiler_certificate(self.suite,self.package,self.capture,output or self.root/'evidence')
    def test_historical_mixed_certificate_keeps_full_runtime_and_rejects_stale_current_sources(self):
        suite='attack-group-mixed';name=alias(suite);config=cli.SUITES[name]
        baseline=cli.load(ROOT/cli.SUITES[suite]['golden']);proof=cli.load(ROOT/config['golden'])
        self.assertEqual(config['source'],cli.SUITES[suite]['source'])
        self.assertNotEqual(config['source'],cli.SUITES['compiler-commands']['source'])
        self.assertEqual(proof,certificate(suite,baseline,(ROOT/cli.SUITES[suite]['golden']).read_bytes()))
        current=backend.source_hashes(config['source'])
        from portable_coordinate_accum_emission_source_contract import project_sources
        from portable_coordinate_group_source_contract import historical_source_hashes
        projected=historical_source_hashes(ROOT,config['source'],project_sources(ROOT))
        self.assertEqual(proof['source_sha256'],projected)
        if current!=proof['source_sha256']:
            # An exact historical inverse proves the prior source, never current
            # package admission. Feed real current bytes to the unchanged gate.
            import shutil
            baseline_path=cli.SUITES[suite]['golden'];paths=[*current,config['golden'],baseline_path]
            for path in paths:
                dest=self.root/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,dest)
            files=cli.file_records(self.root,paths)
            manifest=dict(schema=cli.SCHEMA,suite=name,purpose='compiler-diagnostic',golden=proof,files=files,selected_cases=[])
            manifest['package_id']=cli.package_id(manifest);cli.write(self.root/'gpu-package.json',manifest)
            with self.assertRaisesRegex(ValueError,'GPU source record differs from golden'):
                cli.verify_package(self.root)
        self.assertIn('gpu/attack_group_runtime.slang',proof['source_sha256'])
        self.assertIn('gpu/program_phases.slang',proof['source_sha256'])
        self.assertEqual(config['inputs'],0);self.assertEqual(config['native'],0)
        self.assertFalse(proof['calculation_verified']);self.assertFalse(proof['executable_battle_verified'])

    def test_registered_aliases_keep_exact_source_and_existing_commands_unchanged(self):
        cfg=cli.SUITES[alias(self.suite)];self.assertEqual(cfg['source'],self.config['source']);self.assertEqual(cfg['support_files'],[self.config['golden']]);self.assertTrue(cli.full_compiler(dict(suite=alias(self.suite))))
        self.assertFalse(cli.full_compiler(dict(suite='compiler-commands')));self.assertTrue(cli.full_compiler(dict(suite='compiler-full')))
        self.assertEqual(cli.SUITES['compiler-full']['golden'],'research/portable-compiler-full-heal-share-source-certificate.json')
        self.assertFalse(full_family(alias(self.suite),'other'));self.assertFalse(full_family('compiler-commands',self.suite))
    def test_independently_sealed_current_battles_have_a_normal_package_path(self):
        for name in ('max-ammo-scaling','max-ammo-scaling-retention','max-ammo-scaling-rosters'):
            self.assertFalse(cli.SUITES[name]['development_only'])
            self.assertFalse(cli.compiler_only(dict(suite=name,purpose='sealed')))
            self.assertEqual(cli.SUITES[name]['source'],cli.SUITES[self.suite]['source'])
            self.assertGreater(cli.SUITES[name]['inputs'],0)
    def test_alias_rejects_paths_uppercase_empty_and_unknown_full_family(self):
        for value in ('','../x','x/y','x_y','Upper','x--y',None):
            with self.subTest(value=value),self.assertRaises(ValueError):alias(value)
        with self.assertRaises(ValueError):cli.make_compiler_certificate('not-registered',self.package,self.capture,self.root/'unknown')
    def test_success_uses_one_independent_audit_and_cannot_claim_cuda_success(self):
        result=self.make();self.assertTrue(result['passed']);self.assertFalse(result['compiler_verified']);self.assertFalse(result['cache_hit_verified']);self.assertFalse(result['calculation_verified']);self.assertEqual(result['gpu_calls'],0)
        self.audit.assert_called_once_with(self.package,self.capture,timeout=120)
        c=cli.load(self.root/'evidence/source-certificate.json');self.assertEqual(c['source_sha256'],self.baseline['source_sha256']);self.assertEqual(c['entries'],[]);self.assertIsNone(c['input_sha256']);self.assertFalse(c['executable_battle_verified'])
        self.assertEqual(c['baseline_golden_sha256'],cli.sha(self.path.read_bytes()))
    def test_sealed_saved_metal_package_is_accepted_without_weakening_seal_command(self):
        self.m['purpose']='sealed';self.assertTrue(self.make()['passed']);self.audit.assert_called_once()
    def test_wrong_run_or_selected_subset_stops_before_audit(self):
        for change in ('backend','package','suite','subset'):
            original=copy.deepcopy(self.m);run=dict(package_id='saved',backend='metal')
            if change=='backend':run['backend']='cuda'
            elif change=='package':run['package_id']='other'
            elif change=='suite':self.m['suite']='max-ammo-scaling'
            else:self.m['selected_cases']=['one']
            cli.write(self.capture/'run.json',run)
            with self.subTest(change=change),self.assertRaises(ValueError):self.make(output=self.root/change)
            self.audit.assert_not_called();self.m=original
    def test_stale_current_or_saved_closure_stops_before_native_audit(self):
        with self.assertRaisesRegex(ValueError,'stale'):self.make(sources={'changed':'x'},output=self.root/'stale')
        self.m['golden']['source_sha256']={'old':'x'}
        with self.assertRaisesRegex(ValueError,'closure differs'):self.make(output=self.root/'old')
        self.audit.assert_not_called()
    def test_audited_output_mismatch_or_failed_audit_cannot_publish_certificate(self):
        for name in ('changed-output','wrong-audited-package','audit-failure'):
            proof=copy.deepcopy(self.audit.return_value)
            if name=='changed-output':proof['golden']['output_sha256']='wrong'
            else:proof['package_id']='wrong'
            audit=Mock(side_effect=ValueError('raw mismatch')) if name=='audit-failure' else Mock(return_value=proof)
            with self.subTest(name=name),self.assertRaises(ValueError):self.make(audit=audit,output=self.root/name)
            self.assertFalse((self.root/name/'source-certificate.json').exists());self.assertTrue((self.root/name/'failure.json').exists())
    def test_baseline_changed_during_audit_is_preserved_as_failure(self):
        def audit(*a,**kw):self.path.write_text('{}');return self.audit.return_value
        with self.assertRaisesRegex(ValueError,'changed during'):self.make(audit=audit)
        self.assertFalse((self.root/'evidence/source-certificate.json').exists())
    def test_origin_receipt_changed_during_audit_cannot_publish_certificate(self):
        def audit(*a,**kw):
            cli.write(self.capture/'artifacts.json',dict(files=['changed']))
            return self.audit.return_value
        with self.assertRaisesRegex(ValueError,'capture changed during'):self.make(audit=audit)
        self.assertFalse((self.root/'evidence/source-certificate.json').exists())
    def test_nonempty_fresh_output_and_invalid_budget_are_rejected(self):
        self.make();original=(self.root/'evidence/report.json').read_bytes()
        with self.assertRaises(FileExistsError):self.make()
        self.assertEqual((self.root/'evidence/report.json').read_bytes(),original)
        for budget in (0,181,True,'120'):
            with self.assertRaises(ValueError):cli.make_compiler_certificate(self.suite,self.package,self.capture,self.root/'budget',timeout=budget)
    def test_current_and_historical_packets_resolve_the_same_immutable_certificate(self):
        name=alias(self.suite);config=cli.SUITES[name];entry=self.root/config['source'];entry.parent.mkdir(parents=True,exist_ok=True);entry.write_text('// full world fixture')
        baseline=dict(self.baseline,source_sha256={config['source']:cli.sha(entry.read_bytes())});cli.write(self.path,baseline)
        cert=certificate(self.suite,baseline,self.path.read_bytes());cert_path=self.root/config['golden'];cli.write(cert_path,cert)
        files=cli.file_records(self.root,[config['source'],config['golden'],self.config['golden']])
        manifest=dict(schema=cli.SCHEMA,suite=name,purpose='compiler-diagnostic',golden=cert,files=files,selected_cases=[]);manifest['package_id']=cli.package_id(manifest);cli.write(self.root/'gpu-package.json',manifest)
        with patch.object(cli,'ROOT',self.root),cli.forbid_gpu():
            self.assertEqual(cli.verify_package(self.root),manifest)
            latest=dict(config,golden='research/moved-certificate.json',support_files=['research/moved-baseline.json'])
            with patch.dict(cli.SUITES,{name:latest}):self.assertEqual(cli.verify_package(self.root,historical_compiler=True),manifest)
            bad=dict(cert,baseline_suite='different');cli.write(cert_path,bad)
            with self.assertRaises(ValueError):cli.verify_package(self.root)

    def test_certificate_does_not_alias_mutable_baseline_or_accept_empty_proof(self):
        c=certificate(self.suite,self.baseline,self.path.read_bytes());c['source_sha256']['new']='x';self.assertNotIn('new',self.baseline['source_sha256'])
        for field,value in [('entries',[]),('input_sha256',None),('output_sha256',None),('generated_normalized',{'cuda':'x'})]:
            with self.subTest(field=field),self.assertRaises(ValueError):certificate(self.suite,dict(self.baseline,**{field:value}),b'{}')
if __name__=='__main__':unittest.main()
