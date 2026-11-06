"""Content-addressed browser kernel builds; never executes a reference battle."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

FLAGS=('-O2','-std=c++17','-ffp-contract=off','--no-entry','-sSTANDALONE_WASM','-sALLOW_MEMORY_GROWTH','-sINITIAL_MEMORY=33554432')


def toolchain(root):
    default=root.parent/'.tools/emsdk'
    if not default.exists():default=root.parents[1]/'.tools/emsdk'
    sdk=Path(os.environ.get('NIKKE_EMSDK',default))
    env=os.environ.copy()
    if not env.get('EMSDK_PYTHON'):
        candidates=(root/'.venv/bin/python',root.parents[1]/'.venv/bin/python')
        env['EMSDK_PYTHON']=str(next((p for p in candidates if p.is_file()),Path(sys.executable)))
    return sdk/'upstream/emscripten/em++',env


def availability(root):
    from portable_slang_generation import slang_compiler
    compiler,env=toolchain(root)
    reason=''
    if not os.access(compiler,os.X_OK):reason='ブラウザ計算にはemsdkが必要です（NIKKE_EMSDK）。'
    elif not os.access(slang_compiler(root),os.X_OK):reason='ブラウザ計算にはslangcが必要です。'
    else:
        try:subprocess.check_output([str(compiler),'--version'],env=env,stderr=subprocess.STDOUT,timeout=10)
        except (OSError,subprocess.SubprocessError):reason='ブラウザ計算のem++を起動できません。EMSDK_PYTHONにはPython 3.10以上を指定してください。'
    return dict(available=not reason,reason=reason)


def build_wasm(root,cpp):
    compiler,env=toolchain(root)
    version=subprocess.check_output([str(compiler),'--version'],env=env,timeout=10)
    snapshots={'kernel.cpp':cpp.read_bytes(),'host.cpp':(root/'scripts/wasm-product-host.cpp').read_bytes(),
        'wasm-platform.h':(root/'scripts/wasm-platform.h').read_bytes()}
    data=dict(sources={k:hashlib.sha256(v).hexdigest() for k,v in snapshots.items()},compiler_version=version.decode('utf-8','replace'),
        flags=[*FLAGS,'-include','wasm-platform.h','-DKERNEL_FILE="kernel.cpp"'])
    identity=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    directory=root/'research/portable-build/wasm'/identity;directory.mkdir(parents=True,exist_ok=True)
    wasm=directory/'product.wasm';receipt=directory/'build.json'
    import fcntl
    with (directory/'build.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if wasm.is_file() and receipt.is_file():
            saved=json.loads(receipt.read_text())
            if saved.get('identity')==identity and saved.get('wasm_sha256')==hashlib.sha256(wasm.read_bytes()).hexdigest():return wasm,dict(saved,cache_hit=True)
        with tempfile.TemporaryDirectory(prefix='build-',dir=directory) as tmp:
            tmp=Path(tmp)
            for name,raw in snapshots.items():(tmp/name).write_bytes(raw)
            command=[str(compiler),*FLAGS,'-include',str(tmp/'wasm-platform.h'),'-DKERNEL_FILE="'+str(tmp/'kernel.cpp')+'"',str(tmp/'host.cpp'),'-o',str(tmp/'product.wasm')]
            process=subprocess.run(command,env=env,capture_output=True,text=True,timeout=300)
            if process.returncode:raise RuntimeError(process.stderr or process.stdout)
            saved=dict(identity=identity,**data,wasm_sha256=hashlib.sha256((tmp/'product.wasm').read_bytes()).hexdigest())
            (tmp/'build.json').write_text(json.dumps(saved,indent=2)+'\n')
            (tmp/'product.wasm').replace(wasm);(tmp/'build.json').replace(receipt)
        return wasm,dict(saved,cache_hit=False)


def build_product(root,source):
    from portable_slang_generation import _build_cpp,source_hashes
    # Use the same explicit hardware variant as the native host. Public build()
    # remains the integer oracle; changed C++ bytes select a separate WASM cache.
    outputs,hashes=_build_cpp(root,source,'portableEvents',native_binary64=True)
    wasm,receipt=build_wasm(root,outputs['cpp'])
    if source_hashes(root,source)!=hashes:raise RuntimeError('Shared sources changed during browser build')
    return wasm,receipt
