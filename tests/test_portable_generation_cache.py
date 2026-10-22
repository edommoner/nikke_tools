"""Exact artifact reuse, independent resident audits and no-compiler failures."""
import base64,hashlib,json,os,shutil,subprocess,sys,tempfile,unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'tests')]
import portable_backend as backend
import portable_generation_cache as cache
from test_portable_resident_layout import document

class GenerationCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'project';self.tool=Path(self.tmp.name)/'compiler';self.cached=Path(self.tmp.name)/'cache';self.calls=[];self.problem=None
        (self.root/'gpu').mkdir(parents=True);(self.root/'app').mkdir();(self.tool/'bin').mkdir(parents=True);(self.tool/'include').mkdir()
        (self.tool/'bin/slangc').write_bytes(b'compiler');(self.tool/'include/prelude.h').write_bytes(b'prelude')
        (self.root/'gpu/entry.slang').write_text('#define PORTABLE_RESIDENT_RUNTIME\n')
        for name in ('portable_backend.py','portable_generation_cache.py','portable_resident_layout.py','portable_scope_snapshot_audit.py'):shutil.copyfile(ROOT/'app'/name,self.root/'app'/name)
        self.context=ExitStack();self.addCleanup(self.context.close)
        self.context.enter_context(patch.object(backend,'ROOT',self.root));self.context.enter_context(patch.dict(os.environ,{'NIKKE_SLANG_ROOT':str(self.tool),'NIKKE_SLANG_GENERATION_CACHE':str(self.cached),'NIKKE_SLANG_GENERATION_REQUIRED':'0'}))
        self.context.enter_context(patch.object(backend.subprocess,'run',side_effect=self.compiler))
    def compiler(self,args,**kwargs):
        target=args[args.index('-target')+1];self.calls.append(target)
        output=Path(args[args.index('-o')+1]);reflection=Path(args[args.index('-reflection-json')+1])
        output.write_bytes(b'struct Runtime_0\n{ unsigned small; unsigned long long large; };\n' if target=='cuda' else b'metal code')
        reflection.write_text(json.dumps(document(target)))
        if self.problem=='source':(self.root/'gpu/entry.slang').write_text('changed')
        if self.problem=='compiler':(self.tool/'bin/slangc').write_bytes(b'changed compiler')
        if self.problem=='exit':return subprocess.CompletedProcess(args,1,b'',b'compiler failure')
        return subprocess.CompletedProcess(args,0,b'',b'')
    def build(self,required=False):
        with patch.dict(os.environ,NIKKE_SLANG_GENERATION_REQUIRED=str(int(required))):return backend.build('gpu/entry.slang','portableEvents')
    def receipt(self):return json.loads((self.root/'research/portable-build/entry.generation-cache.json').read_text())
    def live(self):
        folder=self.root/'research/portable-build'
        return {p.name:p.read_bytes() for p in folder.glob('*')} if folder.exists() else {}
    def corrupt(self,change):
        p=next(self.cached.glob('*.json'));v=json.loads(p.read_text());change(v);p.write_text(json.dumps(v))
    def test_miss_then_required_hit_never_launches_compiler(self):
        paths,hashes=self.build();self.assertEqual(self.calls,['cuda','metal']);first=self.live();self.assertFalse(self.receipt()['hit'])
        paths,hashes=self.build(True);self.assertEqual(self.calls,['cuda','metal']);self.assertTrue(self.receipt()['hit'])
        for name,raw in first.items():
            if not name.endswith('generation-cache.json'):self.assertEqual(self.live()[name],raw)
        self.assertTrue(cache.audit_receipt(self.receipt(),hashes,paths)['verified'])
    def test_identical_code_from_another_package_root_reuses_pair(self):
        self.build();other=Path(self.tmp.name)/'other';shutil.copytree(self.root,other);shutil.rmtree(other/'research')
        with patch.object(backend,'ROOT',other):self.build(True)
        self.assertEqual(self.calls,['cuda','metal'])
    def test_required_miss_and_foreign_claim_never_compile(self):
        with self.assertRaisesRegex(RuntimeError,'Required.*miss'):self.build(True)
        self.assertEqual(self.calls,[]);hashes=backend.source_hashes('gpu/entry.slang');i=cache.identity(self.root,self.tool,'gpu/entry.slang','portableEvents',hashes);self.cached.mkdir();claim=self.cached/(cache.key(i)+'.claim');claim.write_bytes(b'foreign')
        with self.assertRaisesRegex(RuntimeError,'Slang generation already claimed'):self.build()
        self.assertEqual(claim.read_bytes(),b'foreign');self.assertEqual(self.calls,[])
    def test_changed_source_compiler_prelude_or_consumer_is_required_miss(self):
        self.build()
        for p in [self.root/'gpu/entry.slang',self.tool/'bin/slangc',self.tool/'include/prelude.h',self.root/'app/portable_scope_snapshot_audit.py']:
            original=p.read_bytes();p.write_bytes(original+b'\n// changed')
            with self.subTest(path=str(p)),self.assertRaisesRegex(RuntimeError,'Required.*miss'):self.build(True)
            p.write_bytes(original)
        self.assertEqual(self.calls,['cuda','metal'])
    def test_artifact_corruption_does_not_compile_or_replace_live_outputs(self):
        self.build();before=self.live();self.corrupt(lambda v:v['artifacts']['cuda'].update(base64=base64.b64encode(b'changed').decode()))
        with self.assertRaisesRegex(ValueError,'integrity'):self.build()
        self.assertEqual(before,self.live());self.assertEqual(self.calls,['cuda','metal'])
    def test_incomplete_pair_rejects_without_live_replacement(self):
        self.build();before=self.live();self.corrupt(lambda v:v['artifacts'].pop('metal-reflection'))
        with self.assertRaisesRegex(ValueError,'pair incomplete'):self.build()
        self.assertEqual(before,self.live());self.assertEqual(self.calls,['cuda','metal'])
    def test_even_rehashed_bad_reflection_is_reaudited(self):
        self.build();before=self.live()
        def change(v):
            doc=json.loads(base64.b64decode(v['artifacts']['metal-reflection']['base64']));doc['parameters'][2]['binding']['index']=1;raw=json.dumps(doc).encode();v['artifacts']['metal-reflection']=dict(bytes=len(raw),sha256=cache.digest(raw),base64=base64.b64encode(raw).decode())
        self.corrupt(change)
        with self.assertRaisesRegex(ValueError,'binding'):self.build()
        self.assertEqual(before,self.live());self.assertEqual(self.calls,['cuda','metal'])
    def test_compiler_failure_or_mutation_never_publishes_live_or_cache(self):
        folder=self.root/'research/portable-build';folder.mkdir(parents=True);(folder/'entry.cu').write_bytes(b'previous')
        before=self.live()
        for problem in ('source','compiler','exit'):
            self.problem=problem
            with self.subTest(problem=problem),self.assertRaises((ValueError,RuntimeError)):self.build()
            self.assertEqual(before,self.live());self.assertEqual(list(self.cached.glob('*.json')),[]);self.assertEqual(list(self.cached.glob('*.claim')),[])
            (self.root/'gpu/entry.slang').write_text('#define PORTABLE_RESIDENT_RUNTIME\n');(self.tool/'bin/slangc').write_bytes(b'compiler')
    def test_untracked_includes_imports_time_macros_or_external_env_reject(self):
        (self.root/'gpu/extra.slang').write_text('// dependency')
        for code in ('#include HEADER','# include \"extra.slang\"','import external;','export import external;','// __TIME__'):
            (self.root/'gpu/entry.slang').write_text('#define PORTABLE_RESIDENT_RUNTIME\n'+code)
            with self.subTest(code=code),self.assertRaises(ValueError):self.build()
        (self.root/'gpu/entry.slang').write_text('#define PORTABLE_RESIDENT_RUNTIME\n')
        with patch.dict(os.environ,SLANG_PATH='external'),self.assertRaises(ValueError):self.build()
        self.assertEqual(self.calls,[])
    def test_receipt_identity_and_artifact_faults_are_rejected(self):
        paths,hashes=self.build();r=self.receipt()
        for field,value in [('key','bad'),('compiler_invocations',7),('hit',1)]:
            bad=json.loads(json.dumps(r));bad[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):cache.audit_receipt(bad,hashes,paths)
        paths['cuda'].write_bytes(b'changed')
        with self.assertRaises(ValueError):cache.audit_receipt(r,hashes,paths)

    def test_cli_generation_and_journal_audit_preserve_cache_boundary(self):
        import importlib.util
        from types import SimpleNamespace
        spec=importlib.util.spec_from_file_location('generation_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        paths,hashes=self.build();gold=dict(source_sha256=hashes,generated_normalized={k:cache.digest(p.read_bytes()) for k,p in paths.items()});self.calls.clear();shutil.rmtree(self.cached)
        manifest=dict(suite='fixture',package_id='fixture',purpose='sealed',golden=gold)
        with patch.object(cli,'ROOT',self.root),patch.object(cli,'verify_package',return_value=manifest),patch.dict(cli.SUITES,fixture=dict(source='gpu/entry.slang')),patch.object(cli,'module',return_value=SimpleNamespace(normalized=cache.digest)):
            first=cli.generation_capture(self.root/'cold');self.assertFalse(first['cache_hit']);self.assertEqual(first['compiler_invocations'],2)
            second=cli.generation_capture(self.root/'warm');self.assertTrue(second['cache_hit']);self.assertEqual(second['compiler_invocations'],0)
            for folder in ('cold','warm'):
                capture=self.root/folder;cli.write(capture/'run.json',dict(mode='gpu'));cli.write(capture/'runtime.json',dict(generation_cache_enabled=True,generation_cache_required=folder=='warm'));self.assertTrue(cli.audit_generation_capture(manifest,capture)['verified'])
            capture=self.root/'warm';rows=(capture/'phases.jsonl').read_text();(capture/'phases.jsonl').write_text(rows+json.dumps(dict(stage='slang_compiler',state='entered'))+'\n')
            with self.assertRaisesRegex(ValueError,'invocation'):cli.audit_generation_capture(manifest,capture)
        self.assertEqual(self.calls,['cuda','metal'])
