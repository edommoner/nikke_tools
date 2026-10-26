"""Generator extraction preserves code; transport edits cannot force Slang work."""
import ast,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'tests')]
import portable_backend as backend
import portable_slang_generation as generator
import portable_generation_cache as cache
import test_portable_generation_cache as fixtures
from portable_arena_transport_source_contract import historical_backend_source

def fingerprint(node):return hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()

class RestoreRoot(ast.NodeTransformer):
    def visit_Name(self,node):
        if node.id=='root':node.id='ROOT'
        return node
    def visit_FunctionDef(self,node):
        self.generic_visit(node)
        if node.name in ('source_hashes','build','_build_resident'):
            assert node.args.args[0].arg=='root';node.args.args.pop(0)
        return node
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Name) and node.func.id in ('source_hashes','_build_resident'):
            assert isinstance(node.args[0],ast.Name) and node.args[0].id=='ROOT';node.args.pop(0)
        return node

def historical_transport_fingerprint(node):
    """Undo only a68a80f's explicit typed-readback stride for the old proof.

    That later commit admitted 1048576 words in these two guards. Preserve the
    original extraction fixture and compare every other AST node unchanged.
    This helper is a historical source test, never a generated-code normalizer.
    """
    node=copy.deepcopy(node)
    if node.name in ('execute','execute_batches'):
        matches=[n for n in ast.walk(node) if isinstance(n,ast.Compare)
                 and isinstance(n.left,ast.Name) and n.left.id=='output_words'
                 and len(n.ops)==1 and isinstance(n.ops[0],ast.NotIn)
                 and len(n.comparators)==1 and isinstance(n.comparators[0],ast.Tuple)]
        if len(matches)!=1:raise ValueError('Typed readback stride guard absent or ambiguous')
        values=matches[0].comparators[0].elts
        if [n.value if isinstance(n,ast.Constant) else None for n in values]!=[655360,786432,1048576]:
            raise ValueError('Unexpected typed readback stride contract')
        values.pop()
    return fingerprint(node)

class GenerationSeparationTests(unittest.TestCase):
    def helper(self):
        h=fixtures.GenerationCacheTests();h.setUp();self.addCleanup(h.doCleanups);return h

    def test_exact_ast_extraction_preserves_compiler_options_publish_and_all_transport_functions(self):
        proof=json.loads((ROOT/'tests/fixtures/portable-generation-extraction.json').read_text())
        functions={n.name:n for n in ast.parse((ROOT/'app/portable_slang_generation.py').read_text()).body if isinstance(n,ast.FunctionDef)}
        self.assertEqual(set(functions),set(proof['generation_functions']))
        self.assertEqual({name:fingerprint(RestoreRoot().visit(node)) for name,node in functions.items()},proof['generation_functions'])
        other={n.name:historical_transport_fingerprint(n) for n in ast.parse(historical_backend_source(ROOT)).body if isinstance(n,ast.FunctionDef) and n.name not in functions}
        self.assertEqual(other,proof['other_backend_functions'])

    def test_historical_stride_projection_cannot_hide_a_different_capacity_or_transport(self):
        node=next(n for n in ast.parse(historical_backend_source(ROOT)).body if isinstance(n,ast.FunctionDef) and n.name=='execute')
        expected=historical_transport_fingerprint(node)
        changed=copy.deepcopy(node)
        guard=next(n for n in ast.walk(changed) if isinstance(n,ast.Constant) and n.value==1048576);guard.value=1048575
        with self.assertRaisesRegex(ValueError,'stride contract'):historical_transport_fingerprint(changed)
        changed=copy.deepcopy(node)
        error=next(n for n in ast.walk(changed) if isinstance(n,ast.Constant) and n.value=='Invalid portable word strides');error.value='different validation'
        self.assertNotEqual(historical_transport_fingerprint(changed),expected)

    def test_composed_transport_review_cannot_hide_guard_or_dispatch_changes(self):
        source=(ROOT/'app/portable_backend.py').read_text()
        for old,new in [('from portable_wire_layout import MAX_INPUT_WORDS,MAX_OUTPUT_WORDS,LARGE_OUTPUT_WORDS','from portable_wire_layout import MAX_INPUT_WORDS,MAX_OUTPUT_WORDS,LARGE_OUTPUT_WORDS\nMAX_OUTPUT_WORDS=2621440'),
                ('source!=\'gpu/world_coordinate_composed_entry.slang\'','source!=\'gpu/world_attack_group_entry.slang\''),
                ('validate_composed_stride(source,input_words,output_words)','validate_composed_stride(source,input_words,1048576)'),
                ('Invalid portable word strides','Ignored portable word strides'),
                ('gpu_execution_verified=True','gpu_execution_verified=False')]:
            self.assertIn(old,source)
            with self.subTest(old=old),self.assertRaises(ValueError):historical_backend_source(ROOT,source.replace(old,new,1))

    def test_wire_dependency_is_reviewed_not_an_unchecked_import(self):
        from portable_coordinate_resident_arc_source_contract import project_sources
        name='app/portable_wire_layout.py'
        with self.assertRaises(AssertionError):project_sources(ROOT,{name:(ROOT/name).read_text()+'\nMAX_OUTPUT_WORDS=2621440\n'})

    def test_transport_only_edits_keep_key_pair_and_required_hit_without_compilation(self):
        h=self.helper();paths,hashes=h.build();receipt=h.receipt();before={k:p.read_bytes() for k,p in cache.artifact_paths(paths).items()}
        p=h.root/'app/portable_backend.py';p.write_bytes(p.read_bytes()+b'\n# synthetic transport-only edit\n')
        paths,_=h.build(True);self.assertEqual(h.calls,['cuda','metal']);self.assertTrue(h.receipt()['hit']);self.assertEqual(h.receipt()['key'],receipt['key'])
        self.assertNotIn('app/portable_backend.py',h.receipt()['identity']['consumers'])
        self.assertEqual(before,{k:p.read_bytes() for k,p in cache.artifact_paths(paths).items()});self.assertTrue(cache.audit_receipt(h.receipt(),hashes,paths)['verified'])

    def test_old_identity_remains_auditable_but_cannot_satisfy_the_new_key(self):
        h=self.helper();paths,hashes=h.build();receipt=h.receipt();legacy=copy.deepcopy(receipt)
        legacy['identity']['consumers'].pop('app/portable_slang_generation.py');legacy['identity']['consumers']['app/portable_backend.py']=cache.file_digest(h.root/'app/portable_backend.py');legacy['key']=cache.key(legacy['identity'])
        self.assertTrue(cache.audit_receipt(legacy,hashes,paths)['verified'])
        current=next(h.cached.glob('*.json'));value=json.loads(current.read_text());value.update(identity=legacy['identity'],key=legacy['key']);raw=json.dumps(value).encode();current.unlink();old=h.cached/(legacy['key']+'.json');old.write_bytes(raw)
        with self.assertRaisesRegex(RuntimeError,'Required.*miss'):h.build(True)
        self.assertEqual(old.read_bytes(),raw);self.assertEqual(h.calls,['cuda','metal'])

    def test_new_generator_entry_points_are_blocked_in_cpu_and_audit_stages(self):
        s=importlib.util.spec_from_file_location('generation_separation_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
        previous=(generator.build,generator._build_resident)
        with cli.forbid_gpu():
            with self.assertRaisesRegex(RuntimeError,'forbidden'):generator.build(None,None,None)
            with self.assertRaisesRegex(RuntimeError,'forbidden'):generator._build_resident(None,None,None,None,None,None)
        self.assertEqual((generator.build,generator._build_resident),previous)

if __name__=='__main__':unittest.main()
