"""Native comparisons cannot be replaced by hashes or an address exclusion."""
import contextlib,copy,hashlib,json,struct,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import portable_partitioned_native as audit
import portable_partitioned_addresses as addresses
import portable_partitioned_transport as transport


def sha(raw):return hashlib.sha256(raw).hexdigest()


class NativeAuditTests(unittest.TestCase):
    def fixture(self,root,status=0,domain=True):
        raw=bytearray(addresses.WORDS*4);struct.pack_into('<I',raw,0,status)
        packed=struct.pack('<II',1,123)
        (root/'input.bin').write_bytes(packed);(root/'readback.bin.partial').write_bytes(raw)
        (root/'run.json').write_text(json.dumps(dict(batch_size=16)))
        p=root/'readback.bin.batches';p.mkdir();(p/'plan.json').write_text(json.dumps(transport.plan(packed,1,addresses.WORDS,16,runtime_stride=143048)))
        generated=root/'research/portable-build';generated.mkdir(parents=True)
        for suffix in ('cu','metal'):(generated/('entry.'+suffix)).write_bytes(suffix.encode())
        (root/'generation-preflight.json').write_text(json.dumps(dict(generation=dict(artifacts={k:dict(sha256=sha(v.encode()),bytes=len(v)) for k,v in [('cuda','cu'),('metal','metal')]}))))
        calls=[]
        def compare(block,d):calls.append(('native',block[0],d));return dict(native=1)
        def reject(block,name):calls.append(('reject',block[0],name))
        adapter=SimpleNamespace(suite=SimpleNamespace(INPUT=1),cross=SimpleNamespace(digest=lambda x:sha(json.dumps(x,sort_keys=True).encode()),normalized=sha),compare=compare,validate_rejection=reject,validate_rejection_stage=lambda b,n:calls.append(('stage',n)))
        entries=[('one',[123],object() if domain else None)]
        native=dict(native=1) if domain else dict(status=64)
        row=dict(name='one',input_sha256=sha(packed[4:]),output_sha256=sha(raw),native_sha256=adapter.cross.digest(native))
        m=dict(suite='frozen',golden=dict(input_sha256=sha(packed),output_sha256=sha(raw),entries=[row],generated_normalized=dict(cuda=sha(b'cu'),metal=sha(b'metal'))))
        cli=SimpleNamespace(ROOT=root,forbid_gpu=contextlib.nullcontext,open_suite=lambda m:adapter,prepare_entries=lambda a,m:(entries,packed),sha=sha,load=lambda p:json.loads(p.read_text()),SUITES={'frozen':dict(source='gpu/entry.slang',require_rejection_stage=True)},comparison_exception_details=lambda e:type(e).__name__+': '+str(e))
        return cli,m,calls,adapter,raw

    def test_fresh_native_comparator_is_required_and_original_raw_is_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);cli,m,calls,_,raw=self.fixture(root)
            result=audit.compare(cli,m,root,root)
            self.assertTrue(result['calculation_verified']);self.assertEqual(result['native_oracles'],1)
            self.assertEqual(calls[0][:2],('native',0));self.assertEqual((root/'readback.bin.partial').read_bytes(),raw)
            self.assertFalse(result['live_parent_receipt_present']);self.assertEqual(result['gpu_calls'],0)

    def test_rejection_uses_original_status_and_stage_validators(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);cli,m,calls,_,_=self.fixture(root,64,False)
            self.assertTrue(audit.compare(cli,m,root,root)['calculation_verified'])
            self.assertEqual(calls,[('reject',64,'one'),('stage','one')])

    def test_native_failure_cannot_pass_even_when_entire_output_hash_matches(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);cli,m,_,adapter,_=self.fixture(root)
            adapter.compare=lambda b,d:(_ for _ in ()).throw(AssertionError('semantic mismatch'))
            r=audit.compare(cli,m,root,root)
            self.assertFalse(r['calculation_verified']);self.assertIn('semantic mismatch',r['mismatches'][0]['reason'])

    def test_expected_native_fingerprint_cannot_be_replaced(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);cli,m,_,_,_=self.fixture(root);m['golden']['entries'][0]['native_sha256']='0'*64
            self.assertFalse(audit.compare(cli,m,root,root)['calculation_verified'])

    def test_bad_input_generated_artifact_or_status_is_not_accepted(self):
        for kind in ('input','generated','status'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);cli,m,_,_,_=self.fixture(root,status=8 if kind=='status' else 0)
                if kind=='input':(root/'input.bin').write_bytes(b'wrong')
                if kind=='generated':(root/'research/portable-build/entry.cu').write_bytes(b'wrong')
                if kind=='status':self.assertFalse(audit.compare(cli,m,root,root)['calculation_verified'])
                else:
                    with self.assertRaises(ValueError):audit.compare(cli,m,root,root)

    def test_budget_rejected_before_any_audit_or_claim(self):
        for budget in (0,241,True):
            with self.assertRaisesRegex(ValueError,'Bounded'):audit.run(None,None,None,None,budget)

    def test_subsets_are_never_full_calculation_proofs(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);cli,m,_,_,_=self.fixture(root)
            r=audit.compare(cli,m,root,root,[0],root/'progress.jsonl')
            self.assertFalse(r['calculation_verified']);self.assertTrue(r['comparison_subset_verified'])
            self.assertEqual(r['case_indices'],[0]);self.assertIn('fresh_native_compare',(root/'progress.jsonl').read_text())

    def test_aggregate_requires_exact_coverage_distinct_children_and_identical_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);cli,m,_,_,_=self.fixture(root)
            r=audit.compare(cli,m,root,root,[0]);r.update(child_pid=999001,elapsed_seconds=1.)
            wire=dict(input_count=1,input_sha256=r['input_sha256'],raw_joined_output_sha256=r['raw_output_sha256'],logical_view_sha256=r['logical_output_sha256'],logical_address_changes=[],active_references_checked=0)
            self.assertTrue(audit.aggregate(m,wire,[r],[[0]],240,999002)['calculation_verified'])
            for field,value in [('calculation_verified',True),('case_indices',[]),('raw_output_sha256','0'*64),('entries',[]),('live_parent_receipt_present',True),('elapsed_seconds',242.),('child_pid',999002),('gpu_calls',1)]:
                bad=copy.deepcopy(r);bad[field]=value
                with self.subTest(field=field),self.assertRaises(ValueError):audit.aggregate(m,wire,[bad],[[0]],240,999002)
            with self.assertRaises(ValueError):audit.aggregate(m,wire,[],[[0]],240,999002)


if __name__=='__main__':unittest.main()
