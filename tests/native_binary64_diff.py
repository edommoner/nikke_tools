"""Generate both binary64 paths with Slang and run their bitwise C++ oracle.

Run with --pairs 20000000 for acceptance; --pairs 10000 is a quick smoke.
All source arithmetic is read from gpu/binary64.slang without modification.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


def build_and_run(root, scratch, pairs):
    sys.path.insert(0, str(root/'app'))
    from portable_slang_generation import slang_compiler, CPP_FLAGS
    from portable_native import clang_compiler, FLAGS
    scratch.mkdir(parents=True, exist_ok=True)
    source = (root/'gpu/binary64.slang').read_text()
    names = re.findall(r'^(?:uint64_t|bool|void|double) (\w+)\(', source, re.M)
    names += re.findall(r'^static const uint64_t (\w+)', source, re.M)
    parts = []
    for prefix, enabled in [('soft', False), ('hard', True)]:
        parts.append('#define PORTABLE_NATIVE_BINARY64 1\n' if enabled else '#undef PORTABLE_NATIVE_BINARY64\n')
        parts.extend(f'#define {name} {prefix}_{name}\n' for name in names)
        parts.append(source)
        parts.extend(f'\n#undef {name}\n' for name in names)
    parts.append('RWStructuredBuffer<uint64_t> data;\n[shader("compute")][numthreads(1,1,1)]\nvoid probe(uint3 id:SV_DispatchThreadID) { uint64_t a=data[0], b=data[1];\n')
    for prefix in ('soft', 'hard'):
        for i, name in enumerate(('f64Add', 'f64Mul', 'f64Div', 'f64Equal', 'f64Less', 'f64FromI64')):
            args = 'a' if name == 'f64FromI64' else 'a,b'
            parts.append(f'data[{2+i+(6 if prefix=="hard" else 0)}]=uint64_t({prefix}_{name}({args}));\n')
    parts.append('}\n')
    slang = scratch/'oracle.slang'; slang.write_text(''.join(parts))
    result = subprocess.run([str(slang_compiler(root)), str(slang), '-entry', 'probe', *CPP_FLAGS], capture_output=True, check=True)
    generated = result.stdout.decode()
    # Resolve generated static function names rather than assuming Slang suffixes.
    harness = (root/'tests/native_binary64_diff.cpp').read_text()
    for prefix in ('soft', 'hard'):
        for name in ('f64Add', 'f64Mul', 'f64Div', 'f64Equal', 'f64Less', 'f64FromI64'):
            match = re.search(r'\b('+prefix+'_'+name+r'_\d+)\(', generated)
            if not match: raise RuntimeError('Missing generated operation: '+name)
            harness = f'#define {prefix}_{name} {match[1]}\n' + harness
    cpp=scratch/'oracle.cpp'; cpp.write_text(generated+'\n'+harness)
    binary=scratch/'oracle'
    subprocess.run([clang_compiler(), *FLAGS, str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary), str(pairs)], check=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--pairs', type=int, default=20000000)
    args=parser.parse_args()
    build_and_run(Path(__file__).resolve().parents[1], args.scratch, args.pairs)
