"""Live preflight reuse must keep every comparator and independent audit fresh."""
import copy,importlib.util,json,os,struct,sys,tempfile,threading,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_parent_oracles import ParentOracles
spec=importlib.util.spec_from_file_location('parent_oracle_cli',ROOT/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
OW=786432*4


class ParentOracleTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.capture=self.root/'capture';self.capture.mkdir()
        self.m,self.adapter=self.fixture()
        self.original_input=(self.capture/'input.bin').read_bytes();self.original_raw=(self.capture/'readback.bin').read_bytes()
        self.stack=self.enterContext(__import__('contextlib').ExitStack())
        self.stack.enter_context(patch.object(cli,'ROOT',self.root));self.stack.enter_context(patch.object(cli,'open_suite',return_value=self.adapter))
        self.stack.enter_context(patch.object(cli,'verify_package',return_value=self.m));self.stack.enter_context(patch.object(cli,'audit_generation_capture'))
        self.stack.enter_context(patch.dict(cli.SUITES,fixture=dict(parent_oracle_reuse=True,tests=[])))
        self.snapshot=ParentOracles(self.m,self.capture);self.addCleanup(self.snapshot.close)

    def fixture(self,kind='reference',nested=False):
        module=types.ModuleType('parent_fixture');module.copy=copy;module.calls=dict(native=0,compare=0,prepare=0)
        value=dict(battle=dict(damage=9),skill_trace=[]);module.value=value
        module.suite=types.SimpleNamespace(INPUT=1)
        module.cross=types.SimpleNamespace(digest=lambda v:cli.sha(json.dumps(v,sort_keys=True).encode()),normalized=cli.sha)
        code="""
def native_reference(domain):
    calls['native']+=1
    return copy.deepcopy(value)
def compare(block,domain):
    calls['compare']+=1
    result=native_reference(domain)
    assert block[1]==result['battle']['damage'],'Damage differs'
    return result
"""
        exec(code,module.__dict__);domain=(dict(amount=9),{},[])
        if kind in ('inspect','real'):
            original=module.native_reference
            def inspected(case):
                result=original(case);return result['battle'],result['skill_trace']
            module.suite.inspect_native=inspected
            if kind=='real':
                module.real=types.SimpleNamespace(native_reference=inspected)
                module.suite.inspect_native=lambda case:module.real.native_reference(case['body'])
                domain=({'body':dict(amount=9)},{},[])
                expression="real.native_reference(domain[0]['body'])"
            else:expression='suite.inspect_native(domain[0])'
            del module.__dict__['native_reference']
            exec("def compare(block,domain):\n    calls['compare']+=1\n    native,trace="+expression+"\n    assert block[1]==native['damage'],'Damage differs'\n    return dict(battle=native,skill_trace=trace)\n",module.__dict__)
        elif kind=='fallback':
            module.fresh_oracle=module.native_reference
            exec("def compare(block,domain):\n    calls['compare']+=1\n    result=fresh_oracle(domain)\n    assert block[1]==result['battle']['damage']\n    return result\n",module.__dict__)
        self.leaf=module
        if nested:
            parent=types.ModuleType('parent_fixture_route');parent.adapters={'unit':module};parent.suite=module.suite;parent.cross=module.cross
            exec("def native_reference(domain):\n    return adapters[domain[0]].native_reference(domain[1])\ndef compare(block,domain):\n    return adapters[domain[0]].compare(block,domain[1])\n",parent.__dict__)
            module=parent;domain=('unit',domain)
        entries=[('native',[10],domain),('reject/guard',[11],None)];data=struct.pack('<III',2,10,11)
        def prepare():self.leaf.calls['prepare']+=1;return entries,data
        module.prepare=prepare;parts=[struct.pack('<II',0,9)+bytes(OW-8),struct.pack('<I',64)+bytes(OW-4)]
        output=b''.join(parts);(self.capture/'input.bin').write_bytes(data);(self.capture/'readback.bin').write_bytes(output)
        for suffix in ('cu','metal'):(self.capture/('generated.'+suffix)).write_bytes(b'generated')
        rows=[dict(name=name,input_sha256=cli.sha(data[4+i*4:8+i*4]),output_sha256=cli.sha(parts[i]),native_sha256=module.cross.digest(value if i==0 else dict(status=64))) for i,(name,_,_) in enumerate(entries)]
        cli.write(self.capture/'evidence.json',dict(input_sha256=cli.sha(data),output_sha256=cli.sha(output),source_sha256={},gpu_execution_verified=True,backend='metal'))
        return dict(package_id='owned',suite='fixture',purpose='sealed',golden=dict(input_sha256=cli.sha(data),source_sha256={},entries=rows,output_sha256=cli.sha(output),generated_normalized=dict(cuda=cli.sha(b'generated'),metal=cli.sha(b'generated')))),module

    def preflight(self):return cli.cpu_preflight(self.m,parent_oracles=self.snapshot)
    def compare(self):return cli.compare_readback(self.m,self.capture,parent_oracles=self.snapshot)

    def test_reuse_calls_existing_comparator_and_default_audit_recalculates(self):
        self.preflight();self.assertEqual(self.leaf.calls['native'],1)
        original=self.adapter.native_reference
        reused=self.compare();self.assertTrue(reused['calculation_verified']);self.assertEqual(self.leaf.calls['native'],1)
        self.assertEqual(self.leaf.calls['compare'],1);self.assertIs(self.adapter.native_reference,original)
        self.assertEqual(reused.pop('parent_oracles')['reused_native_cases'],1)
        fresh=cli.compare_readback(self.m,self.capture,self.adapter)
        self.assertEqual(fresh,reused);self.assertEqual(self.leaf.calls['native'],2)
        self.assertEqual(self.leaf.calls['prepare'],2)
        self.assertTrue(all(words is None for _,words,_ in self.snapshot.entries));self.assertFalse(hasattr(self.snapshot,'data'))

    def test_nested_inspect_and_real_existing_protocols(self):
        for kind,nested in [('reference',True),('inspect',False),('real',False)]:
            with self.subTest(kind=kind):
                self.m,self.adapter=self.fixture(kind,nested);self.snapshot.close();self.snapshot=ParentOracles(self.m,self.capture)
                with patch.object(cli,'open_suite',return_value=self.adapter),patch.object(cli,'verify_package',return_value=self.m):
                    self.preflight();result=self.compare()
                self.assertTrue(result['calculation_verified']);self.assertEqual(result['parent_oracles']['reused_native_cases'],1)
                self.assertEqual(self.leaf.calls['native'],1)

    def test_unknown_protocol_remains_fresh(self):
        self.m,self.adapter=self.fixture('fallback');self.snapshot=ParentOracles(self.m,self.capture)
        with patch.object(cli,'open_suite',return_value=self.adapter):
            self.preflight();result=self.compare()
        self.assertTrue(result['calculation_verified']);self.assertEqual(result['parent_oracles']['fresh_native_cases'],1)
        self.assertEqual(self.leaf.calls['native'],2)

    def test_unfingerprintable_domain_uses_original_fresh_prepare(self):
        self.adapter.prepare()[0][0][2][1]['callback']=lambda:None
        self.preflight();self.assertFalse(self.snapshot.usable);self.assertFalse(self.snapshot.entries)
        result=self.compare();self.assertTrue(result['calculation_verified'])
        self.assertEqual(result['parent_oracles']['fallback_reason'],'unfingerprintable-domain')
        self.assertEqual(self.leaf.calls['native'],2);self.assertTrue(self.snapshot.closed)

    def test_mutated_oracle_or_domain_or_provider_cannot_pass(self):
        for fault in ('oracle','domain','provider'):
            with self.subTest(fault=fault):
                self.m,self.adapter=self.fixture();self.snapshot.close();self.snapshot=ParentOracles(self.m,self.capture)
                with patch.object(cli,'open_suite',return_value=self.adapter):self.preflight()
                if fault=='oracle':self.snapshot.records[0]['value']['battle']['damage']+=1
                elif fault=='domain':self.snapshot.entries[0][2][0]['amount']+=1
                else:self.adapter.native_reference=lambda d:dict(forged=True)
                result=self.compare();self.assertFalse(result['calculation_verified']);self.assertTrue(result['mismatches'])
                self.assertEqual((self.capture/'readback.bin').read_bytes(),self.original_raw)

    def test_comparator_metadata_mutation_is_rejected_for_reuse_and_fresh_fallback(self):
        for kind in ('reference','fallback'):
            with self.subTest(kind=kind):
                self.m,self.adapter=self.fixture(kind);self.snapshot.close();self.snapshot=ParentOracles(self.m,self.capture)
                with patch.object(cli,'open_suite',return_value=self.adapter):self.preflight()
                call='native_reference' if kind=='reference' else 'fresh_oracle'
                exec("def compare(block,domain):\n    result="+call+"(domain)\n    domain[1]['changed']=True\n    return result\n",self.adapter.__dict__)
                result=self.compare();self.assertFalse(result['calculation_verified'])
                self.assertIn('mutated its preflight input',result['mismatches'][0]['reason'])

    def test_raw_mismatch_keeps_the_comparator_and_restores_binding(self):
        self.preflight();original=self.adapter.native_reference
        # Keep file integrity valid but alter the GPU value. The original
        # comparator, not a cached success receipt, must detect the difference.
        raw=bytearray(self.original_raw);raw[4:8]=struct.pack('<I',8);(self.capture/'readback.bin').write_bytes(raw)
        evidence=cli.load(self.capture/'evidence.json');evidence['output_sha256']=cli.sha(raw);cli.write(self.capture/'evidence.json',evidence)
        result=self.compare();self.assertFalse(result['calculation_verified']);self.assertIn('Damage differs',result['mismatches'][0]['reason'])
        self.assertIs(self.adapter.native_reference,original);self.assertEqual(self.leaf.calls['compare'],1)

    def test_unexpected_oracle_request_does_not_receive_a_cached_value(self):
        self.preflight();original=self.adapter.native_reference
        exec("def compare(block,domain):\n    return native_reference(copy.deepcopy(domain))\n",self.adapter.__dict__)
        result=self.compare();self.assertFalse(result['calculation_verified']);self.assertIn('Unexpected preflight oracle request',result['mismatches'][0]['reason'])
        self.assertIs(self.adapter.native_reference,original)

    def test_package_capture_pid_thread_closed_and_repeated_use_are_rejected(self):
        self.preflight()
        for m,path in [(dict(self.m,package_id='foreign'),self.capture),(self.m,self.root/'foreign')]:
            with self.assertRaises(ValueError):self.snapshot.check(m,path)
        with patch('portable_parent_oracles.os.getpid',return_value=os.getpid()+1):
            with self.assertRaises(ValueError):self.snapshot.check(self.m,self.capture)
        errors=[]
        def other_thread():
            try:self.snapshot.check(self.m,self.capture)
            except ValueError:errors.append(True)
        thread=threading.Thread(target=other_thread);thread.start();thread.join();self.assertEqual(errors,[True])
        self.assertTrue(self.compare()['calculation_verified'])
        with self.assertRaisesRegex(ValueError,'already consumed'):self.compare()
        self.snapshot.close()
        with self.assertRaises(ValueError):self.snapshot.check(self.m,self.capture)

    def test_input_and_source_mutation_stop_before_reuse(self):
        self.preflight();(self.capture/'input.bin').write_bytes(self.original_input+b'x')
        with self.assertRaisesRegex(ValueError,'trailing'):self.compare()
        self.assertEqual(self.leaf.calls['compare'],0)
        (self.capture/'input.bin').write_bytes(self.original_input)
        self.snapshot=ParentOracles(self.m,self.capture);self.preflight()
        with patch.object(cli,'verify_package',side_effect=ValueError('Package bytes changed')):
            with self.assertRaisesRegex(ValueError,'Package bytes'):self.compare()
        self.assertEqual(self.leaf.calls['compare'],0)

    def test_independent_audit_cannot_receive_live_preflight_oracles(self):
        self.preflight();cli.write(self.capture/'run.json',dict(package_id='owned',mode='gpu'))
        with self.assertRaisesRegex(ValueError,'owning live battle audit'):cli.audit_capture(self.capture,verify_artifacts=False,parent_oracles=self.snapshot)
        self.assertEqual(self.leaf.calls['compare'],0)

    def test_input_mismatch_stops_before_native_and_native_input_mutation_is_rejected(self):
        self.m['golden']['entries'][0]['name']='wrong'
        with self.assertRaisesRegex(ValueError,'CPU/input mismatch'):self.preflight()
        self.assertEqual(self.leaf.calls['native'],0)
        self.m,self.adapter=self.fixture();self.snapshot=ParentOracles(self.m,self.capture)
        exec("def native_reference(domain):\n    calls['native']+=1\n    domain[0]['amount']+=1\n    return copy.deepcopy(value)\n",self.adapter.__dict__)
        with patch.object(cli,'open_suite',return_value=self.adapter):
            with self.assertRaisesRegex(ValueError,'mutated its comparison input'):self.preflight()
        self.assertFalse((self.capture/'gpu-claimed-metal.json').exists())

    def test_run_owner_closes_snapshot_on_failed_transport_and_keeps_claim(self):
        import portable_parent_oracles as module
        owned=self.root/'owned';created=[];original=module.ParentOracles
        def construct(*a):result=original(*a);created.append(result);return result
        fake_os=types.SimpleNamespace(**dict(vars(os),name='nt'))
        # This fixture injects a transport failure, not host disk pressure.
        # Actual storage gates have separate budget tests and remain in run.
        with patch.object(module,'ParentOracles',side_effect=construct),patch.object(cli,'os',fake_os),patch.object(cli,'cpu_test_groups'),patch.object(cli,'capture_storage_preflight',return_value=dict(passed=True)) as storage,patch.object(cli,'run_job',side_effect=RuntimeError('Transport failed')):
            with self.assertRaisesRegex(RuntimeError,'Transport failed'):cli.run_capture(owned,'cuda',30)
        self.assertEqual(storage.call_count,2)
        self.assertEqual(len(created),1);self.assertTrue(created[0].closed);self.assertFalse(created[0].records)
        self.assertTrue((self.root/'gpu-claimed-cuda.json').is_file());self.assertTrue((owned/'failure.json').is_file())
        self.assertFalse((owned/'comparison.json').exists())


if __name__=='__main__':unittest.main()
