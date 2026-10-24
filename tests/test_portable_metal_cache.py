"""Cache identity and native no-fallback evidence must survive saved audits."""
import copy,sys,unittest,subprocess,tempfile,importlib.util
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_metal_cache import verify,digest,key_for

class MetalCacheTests(unittest.TestCase):
    def fixture(self):
        source=b'kernel source';consumer=b'fixed Swift transport'
        identity=dict(schema='1',source_sha256=digest(source),consumer_sha256=digest(consumer),entry='portableEvents',resident_stride='138952',threads_per_threadgroup='1',math_mode='safe',registry_id='42',device='Apple test',os_build='test build')
        receipt=dict(schema=1,enabled=True,required=True,hit=True,key=key_for(identity),identity=identity,archive_sha256='a'*64,archive_bytes=1024,native_archive_miss_rejected=True,archive_compile_seconds=0.)
        return dict(device='Apple test',registry_id='42',runtime_stride_bytes=138952,pipeline_os_build='test build',pipeline_cache=receipt),dict(metal_pipeline_cache_enabled=True,metal_pipeline_cache_required=True),source,consumer
    def test_hit_uses_saved_identities_without_reading_external_cache(self):
        t,r,s,c=self.fixture();result=verify(t,r,s,c)
        self.assertTrue(result['hit']);self.assertFalse(result['external_cache_read']);self.assertFalse(result['calculation_verified'])
    def test_required_missing_or_native_fallback_is_rejected(self):
        t,r,s,c=self.fixture()
        for name,value in [('hit',False),('required',False),('native_archive_miss_rejected',False),('hit','true')]:
            changed=copy.deepcopy(t);changed['pipeline_cache'][name]=value
            with self.assertRaises(ValueError):verify(changed,r,s,c)
        t.pop('pipeline_cache')
        with self.assertRaises(ValueError):verify(t,r,s,c)
    def test_source_consumer_device_and_options_cannot_share_a_key(self):
        t,r,s,c=self.fixture()
        for name,value in [('source_sha256','b'*64),('consumer_sha256','b'*64),('registry_id','43'),('math_mode','fast'),('resident_stride','8'),('entry','other'),('threads_per_threadgroup','2'),('os_build','different build')]:
            changed=copy.deepcopy(t);identity=changed['pipeline_cache']['identity'];identity[name]=value;changed['pipeline_cache']['key']=key_for(identity)
            with self.assertRaises(ValueError):verify(changed,r,s,c)
    def test_bad_archive_metadata_and_warm_compile_are_rejected(self):
        t,r,s,c=self.fixture()
        for name,value in [('archive_bytes',0),('archive_bytes',True),('archive_sha256','invalid'),('archive_compile_seconds',1.),('archive_compile_seconds',float('nan'))]:
            changed=copy.deepcopy(t);changed['pipeline_cache'][name]=value
            with self.assertRaises(ValueError):verify(changed,r,s,c)
    def test_disabled_historical_transport_is_accepted(self):
        self.assertFalse(verify({}, {}, b's', b'c')['enabled'])
        t,r,s,c=self.fixture()
        with self.assertRaises(ValueError):verify(t,{},s,c)
    def test_explicit_cold_compile_is_not_a_hit(self):
        t,r,s,c=self.fixture();r['metal_pipeline_cache_required']=False;t['pipeline_cache'].update(required=False,hit=False,archive_compile_seconds=2.)
        self.assertFalse(verify(t,r,s,c)['hit'])
    def test_cli_rejects_wrong_backend_and_required_without_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            capture=Path(folder)/'capture'
            for options,message in [(['--backend','cuda','--metal-pipeline-cache',folder],'Metal pipeline settings require Metal backend'),(['--backend','metal','--require-metal-pipeline-cache'],'requires --metal-pipeline-cache')]:
                result=subprocess.run([sys.executable,str(ROOT/'scripts/nikke_gpu.py'),'run','--capture',str(capture),*options],cwd=ROOT,capture_output=True,text=True,timeout=15)
                self.assertNotEqual(result.returncode,0);self.assertIn(message,result.stderr);self.assertFalse(capture.exists())
    def test_replay_cannot_replace_the_metal_cache_auditor(self):
        spec=importlib.util.spec_from_file_location('cache_replay_control',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        names=['app/portable_backend.py','app/portable_compile_cache.py','scripts/run-metal-probe.swift',
               'research/portable_phase_audit.py','research/summarize-portable-cross-gpu.py',
               'app/detail_gpu.py','app/engine_worker.py','app/effect_spec.py','app/engine_compat.py','app/portable_metal_cache.py']
        original=dict(purpose='development',suite='attack-group-native-route',golden={},files=[dict(path=n,sha256='a'*64) for n in names])
        changed=copy.deepcopy(original);changed['files'][-1]['sha256']='b'*64
        with patch.object(cli,'verify_package',return_value=original):
            with self.assertRaisesRegex(ValueError,'GPU transport, source, normalizer or canonical reference changed'):
                cli.replay_source(changed,Path('/unread-source'),Path('/unread-capture'))

if __name__=='__main__':unittest.main()
