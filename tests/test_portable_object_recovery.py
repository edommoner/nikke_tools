"""Recover saved bytes without rerunning or rewriting a timed-out capture."""
import contextlib, copy, importlib.util, io, json, shutil, sys, types, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','tests','research')]
import portable_object_recovery as recovery
import test_portable_module_object as modules
cli=modules.cli


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.module=modules.ModuleObjectTests();self.module.setUp();self.addCleanup(self.module.doCleanups)
        self.f=self.module.f;self.outer=self.f.root/'packet';self.outer.mkdir()
        self.f.capture=self.outer/'proof';self.f.capture.mkdir()
        self.module.request={key:value if key=='source_kind' else str(Path(value).resolve()) for key,value in self.module.request.items()}
        self.module.proof()
        self.capture=self.f.capture;self.package=self.f.base.package
        wrapper=self.package/'scripts/run-gpu-packet.py';wrapper.parent.mkdir()
        shutil.copyfile(ROOT/'scripts/run-gpu-packet.py',wrapper)
        spec=importlib.util.spec_from_file_location('recovery_packet_fixture',wrapper)
        self.packet=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.packet)
        self.request={key:self.module.request[key] for key in self.packet.OBJECT_STAGES['module-object']}
        plan=self.packet.recipe(self.f.base.m['package_id'],'module-object','cuda',self.outer,self.f.root/'original',90,self.request)
        cli.write(self.outer/'recipe.json',plan);self.f.base.job_proof(self.outer)
        for folder in (self.outer,self.capture):
            facts=cli.load(folder/'execution.json');facts.update(timed_out=folder==self.outer,
                passed=folder!=self.outer,below_normal_priority=True,child_exit_code=None if folder==self.outer else 0)
            (folder/'execution.json').write_text(json.dumps(facts))
        run=cli.load(self.capture/'run.json');run['status']='processing'
        (self.capture/'run.json').write_text(json.dumps(run))
        origin=cli.load(self.capture/'object-request.json')['origin']
        cli.write(self.package/'module-object-claimed-cuda.json',dict(package_id=self.f.base.m['package_id'],capture=str(self.capture),origin=origin))
        cli.write(self.package/'packet-stage-claimed-module-object-cuda.json',dict(package_id=self.f.base.m['package_id'],capture=str(self.outer)))
        self.output=self.f.root/'recovered'
        self.expected=cli.sha((self.capture/'module.o').read_bytes())

    def context(self):
        stack=self.f.context()
        stack.enter_context(patch.object(cli,'module',side_effect=lambda path:self.packet if Path(path).name=='run-gpu-packet.py' else types.SimpleNamespace(normalized=cli.sha)))
        return stack

    def test_original_stays_incomplete_and_no_native_tool_is_repeated(self):
        before=recovery.snapshot(cli,self.package,self.capture);processes=len(self.f.base.processes)
        with self.context():result=recovery.recover(cli,self.package,self.capture,self.output,self.expected)
        self.assertTrue(result['object_verified']);self.assertTrue(result['containment_verified'])
        for key in ('passed','original_stage_verified','calculation_verified','link_verified','original_capture_modified'):
            self.assertIs(result[key],False)
        self.assertEqual(result['native_tool_calls'],0);self.assertEqual(result['kernel_calls'],0)
        self.assertEqual(before,recovery.snapshot(cli,self.package,self.capture))
        self.assertEqual(len(self.f.base.processes),processes)
        for name in recovery.MISSING:self.assertFalse((self.capture/name).exists())
        self.assertEqual(cli.load(self.capture/'run.json')['status'],'processing')
        with self.context(),self.assertRaises(FileExistsError):recovery.recover(cli,self.package,self.capture,self.output,self.expected)

    def test_wrong_artifact_is_rejected_without_rewriting_original(self):
        (self.capture/'module.o').write_bytes((self.capture/'module.o').read_bytes()+b'bad')
        before=recovery.snapshot(cli,self.package,self.capture)
        with self.context(),self.assertRaisesRegex(ValueError,'audit failed'):recovery.recover(cli,self.package,self.capture,self.output,self.expected)
        self.assertTrue((self.output/'failure.json').exists());self.assertFalse((self.output/'result.json').exists())
        self.assertEqual(before,recovery.snapshot(cli,self.package,self.capture))

    def test_prior_result_cannot_be_overwritten_and_output_cannot_enter_original(self):
        for path in (self.package/'recovered',self.outer/'recovered',self.capture):
            with self.context(),self.assertRaisesRegex(ValueError,'outside original'):recovery.recover(cli,self.package,self.capture,path,self.expected)
        cli.write(self.capture/'artifacts.json',dict(files=[]))
        with self.context(),self.assertRaisesRegex(ValueError,'does not replace'):recovery.recover(cli,self.package,self.capture,self.output,self.expected)

    def test_failed_or_nonterminal_inner_and_unclosed_outer_are_rejected(self):
        outer=cli.load(self.outer/'execution.json');inner=cli.load(self.capture/'execution.json')
        jobs=cli.load(self.outer/'job.json')
        cases=[(self.outer/'execution.json',dict(outer,timed_out=False)),
               (self.capture/'execution.json',dict(inner,child_exit_code=1)),
               (self.capture/'execution.json',dict(inner,timed_out=True)),
               (self.capture/'execution.json',dict(inner,cleanup_error='unknown'))]
        bad=copy.deepcopy(jobs);bad['records'][0]['post_wait']['job_members']=[123]
        cases.append((self.outer/'job.json',bad))
        for index,(path,value) in enumerate(cases):
            original=path.read_bytes();path.write_text(json.dumps(value))
            with self.subTest(index=index),self.context(),self.assertRaises(ValueError):
                recovery.recover(cli,self.package,self.capture,self.f.root/('bad'+str(index)),self.expected)
            path.write_bytes(original)

    def test_bytes_changed_during_existing_audit_are_detected(self):
        real=cli.audit_partition_object_capture
        def changed(*args,**kwargs):
            result=real(*args,**kwargs)
            (self.capture/'new.log').write_bytes(b'late write')
            return result
        with self.context(),patch.object(cli,'audit_partition_object_capture',side_effect=changed),self.assertRaisesRegex(ValueError,'changed during'):
            recovery.recover(cli,self.package,self.capture,self.output,self.expected)

    def test_external_digest_and_upstream_evidence_locations_are_required(self):
        with self.context(),self.assertRaisesRegex(ValueError,'externally recorded'):
            recovery.recover(cli,self.package,self.capture,self.output,'0'*64)
        for index,path in enumerate((self.f.base.source_package/'new', self.f.cache.parent/'new')):
            with self.context(),self.assertRaisesRegex(ValueError,'outside original'):
                recovery.recover(cli,self.package,self.capture,path,self.expected)

    def test_cli_dispatch_works_when_imported_and_retains_preservation_exit_two(self):
        with self.context(),contextlib.redirect_stdout(io.StringIO()),self.assertRaises(SystemExit) as error:
            cli.main(['recover-object','--source-package',str(self.package),'--source-capture',str(self.capture),
                '--out',str(self.output),'--object-sha256',self.expected])
        self.assertEqual(error.exception.code,2)
        self.assertTrue(cli.load(self.output/'result.json')['object_verified'])


if __name__=='__main__':unittest.main()
