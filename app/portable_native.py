"""Native shared-kernel compilation and file transport; no reference execution."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile

from portable_file_identity import file_value, file_digest
from contextvars import ContextVar
HOST_THREADS=ContextVar('native_host_threads',default=None)

FLAGS=('-O2','-std=c++17','-ffp-contract=off')


def clang_compiler():
    return '/usr/bin/clang++' if platform.system()=='Darwin' else shutil.which('clang++')


def availability(root):
    from portable_slang_generation import slang_compiler
    reason=''
    if platform.system() not in ('Darwin','Linux'):reason='CPU高速計算はmacOSまたはLinuxで利用できます。'
    elif not clang_compiler() or not os.access(clang_compiler(),os.X_OK):reason='CPU高速計算にはclang++が必要です。'
    elif not os.access(slang_compiler(root),os.X_OK):reason='CPU高速計算にはslangcが必要です。'
    return dict(available=not reason,device='cpu:'+cpu_brand(),reason=reason)


def cpu_brand():
    if platform.system()=='Darwin':
        try:return subprocess.check_output(['/usr/sbin/sysctl','-n','machdep.cpu.brand_string'],text=True,stderr=subprocess.DEVNULL,timeout=5).strip()
        except (OSError,subprocess.SubprocessError):pass
    try:
        for line in Path('/proc/cpuinfo').read_text().splitlines():
            if line.startswith('model name'):return line.split(':',1)[1].strip()
    except OSError:pass
    return platform.processor() or platform.machine()


def build_host(root,cpp):
    compiler=clang_compiler()
    if not compiler:raise RuntimeError('clang++ is unavailable')
    version=file_value(compiler, 'clang-version', lambda p: subprocess.check_output([str(p),'--version'],timeout=10))
    source=root/'scripts/native-product-host.cpp'
    identity_data=dict(cpp_sha256=file_digest(cpp),host_sha256=file_digest(source),
        compiler_version=version.decode('utf-8','replace'),flags=list(FLAGS))
    identity=hashlib.sha256(json.dumps(identity_data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    directory=root/'research/portable-build/native'/identity;directory.mkdir(parents=True,exist_ok=True)
    executable=directory/'host';receipt=directory/'build.json'
    # Serialize publishers; immutable snapshots keep concurrent generation from
    # changing the bytes consumed by clang after the identity was calculated.
    import fcntl
    with (directory/'build.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if executable.is_file() and receipt.is_file():
            saved=json.loads(receipt.read_text())
            if saved['identity']==identity and saved['host_binary_sha256']==file_digest(executable):return executable,dict(saved,cache_hit=True)
        with tempfile.TemporaryDirectory(prefix='build-',dir=directory) as tmp:
            tmp=Path(tmp);kernel=tmp/'kernel.cpp';host=tmp/'host.cpp';binary=tmp/'host'
            kernel.write_bytes(cpp.read_bytes());host.write_bytes(source.read_bytes())
            if file_digest(kernel)!=identity_data['cpp_sha256'] or file_digest(host)!=identity_data['host_sha256']:
                raise RuntimeError('Native sources changed during build')
            command=[compiler,*FLAGS,'-DKERNEL_FILE="'+str(kernel)+'"',str(host),'-o',str(binary)]
            process=subprocess.run(command,capture_output=True,text=True,timeout=300)
            if process.returncode:raise RuntimeError(process.stderr or process.stdout)
            saved=dict(identity=identity,**identity_data,host_binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
            stamp=tmp/'build.json';stamp.write_text(json.dumps(saved,indent=2)+'\n')
            binary.replace(executable);stamp.replace(receipt)
        return executable,dict(saved,cache_hit=False)


def run_host(host,input_path,output_path,input_words,output_words,count,timeout):
    threads=min(count,HOST_THREADS.get() or os.cpu_count() or 1)
    process=subprocess.run([str(host),str(input_path),str(output_path),str(input_words),str(output_words),str(threads)],
        capture_output=True,text=True,timeout=timeout)
    if process.returncode:raise RuntimeError(process.stderr or process.stdout)
    transport=json.loads(process.stdout)
    if (transport.get('cases')!=count or transport.get('threads')!=threads or transport.get('command_status')!='completed'
        or transport.get('input_bytes')!=input_path.stat().st_size or transport.get('output_bytes')!=count*output_words*4):
        raise RuntimeError('Invalid native host transport')
    transport.update(command_timeout_seconds=timeout,file_readback_mode='whole batch in memory; single file write, no chunk streaming')
    return transport
