"""Saved PTX diagnostics cannot compile or promote arithmetic verification."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from portable_ptx_stats import ptx_statistics,saved_ptx_statistics

PTX=b'''// .entry ignored() { .reg .b32 fake<1000>; }
.extern .func (.param .b32 result) forward(.param .b32 input);
.visible .entry kernel(.param .u64 arg) {
 .reg .b32 temp_param_reg;
 .reg .b32 %r<3>, ordinary;
 .reg .pred %p<2>;
 .reg .v2 .b64 %wide;
 .local .align 8 .b8 depot[16];
 proto: .callprototype (.reg .b32 result) _ (.reg .b32 input);
 { .reg .b32 nested; }
 ret;
}
.func (.param .b32 result) helper() {
 .local .align 8 .b64 matrix[2][3];
 ret;
}
'''


class PTXStatisticsTests(unittest.TestCase):
    def test_optional_percent_vectors_nested_scope_and_call_prototype(self):
        result=ptx_statistics(PTX+b'\0')
        self.assertEqual(result['functions'],2)
        helper,kernel=result['largest_functions']
        self.assertEqual(helper['name'],'helper');self.assertEqual(helper['declared_local_bytes'],48)
        self.assertEqual(kernel['virtual_registers'],dict(b32=6,pred=2,b64=2))
        self.assertEqual(kernel['declared_local_bytes'],16);self.assertEqual(kernel['line'],3)

    def test_unknown_or_malformed_input_never_returns_partial_estimates(self):
        for raw in (b'.entry bad() {',b'.entry bad() { .reg .b32 nope<unknown>; }',
                    b'.entry bad() { .local .b8 depot[]; }',b'.extern .func forward();'):
            with self.assertRaises(ValueError):ptx_statistics(raw)
        for top in (0,51,True):
            with self.assertRaises(ValueError):ptx_statistics(PTX,top=top)

    def test_cache_and_receipt_bytes_are_required_and_remain_unchanged(self):
        with tempfile.TemporaryDirectory() as f:
            root=Path(f);identity=dict(schema=1,artifact='ptx',options=['--fmad=false'])
            key=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            receipt=dict(key=key,identity=identity,artifact_bytes=len(PTX),artifact_sha256=hashlib.sha256(PTX).hexdigest())
            cache=root/(key+'.json');phases=root/'phases.jsonl'
            cache.write_text(json.dumps(dict(identity=identity,artifact_bytes=len(PTX),artifact_sha256=receipt['artifact_sha256'],artifact_base64=base64.b64encode(PTX).decode())))
            phases.write_text(json.dumps(dict(stage='cuda_compile_cache',state='verified',receipt=receipt))+'\n')
            before=(cache.read_bytes(),phases.read_bytes());r=saved_ptx_statistics(cache,phases)
            self.assertTrue(r['receipt_match']);self.assertFalse(r['calculation_verified'])
            self.assertFalse(r['compiler_verified']);self.assertEqual(r['nvrtc_compile_calls'],0);self.assertEqual(r['gpu_calls'],0)
            self.assertEqual(before,(cache.read_bytes(),phases.read_bytes()))
            spec=importlib.util.spec_from_file_location('ptx_stats_cli',Path(__file__).resolve().parents[1]/'scripts/nikke_gpu.py')
            cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
            output=root/'stats.json';self.assertEqual(cli.ptx_statistics(cache,phases,output),r)
            with self.assertRaisesRegex(ValueError,'already exists'):cli.ptx_statistics(cache,phases,output)
            phases.write_text(phases.read_text().replace(receipt['artifact_sha256'],'0'*64))
            with self.assertRaisesRegex(ValueError,'receipt mismatch'):saved_ptx_statistics(cache,phases)
            phases.write_bytes(before[1]);cache.write_bytes(cache.read_bytes().replace(base64.b64encode(PTX),base64.b64encode(PTX+b'x')))
            with self.assertRaisesRegex(ValueError,'corrupt'):saved_ptx_statistics(cache,phases)
            with self.assertRaises(ValueError):cli.ptx_statistics(cache,phases,root/'bad.json')
            self.assertFalse((root/'bad.json').exists())


if __name__=='__main__':unittest.main()
