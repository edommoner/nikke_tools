import json
import math
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'app'))
import metal_search as metal
from combat_reference import combat_reference, hit
from gpu_selector import select_teams, cpu_expand
from optimizer_search_cases import selection_cases, emulate_selection_wire


def basic(duration=1):
    return dict(chars=([100,100,10,1,1,1,1,0,0,100,1,1,200,0,0,0,0,20,2,0]+[0]*24)*5, effects=[], enemy=[duration,0,0,0,0], names=list('abcde'))


class MetalSelectionTests(unittest.TestCase):
    def test_shared_corpus_matches_canonical_cpu_exactly(self):
        # Bitonic simulation is expensive: test it once per wire shape, then
        # separately compare full beams with an independent sorted wire executor.
        cases = list(selection_cases())
        self.assertTrue(any(len({n for c in b['candidates'] for n in c['squad']}) == 256 for b in cases))
        def dispatch(source, entry, packed, iw, ow, backend):
            self.assertEqual((source, entry, iw, ow, backend), ('gpu/optimizer_select.slang', 'optimizerSelect', 1612, 480, 'metal'))
            return sorted_wire(packed), {'transport': {'device': 'mock Metal'}}
        with patch.object(metal, 'execute', side_effect=dispatch):
            for index, body in enumerate(cases):
                with self.subTest(case=index):
                    cpu = select_teams(body)
                    gpu = metal.select_teams({**body, 'backend': 'metal'})
                    for field in ('recommendation', 'expanded', 'width'):
                        self.assertEqual(gpu[field], cpu[field])
                    self.assertEqual(gpu['backend'], 'metal')

    def test_bitonic_wire_matches_independent_expansion_at_mask_boundaries(self):
        rng = random.Random(713)
        masks = []
        for i in range(160):
            mask = [0]*8
            for j in rng.sample(range(256), 5): mask[j//32] |= 1 << (j % 32)
            masks.append(mask)
        masks[-1] = [0]*7+[1 << 31]
        states = [([0]*8, 0, [], 0xffffffff), ([0xffffffff]*8, 0, [], 0xffffffff), ([0]*7+[1 << 31], 2**50, [], 31)]
        for scores in ([0]*160, [2**53//5-i % 3 for i in range(160)]):
            raw = emulate_selection_wire(metal.selection_wire(states, masks, scores))
            values = cpu_expand(states, masks, scores)
            for top in (1, 73, 256, 4096):
                expected = sorted(((i,v) for i,v in enumerate(values) if v), key=lambda x: (-x[1], x[0]))[:top]
                self.assertEqual(metal.merge_selection(raw, 3, 160, top), expected)

    def test_actual_selection_shader_body_as_cpu_cpp(self):
        compiler = shutil.which('clang++')
        self.assertIsNotNone(compiler)
        source = (ROOT/'gpu/optimizer_select.slang').read_text()
        source = source[source.index('void optimizerSelect'):].replace('uint3 id: SV_DispatchThreadID', 'uint3 id')
        wrapper = '#include <cstdint>\n#include <iostream>\n#include <vector>\nusing uint=uint32_t;struct uint3{uint x;};std::vector<uint> commands,results;\n'+source+'''
int main(){uint words;while(std::cin.read(reinterpret_cast<char*>(&words),4)){
commands.resize(words);std::cin.read(reinterpret_cast<char*>(commands.data()),words*4);
results.assign(commands[0]*480,0);for(uint i=0;i<commands[0];i++)optimizerSelect(uint3{i});
std::cout.write(reinterpret_cast<char*>(results.data()),results.size()*4);}}
'''
        cases=[];rng=random.Random(871)
        for n in (1,7,127,160):
            masks=[]
            for i in range(n):
                mask=[0]*8
                for j in rng.sample(range(256),5):mask[j//32]|=1<<(j%32)
                masks.append(mask)
            for scores in ([0]*n,[2**53//5-rng.randrange(5) for _ in range(n)]):
                states=[([0]*8,0,[],0xffffffff),([0xffffffff]*8,0,[],0xffffffff),([0]*8,2**50,[],n//2)]
                packed=metal.selection_wire(states,masks,scores)
                cases.append((packed,emulate_selection_wire(packed)))
        data=b''.join(struct.pack('<I',len(packed)//4)+packed for packed,_ in cases)
        with tempfile.TemporaryDirectory() as tmp:
            cpp,exe=Path(tmp)/'selection.cpp',Path(tmp)/'selection'
            cpp.write_text(wrapper)
            subprocess.run([compiler,'-O0',str(cpp),'-o',str(exe)],check=True,capture_output=True)
            actual=subprocess.run([str(exe)],input=data,capture_output=True,check=True,timeout=30).stdout
        self.assertEqual(actual,b''.join(expected for _,expected in cases))

    def test_failure_propagates_and_validation_precedes_dispatch(self):
        with patch.object(metal, 'execute', side_effect=RuntimeError('Metal child failed')) as run:
            for body in ({'backend':'bad','candidates':[]}, {'backend':'metal','candidates':[dict(squad=['x']*5,damage=0)]}, {'backend':'metal','candidates':[],'width':4097}):
                with self.assertRaises(ValueError):metal.select_teams(body)
            run.assert_not_called()
            with self.assertRaisesRegex(RuntimeError, 'Metal child failed'):
                metal.select_teams(dict(backend='metal', candidates=[dict(squad=list('abcde'),damage=0)],teamCount=1))

    def test_malformed_readback_rejected(self):
        with self.assertRaises(RuntimeError):metal.merge_selection(b'', 1, 1, 1)
        raw = struct.pack('<III', 1, 0, 160)+bytes(479*4-8)
        with self.assertRaises(RuntimeError):metal.merge_selection(raw, 1, 1, 1)


def sorted_wire(packed):
    """Independent CPU expansion/sort, not the shader's bitonic implementation."""
    words = struct.unpack('<'+'I'*(len(packed)//4), packed)
    raw = bytearray()
    for parent in range(words[0]):
        at = 1+parent*1612
        nc, last = words[at:at+2]
        states = [(words[at+2:at+10], words[at+10] | words[at+11] << 32, [], last)]
        masks, scores = [], []
        for i in range(nc):
            c = at+12+i*10
            masks.append(words[c:c+8]); scores.append(words[c+8] | words[c+9] << 32)
        values = cpu_expand(states, masks, scores)
        rows = sorted(enumerate(values), key=lambda row: (-row[1], row[0]))
        for index,value in rows:
            raw.extend(struct.pack('<III',value & 0xffffffff,value >> 32,index))
        raw.extend(bytes((160-nc)*12))
    return bytes(raw)


class MetalProbeTests(unittest.TestCase):
    def test_visibility_toolchain_and_reason_are_exposed_without_dispatch(self):
        import portable_metal_device
        with patch.object(portable_metal_device,'probe',return_value=dict(passed=True,device='Apple Mock')),patch.object(Path,'is_file',return_value=True),patch.object(shutil,'which',return_value='/swift'),patch.object(metal,'execute') as execute:
            result=metal.probe()
            self.assertTrue(result['available']);self.assertEqual(result['device'],'Apple Mock')
            self.assertEqual(result['verification'],'per-request');execute.assert_not_called()
        with patch.object(portable_metal_device,'probe',return_value=dict(passed=False,error='No Metal device')):
            result=metal.probe()
            self.assertFalse(result['available']);self.assertEqual(result['reason'],'No Metal device')

    def test_dispatch_requires_explicit_metal_and_keeps_legacy_actions_out(self):
        with patch.object(metal,'select_teams',return_value={'backend':'metal'}) as select:
            self.assertEqual(metal.dispatch(dict(action='select',backend='metal')),{'backend':'metal'})
            select.assert_called_once()
        for body in (dict(action='select',backend='cuda'),dict(action='evaluate_portable_events',backend='metal')):
            with self.assertRaises(ValueError):metal.dispatch(body)


class CombatReferenceTests(unittest.TestCase):
    def test_known_timeline_and_periodic_order(self):
        self.assertEqual(combat_reference(basic())['damage'], 540)
        m = basic(5)
        for i in range(5):
            m['chars'][i*44+2] = 2;m['chars'][i*44+4] = m['chars'][i*44+5] = 2
        self.assertEqual(combat_reference(m)['shots'],30)
        m = basic(5)
        m['effects'] = [[0,31,0,0,4,1,100,1.5,2,0,0,1],[0,31,0,1,4,1,100,0,1,0,0,1]]
        self.assertEqual(combat_reference(m)['members'],[2470,1289,1289,1289,1289])

    def test_binary64_transcription_against_original_source_on_cpu(self):
        compiler = shutil.which('clang++')
        self.assertIsNotNone(compiler, 'CPU source-semantic oracle requires clang++')
        # Compile original kernel text as ordinary CPU C++, no CUDA compiler,
        # driver, PTX, device or kernel launch. Original .cu bytes stay untouched.
        source = (ROOT/'app/combat.cu').read_text().replace('extern "C" __global__', '').replace('__device__', '')
        wrapper = '#include <cmath>\n#include <iostream>\n#include <iomanip>\nusing std::pow;\nstruct Dim {int x=0;};Dim blockIdx,threadIdx;Dim blockDim{1};\nlong long __double2ll_rn(double x){return std::llrint(x);}\n'+source+'''
int main(){double c[220],e[1920]={},env[5],out[7];int ne;
while(std::cin>>ne){for(auto &x:c)std::cin>>x;for(int i=0;i<ne*12;i++)std::cin>>e[i];for(auto &x:env)std::cin>>x;
combat(c,e,&ne,env,out,1);for(auto x:out)std::cout<<std::setprecision(17)<<x<<" ";std::cout<<"\\n";}}
'''
        rng = random.Random(905)
        models = [basic(55),basic(5)]
        for case in range(50):
            m = basic(rng.choice((1,5,15,55)))
            m['enemy'][1:3] = [rng.uniform(0,1000),rng.uniform(0,60)]
            m['enemy'][4] = case % 6
            for i in range(5):
                a = m['chars'];at = i*44
                a[at] = rng.uniform(1000,100000);a[at+1] = rng.uniform(1,300)
                a[at+2] = rng.randint(1,30);a[at+4] = rng.uniform(1,20);a[at+5] = 30
                a[at+7] = .1 if case % 2 else 0;a[at+13] = rng.uniform(1,100)
                a[at+16] = [1,2,3,2,3][i];a[at+17] = 20
                for k in range(24):a[at+20+k] = rng.uniform(0,20)
            for j in range(20):
                timing = rng.choice((0,1,2,3,4,5,6,7,8,9,10));kind = rng.randrange(3)
                m['effects'].append([rng.randrange(5),rng.randint(1,31),rng.randrange(24),kind,timing,rng.randint(1,7),rng.uniform(1,30),rng.choice((-1,.5,2)),rng.randint(1,3),rng.randrange(3),rng.randrange(16),rng.randint(1,4)])
            models.append(m)
        with tempfile.TemporaryDirectory() as tmp:
            cpp, exe = Path(tmp)/'oracle.cpp', Path(tmp)/'oracle'
            cpp.write_text(wrapper)
            subprocess.run([compiler,'-O0','-ffp-contract=off',str(cpp),'-o',str(exe)],check=True,capture_output=True)
            data = '\n'.join(' '.join(map(str,[len(m['effects']),*m['chars'],*(v for row in m['effects'] for v in row),*m['enemy']])) for m in models)
            run = subprocess.run([str(exe)],input=data,text=True,capture_output=True,check=True,timeout=60)
        for index,(m,line) in enumerate(zip(models,run.stdout.splitlines())):
            with self.subTest(case=index):
                result = combat_reference(m)
                self.assertEqual([*result['members'],result['shots'],result['cycles']],list(map(float,line.split())))
        self.assertEqual(len(run.stdout.splitlines()),len(models))

    def test_wire_layout_and_no_silent_dispatch_fallback(self):
        packed = metal.combat_wire([basic()])
        self.assertEqual(len(packed),4+2146*4)
        self.assertEqual(struct.unpack_from('<I',packed)[0],1)
        self.assertEqual(struct.unpack_from('<f',packed,8)[0],100)
        self.assertEqual(struct.unpack_from('<5f',packed,4+2141*4),(1,0,0,0,0))
        m = basic();m['chars'][0] = math.nan
        with self.assertRaises(ValueError):metal.combat_wire([m])
        with patch.object(metal,'execute',side_effect=RuntimeError('Metal failed')):
            with self.assertRaisesRegex(RuntimeError,'Metal failed'):metal.MetalCombat().run([basic()])
        with patch.object(metal,'execute',return_value=(struct.pack('<7f',*[108]*5,5,0)+bytes((metal.COMBAT_OUTPUT_WORDS-7)*4),{'transport':{'device':'Mock Metal'}})):
            result = metal.MetalCombat().run([basic()])
        self.assertEqual(result['scores'],[combat_reference(basic())])
        self.assertEqual(result['model'],metal.COMBAT_MODEL)

if __name__ == '__main__':unittest.main()
