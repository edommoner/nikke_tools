"""CPU-only regression of the actual v1/v2 shader bodies, including wire ownership."""
import copy
import hashlib
import json
from pathlib import Path
import random
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
import metal_search as metal


def basic(duration=1):
    return dict(chars=([100,100,10,1,1,1,1,0,0,100,1,1,200,0,0,0,0,20,2,0]+[0]*24)*5,effects=[],enemy=[duration,0,0,0,0],names=list('abcde'))


def models():
    rng=random.Random(637302)
    result=[basic(0),basic(1/60),basic(180)]
    for case in range(64):
        m=basic(rng.choice((1,5,15,55)))
        m['enemy'][1:3]=[rng.uniform(0,1000),rng.uniform(0,60)]
        m['enemy'][4]=case%6
        for i in range(5):
            a=m['chars'];at=i*44
            a[at]=rng.uniform(1000,100000);a[at+1]=rng.uniform(1,300)
            a[at+2]=rng.randint(1,30);a[at+4]=rng.uniform(1,20);a[at+5]=30
            a[at+7]=.1 if case%2 else 0;a[at+10]=rng.choice((1,6));a[at+11]=rng.choice((1,2))
            a[at+13]=rng.uniform(1,100);a[at+14]=case%2;a[at+15]=case%3==0
            a[at+16]=[1,2,3,2,3][i];a[at+17]=20
            for k in range(24):a[at+20+k]=rng.uniform(0,20)
        for j in range(20):
            m['effects'].append([rng.randrange(5),rng.randint(1,31),rng.randrange(24),rng.randrange(3),rng.choice((0,1,2,3,4,5,6,7,8,9,10)),rng.randint(1,7),rng.uniform(1,30),rng.choice((-1,.5,2)),rng.randint(1,3),rng.randrange(3),rng.randrange(16),rng.randint(1,4)])
        result.append(m)
    # Exercise both effect-array ends, expiry, max stacks and scratch pages.
    for timing in range(11):
        m=basic(1);m['effects']=[[j%5,31,j%24,j%2,timing,1,1.25,.05,3,j%3,j%16,2] for j in range(160)]
        result.append(m)
    # Reload/attack/last-bullet effects alter reload and charge speed after the
    # normal-shot buff snapshot was taken. Shared buff scratch would fail here.
    m=basic(20)
    for i in range(5):m['chars'][i*44+2]=1;m['chars'][i*44+7]=.1
    m['effects']=[[i,31,stat,0,timing,1,75,.5,2,0,0,1] for i in range(5) for timing in (5,7,8,9,10) for stat in (19,20)]
    result.append(m)
    return result


def cpp_shader(text,namespace):
    text=re.sub(r'\[shader\("compute"\)\]|\[numthreads\(1,1,1\)\]|\[mutating\]|\[loop\]','',text)
    text=text.replace('[noinline]','__attribute__((noinline))').replace('out float b[24]','float b[24]')
    text=text.replace('uint3 id:SV_DispatchThreadID','uint3 id')
    text=text.replace('StructuredBuffer<uint> commands;','std::vector<uint> commands;')
    text=text.replace('RWStructuredBuffer<uint> results;','std::vector<uint> results;')
    text=text.replace('RWStructuredBuffer<float> results;','std::vector<float> results;')
    return 'namespace '+namespace+' {\n'+text+'\n}\n'


class CombatStructureTests(unittest.TestCase):
    def test_v2_float32_output_bits_equal_frozen_v1_and_slices_are_disjoint(self):
        compiler=shutil.which('clang++');self.assertIsNotNone(compiler)
        old=(ROOT/'tests/fixtures/optimizer-combat-f32-v1.slang').read_text()
        new=(ROOT/'gpu/optimizer_combat.slang').read_text()
        # Frozen v1 is the source Claude's compiler rejected, not a new oracle.
        self.assertEqual(hashlib.sha256(old.encode()).hexdigest(),'f81a7e21c6b87461a986dfef4c4f2b5d70af81474b28a301fafb73f955b3fcbd')
        prelude='''#include <cmath>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <vector>
using uint=uint32_t;using std::pow;using std::floor;using std::fmod;
struct uint3{uint x;};float asfloat(uint x){float v;std::memcpy(&v,&x,4);return v;}
uint asuint(float x){uint v;std::memcpy(&v,&x,4);return v;}
'''
        main='''int main(){uint words;if(!std::cin.read(reinterpret_cast<char*>(&words),4))return 1;
v1::commands.resize(words);std::cin.read(reinterpret_cast<char*>(v1::commands.data()),words*4);
v2::commands=v1::commands;uint n=v1::commands[0];v1::results.assign(n*7,0);
v2::results.assign(n*COMBAT_OUTPUT_WORDS,asfloat(0x7fc12345));
for(uint x=n;x>0;x--){uint i=x-1;auto before=v2::results;v1::optimizerCombat(uint3{i});v2::optimizerCombat(uint3{i});
uint begin=i*COMBAT_OUTPUT_WORDS,end=(i+1)*COMBAT_OUTPUT_WORDS;
if(std::memcmp(before.data(),v2::results.data(),begin*4)!=0)return 2;
if(std::memcmp(before.data()+end,v2::results.data()+end,(before.size()-end)*4)!=0)return 3;
}
std::cout.write(reinterpret_cast<char*>(v1::results.data()),n*28);
for(uint i=0;i<n;i++)std::cout.write(reinterpret_cast<char*>(v2::results.data()+i*COMBAT_OUTPUT_WORDS),28);
}'''
        corpus=models();packed=metal.combat_wire(corpus)
        with tempfile.TemporaryDirectory() as tmp:
            cpp,exe=Path(tmp)/'combat.cpp',Path(tmp)/'combat'
            cpp.write_text(prelude+cpp_shader(old,'v1')+cpp_shader(new,'v2')+main)
            build=subprocess.run([compiler,'-std=c++17','-O0','-ffp-contract=off',str(cpp),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(build.returncode,0,build.stderr)
            run=subprocess.run([str(exe)],input=struct.pack('<I',len(packed)//4)+packed,capture_output=True,timeout=60)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(len(run.stdout),len(corpus)*56)
        for i in range(len(corpus)):
            with self.subTest(model=i):
                self.assertEqual(run.stdout[i*28:(i+1)*28],run.stdout[(len(corpus)+i)*28:(len(corpus)+i+1)*28])

    def test_host_decodes_public_prefix_at_each_scratch_stride(self):
        stride=metal.COMBAT_OUTPUT_WORDS*4
        raw=bytearray(stride*2)
        struct.pack_into('<7f',raw,0,*[108]*5,5,0)
        struct.pack_into('<7f',raw,stride,*[216]*5,10,1)
        with patch.object(metal,'execute',return_value=(raw,dict(transport=dict(device='mock')))):
            result=metal.MetalCombat().run([basic(),basic()])
        self.assertEqual([r['damage'] for r in result['scores']],[540,1080])
        with patch.object(metal,'execute',return_value=(bytes(56),dict(transport=dict(device='mock')))):
            with self.assertRaisesRegex(RuntimeError,'readback length'):metal.MetalCombat().run([basic(),basic()])

    def test_source_has_only_small_context_and_bounded_noninline_loops(self):
        source=(ROOT/'gpu/optimizer_combat.slang').read_text()
        context=source.split('struct CombatModel {',1)[1].split('float C(',1)[0]
        self.assertNotIn('[',context)
        for helper in ('buffs','event','run'):
            self.assertIn('[noinline] void '+helper,source)
        self.assertIn('[noinline] float hit',source)
        self.assertNotRegex(source,r'float\s+\w+\[')
        self.assertEqual(len(re.findall(r'\bfor\(',source)),len(re.findall(r'\[loop\] for\(',source)))
        self.assertIn('#define COMBAT_OUTPUT_WORDS '+str(metal.COMBAT_OUTPUT_WORDS),source)


class CombatCompileSmokeTests(unittest.TestCase):
    def test_smoke_uses_only_one_combat_dispatch_and_retains_failure(self):
        import contextlib
        import importlib.util
        import io
        import portable_backend
        unit=ROOT.parent/'proofs/claude-product-standard-phase0-v1-20261102/optimizer-metal-v1'
        spec=importlib.util.spec_from_file_location('compile_metal_combat_smoke',unit/'compile-metal-combat.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        raw=struct.pack('<7f',*[108]*5,5,0)+bytes((metal.COMBAT_OUTPUT_WORDS-7)*4)
        for failure in (False,True):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as tmp:
                with patch.object(module,'UNIT',Path(tmp)),patch.object(portable_backend,'execute',return_value=(raw,dict(gpu_execution_verified=True)),side_effect=RuntimeError('AGX pipeline failure') if failure else None) as execute,contextlib.redirect_stdout(io.StringIO()):
                    code=module.main()
                self.assertEqual(code,1 if failure else 0)
                execute.assert_called_once()
                args=execute.call_args.args
                self.assertEqual((args[0],args[1],args[3],args[4],args[5]),('gpu/optimizer_combat.slang','optimizerCombat',2146,565,'metal'))
                self.assertEqual(struct.unpack_from('<I',args[2])[0],1)
                result=json.loads((Path(tmp)/'metal-combat-compile-v2.json').read_text())
                self.assertEqual(result['passed'],not failure)
                if failure:self.assertEqual(result['error'],'AGX pipeline failure')

if __name__=='__main__':unittest.main()
