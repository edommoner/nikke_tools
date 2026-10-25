"""Snapshots reject stale/corrupt data without importing device APIs."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_metal_cache import key_for
from portable_metal_cache_probe import probe
class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.source=b'shared generated MSL';self.consumer=b'swift';self.arc=b'archive';h=lambda b:hashlib.sha256(b).hexdigest()
        identity=dict(schema='1',source_sha256=h(self.source),consumer_sha256=h(self.consumer),entry='portableEvents',resident_stride='138952',threads_per_threadgroup='1',math_mode='safe',registry_id='42',device='Apple test',os_build='recorded build');self.key=key_for(identity)
        self.receipt=dict(schema=1,enabled=True,required=False,hit=False,native_archive_miss_rejected=True,identity=identity,key=self.key,archive_bytes=len(self.arc),archive_sha256=h(self.arc),archive_compile_seconds=90.)
        self.transport=dict(pipeline_cache=self.receipt,runtime_stride_bytes=138952,registry_id='42',device='Apple test',pipeline_os_build='recorded build')
        self.record=self.root/(self.key+'.json');self.archive=self.root/(self.key+'.metalarc');self.archive.write_bytes(self.arc);self.record.write_text(json.dumps({k:self.receipt[k] for k in ['identity','archive_bytes','archive_sha256']}))
    def run_probe(self):return probe(self.root,self.transport,self.source,self.consumer)
    def test_hit_is_only_advisory_and_does_not_certify_device_or_calculation(self):
        d=self.run_probe();self.assertTrue(d['hit_snapshot']);self.assertFalse(d['calculation_verified']);self.assertFalse(d['context_current_verified']);self.assertTrue(d['native_cache_revalidation_required']);self.assertEqual((d['gpu_calls'],d['compiler_calls'],d['driver_calls']),(0,0,0))
    def test_changed_source_and_consumer_reject_before_cache_use(self):
        self.assertFalse(probe(self.root,self.transport,self.source+b'x',self.consumer)['hit_snapshot']);self.assertFalse(probe(self.root,self.transport,self.source,self.consumer+b'x')['hit_snapshot'])
    def test_corrupt_same_size_archive_is_not_a_hit(self):
        self.archive.write_bytes(b'Archive');self.assertFalse(self.run_probe()['hit_snapshot'])
    def test_missing_or_changed_metadata_is_not_a_hit(self):
        self.record.write_text('{}');self.assertFalse(self.run_probe()['hit_snapshot']);self.record.unlink();self.assertFalse(self.run_probe()['hit_snapshot'])
    def test_symlink_members_are_rejected(self):
        real=self.root/'other';self.archive.rename(real);self.archive.symlink_to(real);self.assertFalse(self.run_probe()['hit_snapshot'])
if __name__=='__main__':unittest.main()
