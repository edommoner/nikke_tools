"""S13's generated soft/hardware oracle compiled with production WASM flags.

python3.12 tests/wasm_binary64_diff.py --scratch PATH --pairs 20000000
"""
import argparse
from pathlib import Path
import re
import subprocess
import sys


def build_and_run(root, scratch, pairs):
    sys.path.insert(0, str(root/'app'))
    from portable_slang_generation import slang_compiler, CPP_FLAGS
    from portable_wasm import toolchain, FLAGS
    scratch.mkdir(parents=True, exist_ok=True)
    source=(root/'gpu/binary64.slang').read_text()
    names=re.findall(r'^(?:uint64_t|bool|void|double) (\w+)\(',source,re.M)
    names+=re.findall(r'^static const uint64_t (\w+)',source,re.M)
    parts=[]
    for prefix,enabled in [('soft',False),('hard',True)]:
        parts.append('#define PORTABLE_NATIVE_BINARY64 1\n' if enabled else '#undef PORTABLE_NATIVE_BINARY64\n')
        parts.extend(f'#define {name} {prefix}_{name}\n' for name in names)
        parts.append(source)
        parts.extend(f'\n#undef {name}\n' for name in names)
    parts.append('RWStructuredBuffer<uint64_t> data;\n[shader("compute")][numthreads(1,1,1)]\nvoid probe(uint3 id:SV_DispatchThreadID) { uint64_t a=data[0],b=data[1];\n')
    for prefix in ('soft','hard'):
        for i,name in enumerate(('f64Add','f64Mul','f64Div','f64Equal','f64Less','f64FromI64')):
            args='a' if name=='f64FromI64' else 'a,b'
            parts.append(f'data[{2+i+(6 if prefix=="hard" else 0)}]=uint64_t({prefix}_{name}({args}));\n')
    parts.append('}\n')
    slang=scratch/'oracle.slang';slang.write_text(''.join(parts))
    generated=subprocess.check_output([str(slang_compiler(root)),str(slang),'-entry','probe',*CPP_FLAGS]).decode()
    harness=(root/'tests/native_binary64_diff.cpp').read_text()
    for prefix in ('soft','hard'):
        for name in ('f64Add','f64Mul','f64Div','f64Equal','f64Less','f64FromI64'):
            match=re.search(r'\b('+prefix+'_'+name+r'_\d+)\(',generated)
            if not match:raise RuntimeError('Missing generated operation: '+name)
            harness=f'#define {prefix}_{name} {match[1]}\n'+harness
    # Renaming main removes C++'s implicit return-zero rule.
    end=harness.rfind('}')
    harness=harness[:end]+'return 0;\n'+harness[end:]
    harness=harness.replace('int main(', 'extern "C" __attribute__((export_name("oracle_main"))) int oracle_main(')
    cpp=scratch/'oracle.cpp';cpp.write_text(generated+'\n'+harness)
    compiler,env=toolchain(root)
    binary=scratch/'oracle.wasm'
    # oracle_main/malloc are harness-only exports. All arithmetic/optimization flags
    # and the forced platform header are identical to build_wasm.
    subprocess.run([str(compiler),*FLAGS,'-include',str(root/'scripts/wasm-platform.h'),
                    '-Wl,--export=malloc',str(cpp),'-o',str(binary)],env=env,check=True)
    runner=scratch/'run.mjs'
    runner.write_text('''import fs from 'node:fs';
import {WASI} from 'node:wasi';
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{},returnOnExit:true});
const instance=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2])),
  {wasi_snapshot_preview1:wasi.wasiImport,env:{emscripten_notify_memory_growth(){}}});
wasi.initialize(instance);
const e=instance.exports, text=Buffer.from(process.argv[3]+'\\0'), p=e.malloc(text.length), argv=e.malloc(12);
new Uint8Array(e.memory.buffer,p,text.length).set(text);
new Uint32Array(e.memory.buffer,argv,3).set([p,p,0]);
const rc=e.oracle_main(2,argv);if(rc!==0)throw Error('oracle rc='+rc);
''')
    subprocess.run(['node',str(runner),str(binary),str(pairs)],check=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch',type=Path,required=True)
    p.add_argument('--pairs',type=int,default=20000000)
    a=p.parse_args();build_and_run(Path(__file__).resolve().parents[1],a.scratch,a.pairs)
