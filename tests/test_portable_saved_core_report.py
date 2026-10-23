"""Sanitized report audits cannot promote claimed readback or environment proof."""
import copy,hashlib,importlib.util,json,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_saved_core_report import audit
s=importlib.util.spec_from_file_location('saved_report_strict_cross',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
GOLDEN=json.loads((ROOT/'research/portable-damage-accum-core-short-expected.json').read_text());MANIFEST='e7c93111b6acb67f312df3c617bc8b21dc5778fc6ae9cfcd806ef3eaf1226448'
class SavedReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'report';shutil.copytree(ROOT/'tests/fixtures/cuda-core-report-v4',self.root)
    def run_audit(self,anchor=MANIFEST):return audit(self.root,GOLDEN,cross.normalized,anchor)
    def change(self,name,fn):
        p=self.root/name;d=json.loads(p.read_text());fn(d);data=(json.dumps(d,indent=2)+'\n').encode();p.write_bytes(data)
        mpath=self.root/'manifest.json';m=json.loads(mpath.read_text());row=next(r for r in m['files'] if r['path']==name);row['export']=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest());raw=(json.dumps(m,indent=2)+'\n').encode();mpath.write_bytes(raw);return hashlib.sha256(raw).hexdigest()
    def test_verified_report_stays_distinct_from_independent_cuda_raw_proof(self):
        r=self.run_audit();self.assertTrue(r['passed']);self.assertEqual((r['files'],r['bytes'],r['inputs']),(26,201729,41));self.assertFalse(r['CUDA_raw_independently_audited']);self.assertFalse(r['compiled_CUBIN_independently_audited']);self.assertFalse(r['calculation_verified']);self.assertFalse(r['environment_preservation_verified']);self.assertEqual(r['gpu_calls'],0)
    def test_trusted_manifest_and_payload_fingerprints_are_required(self):
        with self.assertRaises(ValueError):self.run_audit('0'*64)
        p=self.root/'gpu/proof/comparison.json';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaises(ValueError):self.run_audit()
    def test_self_consistent_export_cannot_change_native_or_quantity_fingerprints(self):
        anchor=self.change('gpu/proof/comparison.json',lambda d:d['entries'][0].__setitem__('native_sha256','0'*64))
        with self.assertRaises(ValueError):self.run_audit(anchor)
    def test_cold_and_warm_cache_receipts_cannot_change_artifact_identity(self):
        anchor=self.change('cache-check.json',lambda d:d['cache'].__setitem__('artifact_sha256','0'*64))
        with self.assertRaises(ValueError):self.run_audit(anchor)
    def test_environment_cause_cannot_be_promoted(self):
        anchor=self.change('saved-observation-counts.json',lambda d:d.__setitem__('cause','gaming'))
        with self.assertRaises(ValueError):self.run_audit(anchor)
    def test_layout_fault_is_rejected(self):
        anchor=self.change('gpu/proof/evidence.json',lambda d:d['resident_runtime'].__setitem__('stride',16))
        with self.assertRaises(ValueError):self.run_audit(anchor)
    def test_reported_input_count_fault_is_rejected(self):
        anchor=self.change('gpu/proof/comparison.json',lambda d:d.__setitem__('input_count',40))
        with self.assertRaises(ValueError):self.run_audit(anchor)
    def test_preservation_claim_cannot_hide_missing_processes(self):
        self.change('safe-summary.json',lambda d:d.__setitem__('environment_preservation_verified',True))
        self.change('gpu/stage-result.json',lambda d:d.__setitem__('whole_stage_environment_preservation_verified',True))
        self.change('saved-observation-counts.json',lambda d:d.__setitem__('original_environment_preservation_verified',True))
        p=self.root/'manifest.json';d=json.loads(p.read_text());d['environment_preservation_verified']=True;raw=json.dumps(d).encode();p.write_bytes(raw)
        with self.assertRaises(ValueError):self.run_audit(hashlib.sha256(raw).hexdigest())
    def test_paths_cannot_escape_manifest_root(self):
        p=self.root/'manifest.json';m=json.loads(p.read_text());m['files'][0]['path']='../safe-summary.json';raw=json.dumps(m).encode();p.write_bytes(raw)
        with self.assertRaises(ValueError):self.run_audit(hashlib.sha256(raw).hexdigest())
if __name__=='__main__':unittest.main()
