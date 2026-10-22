"""Function-byte/ABI/single-owner PTX candidate checks, never an assembler proof."""
import base64,copy,hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_ptx_partition import partition_candidate,saved_partition,audit_partition
from portable_ptx_stats import function_records

PTX=b'''// saved producer; this file is never rewritten
.version 8.4
.target sm_86
.address_size 64
.func (.param .b32 r) leaf(.param .align 8 .b8 renamed[16]);
.visible .const .align 8 .b8 SLANG_globalParams[48];
.global .align 4 .u32 table[2] = {1, 2};
.func (.param .b32 r) leaf(.param .align 8 .b8 data[16]) {
 .reg .b32 %r<2>;
 ld.const.u32 %r0, [SLANG_globalParams];
 ret;
}
.func focus(.param .b64 ptr) {
 .reg .b64 %rd<12>;
 // body marker must survive exactly
 call (result), leaf, (arg);
 ret;
}
.visible .entry kernel(.param .b64 ptr) .maxntid 1, 1, 1 {
 call focus, (ptr);
 ret;
}
'''


def cache_files(folder,raw=PTX):
    identity=dict(schema=1,artifact='ptx',options=['--fmad=false']);key=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest();digest=hashlib.sha256(raw).hexdigest()
    cache=folder/(key+'.json');cache.write_text(json.dumps(dict(identity=identity,artifact_bytes=len(raw),artifact_sha256=digest,artifact_base64=base64.b64encode(raw).decode())))
    receipt=dict(key=key,identity=identity,artifact_bytes=len(raw),artifact_sha256=digest)
    phases=folder/'phases.jsonl';phases.write_text(json.dumps(dict(stage='cuda_compile_cache',state='verified',receipt=receipt))+'\n')
    return cache,phases


class PTXPartitionTests(unittest.TestCase):
    def test_all_bodies_and_definition_parameter_names_remain_in_one_owner(self):
        report,units=partition_candidate(PTX)
        self.assertEqual(report['focus'],'focus');self.assertEqual(report['definitions'],3)
        self.assertTrue(report['function_body_abi_coverage_verified']);self.assertFalse(report['partition_legal_verified']);self.assertFalse(report['compiler_verified']);self.assertFalse(report['calculation_verified'])
        original={r['name']:PTX.decode()[r['body_start']:r['end']] for r in function_records(PTX) if r['body'] is not None};found={}
        for name,raw in units.items():
            for r in function_records(raw):
                if r['body'] is not None:
                    self.assertNotIn(r['name'],found);found[r['name']]=raw.decode()[r['body_start']:r['end']]
            self.assertNotIn(b'renamed',raw) # prototype name must not replace the definition's data name
        self.assertEqual(found,original);self.assertIn(b'data[16]',units['remainder.ptx'])
        self.assertIn(b'.extern .func (.param .b32 r) leaf',units['focus.ptx'])
        self.assertIn(b'.visible .func (.param .b32 r) leaf',units['remainder.ptx'])

    def test_constant_and_initialized_global_have_only_remainder_definitions(self):
        report,units=partition_candidate(PTX,'focus')
        self.assertEqual({g['name']:g['owner'] for g in report['global_state']},dict(SLANG_globalParams='remainder',table='remainder'))
        self.assertIn(b'.extern .global .align 4 .u32 table[2];',units['focus.ptx'])
        self.assertNotIn(b'{1, 2}',units['focus.ptx']);self.assertIn(b'.visible .global .align 4 .u32 table[2] = {1, 2};',units['remainder.ptx'])
        self.assertIn(b'.maxntid 1, 1, 1',units['remainder.ptx'])

    def test_abi_mismatch_weak_external_or_unknown_module_state_fail_closed(self):
        variants=[PTX.replace(b'renamed[16]',b'renamed[8]'),PTX.replace(b'.global .align 4',b'.weak .global .align 4'),PTX.replace(b'.global .align 4',b'.extern .global .align 4'),PTX+b'\n.section .debug_info {}\n',PTX.replace(b'.func focus(',b'.weak .func focus('),PTX.replace(b'.func focus(',b'.extern .func focus(')]
        for raw in variants:
            with self.subTest(raw=raw[-60:]),self.assertRaises(ValueError):partition_candidate(raw,'focus')
        for focus in ('missing','kernel'):
            with self.assertRaises(ValueError):partition_candidate(PTX,focus)

    def test_function_pointer_table_follows_prototypes_and_has_single_data_owner(self):
        raw=PTX.replace(b'{1, 2}',b'{focus, leaf}')
        _,units=partition_candidate(raw,'focus');remainder=units['remainder.ptx']
        self.assertLess(remainder.index(b'.extern .func focus'),remainder.index(b'table[2] = {focus, leaf}'))
        self.assertLess(remainder.index(b'.visible .func (.param .b32 r) leaf'),remainder.index(b'table[2] = {focus, leaf}'))

    def test_saved_integrity_failure_is_retained_and_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);cache,phases=cache_files(root);before=cache.read_bytes(),phases.read_bytes();out=root/'bad'
            with self.assertRaises(ValueError):saved_partition(cache,phases,out,'missing')
            original=(out/'plan.json').read_bytes();self.assertFalse(json.loads(original)['passed'])
            self.assertEqual(sorted(p.name for p in out.iterdir()),['plan.json'])
            with self.assertRaises(FileExistsError):saved_partition(cache,phases,out,'focus')
            self.assertEqual(original,(out/'plan.json').read_bytes());self.assertEqual(before,(cache.read_bytes(),phases.read_bytes()))
            phases.write_text(phases.read_text().replace(hashlib.sha256(PTX).hexdigest(),'0'*64))
            with self.assertRaisesRegex(ValueError,'receipt mismatch'):saved_partition(cache,phases,root/'bad-receipt','focus')

    def test_real_cli_makes_only_local_cpu_candidate_and_report(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);cache,phases=cache_files(root);before=cache.read_bytes(),phases.read_bytes();out=root/'candidate'
            command=[sys.executable,str(ROOT/'scripts/nikke_gpu.py'),'ptx-partition','--cache-entry',str(cache),'--phases',str(phases),'--out',str(out),'--function','focus']
            r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=15);self.assertEqual(r.returncode,0,r.stderr)
            plan=json.loads((out/'plan.json').read_text());self.assertTrue(plan['passed']);self.assertTrue(plan['receipt_match'])
            self.assertEqual(set(p.name for p in out.iterdir()),{'plan.json','focus.ptx','remainder.ptx'})
            for artifact in plan['artifacts']:
                raw=(out/artifact['path']).read_bytes();self.assertEqual(len(raw),artifact['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),artifact['sha256'])
            for key in ('nvrtc_calls','ptxas_calls','link_calls','driver_calls','gpu_calls'):self.assertEqual(plan[key],0)
            self.assertEqual(before,(cache.read_bytes(),phases.read_bytes()))

    def test_audit_does_not_trust_rehashed_candidate_or_edited_plan(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);cache,phases=cache_files(root);out=root/'candidate'
            saved_partition(cache,phases,out,'focus');self.assertTrue(audit_partition(cache,phases,out)['cpu_audit_verified'])
            original=(out/'plan.json').read_bytes();raw=(out/'focus.ptx').read_bytes();changed=raw.replace(b'%rd<12>',b'%rd<13>');self.assertNotEqual(raw,changed)
            (out/'focus.ptx').write_bytes(changed);plan=json.loads(original)
            plan['artifacts'][0].update(bytes=len(changed),sha256=hashlib.sha256(changed).hexdigest());(out/'plan.json').write_text(json.dumps(plan))
            with self.assertRaises(ValueError):audit_partition(cache,phases,out)
            (out/'plan.json').write_bytes(original)
            with self.assertRaises(ValueError):audit_partition(cache,phases,out)
            (out/'focus.ptx').write_bytes(raw);self.assertTrue(audit_partition(cache,phases,out)['passed'])
