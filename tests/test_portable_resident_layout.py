"""Resident ABI errors stop before GPU allocation; no numerical oracle changes."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_resident_layout import reflection_plan,cuda_layout_assertions,verify_cuda_layout_assertions


def document(target):
    state=dict(kind='struct',name='Runtime',sizes=[dict(kind='uniform',value=16,alignment=8)],fields=[dict(name='small',type=dict(kind='scalar',scalarType='uint32'),binding=dict(kind='uniform',offset=0,size=4)),dict(name='large',type=dict(kind='scalar',scalarType='uint64'),binding=dict(kind='uniform',offset=8,size=8))])
    parameters=[]
    for i,name in enumerate(('commands','results','runtimeStates')):
        parameters.append(dict(name=name,binding=dict(kind='constantBuffer',index=i) if target=='metal' else dict(kind='uniform',offset=i*16,size=16,elementStride=0),type=dict(kind='resource',baseShape='structuredBuffer',access='readWrite',resultType=state if i==2 else dict(kind='scalar',scalarType='uint32'))))
    return dict(entryPoints=[dict(name='portableEvents')],parameters=parameters)


class ResidentLayoutTests(unittest.TestCase):
    def plan(self,documents):
        with tempfile.TemporaryDirectory() as folder:
            paths={k:Path(folder)/k for k in documents}
            for k,path in paths.items():Path(str(path)+'.reflection.json').write_text(json.dumps(documents[k]))
            return reflection_plan(paths,'portableEvents')

    def test_two_target_layout_and_compiler_assertion_gate_allocation(self):
        plan=self.plan({t:document(t) for t in ('cuda','metal')})
        self.assertEqual(plan['stride'],16);self.assertEqual(plan['cuda_constant_bytes'],48)
        source=b'struct Runtime_0\n{ unsigned small; unsigned long long large; };\n'
        guarded=cuda_layout_assertions(source,plan)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'probe.cu';path.write_bytes(guarded)
            verify_cuda_layout_assertions(path,plan)
            with self.assertRaisesRegex(ValueError,'allocation disagrees'):verify_cuda_layout_assertions(path,dict(plan,stride=8))
            path.write_bytes(source)
            with self.assertRaises(ValueError):verify_cuda_layout_assertions(path,plan)
        self.assertIn(b'static_assert(sizeof(Runtime_0) == 16',guarded)

    def test_changed_binding_size_field_or_target_layout_is_rejected(self):
        for kind in ('binding','stride','overlap','scalar','array','target-difference','entry','extra-resource'):
            documents={t:document(t) for t in ('cuda','metal')};r=documents['metal'];state=r['parameters'][2]['type']['resultType']
            if kind=='binding':r['parameters'][2]['binding']['index']=1
            elif kind=='stride':state['sizes'][0]['value']=0
            elif kind=='overlap':state['fields'][1]['binding']['offset']=0
            elif kind=='scalar':state['fields'][1]['type']['scalarType']='float64'
            elif kind=='array':state['fields'][1]['type']=dict(kind='array',elementCount=0,elementType=dict(kind='scalar',scalarType='uint64'))
            elif kind=='target-difference':state['fields'][1]['name']='different'
            elif kind=='entry':r['entryPoints'][0]['name']='other'
            else:r['parameters'].append(copy.deepcopy(r['parameters'][2]))
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.plan(documents)

    def test_unrecognized_cuda_struct_cannot_get_an_assumed_size(self):
        for raw in (b'',b'struct Runtime_0\n{};\nstruct Runtime_1\n{};'):
            with self.assertRaisesRegex(ValueError,'Unknown generated'):cuda_layout_assertions(raw,dict(stride=16,alignment=8))

    def nested(self,target):
        d=document(target);s=d['parameters'][2]['type']['resultType']
        child=dict(kind='struct',name='Nested',sizes=[dict(kind='uniform',value=8,alignment=4)],fields=[dict(name='slots',type=dict(kind='array',elementCount=2,elementType=dict(kind='scalar',scalarType='uint32')),binding=dict(kind='uniform',offset=0,size=8))])
        s['fields'][0]=dict(name='locks',type=child,binding=dict(kind='uniform',offset=0,size=8));return d

    def test_nested_numeric_state_has_exact_absolute_leaf_offsets(self):
        plan=self.plan({t:self.nested(t) for t in ('cuda','metal')})
        self.assertEqual(plan['fields'],[dict(name='locks.slots',scalar='uint32',count=2,offset=0,size=8),dict(name='large',scalar='uint64',count=1,offset=8,size=8)])

    def test_nested_malformed_or_backend_different_state_is_rejected(self):
        for fault in ('size','alignment','overlap','duplicate','float','array-struct','trailing','backend-name'):
            docs={t:self.nested(t) for t in ('cuda','metal')};s=docs['metal']['parameters'][2]['type']['resultType'];f=s['fields'][0];child=f['type']
            if fault=='size':child['sizes'][0]['value']=4
            elif fault=='alignment':f['binding']['offset']=1
            elif fault=='overlap':s['fields'][1]['binding']['offset']=4
            elif fault=='duplicate':child['fields'].append(copy.deepcopy(child['fields'][0]))
            elif fault=='float':child['fields'][0]['type']['elementType']['scalarType']='float64'
            elif fault=='array-struct':f['type']=dict(kind='array',elementCount=1,elementType=child)
            elif fault=='trailing':child['fields'][0]['type']['elementCount']=1;child['fields'][0]['binding']['size']=4
            else:child['fields'][0]['name']='changed'
            with self.subTest(fault=fault),self.assertRaises(ValueError):self.plan(docs)


if __name__=='__main__':unittest.main()
