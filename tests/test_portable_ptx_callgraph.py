"""Cached PTX topology is read-only, anchored, and explicitly incomplete for pointers."""
import base64,hashlib,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_ptx_callgraph import callgraph_statistics
from portable_ptx_stats import ptx_statistics,saved_ptx_statistics

PTX=b'''// call ghost; .func ghost() {}
.extern .func ext(.param .b64 arg);
.visible .entry kernel(.param .u64 arg) {
 .reg .b32 %r<3>;
 .reg .pred %p;
 @%p call.uni (retval), a, (arg);
 call a;
 ret;
}
.func a() {
 ld.global.u32 %r0, [addr];
 call b, (arg);
 ret;
}
.func b() {
 call a;
 st.local.u32 [addr], %r0;
 ret;
}
.func unrelated() { ret; }
'''


class PTXCallgraphTests(unittest.TestCase):
    def test_direct_calls_cycles_repeated_edges_and_entry_closure(self):
        result=callgraph_statistics(PTX);rows={r['name']:r for r in result['function_rows']}
        self.assertTrue(result['direct_graph_complete']);self.assertFalse(result['partition_legal_verified'])
        self.assertFalse(result['compiler_memory_attribution_verified']);self.assertFalse(result['compiler_verified']);self.assertFalse(result['calculation_verified'])
        self.assertEqual(rows['kernel']['direct_calls'],dict(a=2));self.assertEqual(rows['a']['direct_calls'],dict(b=1))
        self.assertEqual(result['cyclic_components'],[['a','b']])
        self.assertEqual(result['entry_closures'],[dict(entry='kernel',defined_function_count=3,functions=['a','b','kernel'])])
        self.assertEqual(rows['a']['load_store_opcodes'],{'ld.global.u32':1})
        self.assertEqual(rows['b']['load_store_opcodes'],{'st.local.u32':1})
        self.assertEqual(result['functions'],ptx_statistics(PTX)['functions'])
        self.assertEqual(rows['kernel']['virtual_register_count'],4)

    def test_indirect_named_pointer_external_and_unknown_are_never_complete(self):
        variants=[(b'.func f() { .reg .b64 %fp; call %fp, (arg), proto; ret; }','indirect_call_count'),
                  (b'.func f(.reg .b64 fp) { call fp, proto; ret; }','indirect_call_count'),
                  (b'.func f() { .reg .b64 first, pointer; call pointer, proto; ret; }','indirect_call_count'),
                  (b'.extern .func ext(); .func f() { call ext; ret; }','external_symbols'),
                  (b'.func f() { call missing; ret; }','unresolved_symbols')]
        for raw,key in variants:
            # Function directives start a line, as the existing NVRTC parser requires.
            raw=raw.replace(b'; .func',b';\n.func')
            with self.subTest(key=key,raw=raw):
                result=callgraph_statistics(raw);self.assertFalse(result['direct_graph_complete']);self.assertTrue(result[key])
                self.assertFalse(result['partition_legal_verified'])

    def test_malformed_unsupported_calls_and_duplicate_symbols_fail_closed(self):
        for raw in (b'.func f() { call.nope foo; }',b'.func f() { call foo }',
                    b'.func f() { call (x), ; }',b'.func f() { call foo, (x)junk; }',
                    b'.func f() { call %fp, (x); }',b'.func f() {}\n.func f() {}'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):callgraph_statistics(raw)

    def test_lexical_strings_comments_and_body_hashes_do_not_add_calls(self):
        raw=b'.func f() {\n // call bad;\n .pragma "call fake;";\n ret;\n}'
        result=callgraph_statistics(raw)
        self.assertTrue(result['direct_graph_complete']);self.assertEqual(result['function_rows'][0]['direct_calls'],{})
        self.assertNotEqual(result['function_rows'][0]['definition_sha256'],callgraph_statistics(raw.replace(b'bad',b'different'))['function_rows'][0]['definition_sha256'])
        self.assertEqual(result['function_rows'][0]['line'],1)

    def test_real_cli_saved_cache_receipt_integrity_and_no_output_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);identity=dict(schema=1,artifact='ptx',options=['--fmad=false'])
            key=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            receipt=dict(key=key,identity=identity,artifact_bytes=len(PTX),artifact_sha256=hashlib.sha256(PTX).hexdigest())
            cache=p/(key+'.json');cache.write_text(json.dumps(dict(identity=identity,artifact_bytes=len(PTX),artifact_sha256=receipt['artifact_sha256'],artifact_base64=base64.b64encode(PTX).decode())))
            phases=p/'phases.jsonl';phases.write_text(json.dumps(dict(stage='cuda_compile_cache',state='verified',receipt=receipt))+'\n')
            before=cache.read_bytes(),phases.read_bytes();output=p/'report.json'
            command=[sys.executable,str(ROOT/'scripts/nikke_gpu.py'),'ptx-stats','--cache-entry',str(cache),'--phases',str(phases),'--out',str(output),'--callgraph']
            result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(output.read_text());self.assertTrue(report['receipt_match']);self.assertTrue(report['callgraph']['direct_graph_complete'])
            self.assertEqual(report['cache_key'],key)
            self.assertEqual(report['gpu_calls'],0);self.assertEqual(report['nvrtc_compile_calls'],0)
            self.assertEqual(before,(cache.read_bytes(),phases.read_bytes()));original=output.read_bytes()
            again=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=15)
            self.assertNotEqual(again.returncode,0);self.assertEqual(output.read_bytes(),original)
            phases.write_text(phases.read_text().replace(receipt['artifact_sha256'],'0'*64))
            with self.assertRaisesRegex(ValueError,'receipt mismatch'):saved_ptx_statistics(cache,phases,callgraph=True)
