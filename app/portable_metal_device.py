"""Bounded Metal visibility check; never compiles a kernel or dispatches work."""
import hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path

TIMEOUT_SECONDS=20

def probe(root):
    started=time.perf_counter();script=Path(root)/'scripts/metal-device-probe.swift'
    result=dict(schema='metal-device-preflight-v1',passed=False,device_visible=False,
        gpu_calls=0,kernel_calls=0,calculation_verified=False,context_current_verified=False,
        scope='Device visibility in this probe only; the bounded GPU child must acquire its own device')
    try:
        if sys.platform!='darwin':raise ValueError('Metal visibility requires macOS')
        swift=shutil.which('swift')
        if not swift:raise ValueError('Swift toolchain missing')
        if not script.is_file() or script.is_symlink():raise ValueError('Regular Metal visibility probe required')
        before=hashlib.sha256(script.read_bytes()).hexdigest();argv=[swift]
        cache=os.environ.get('NIKKE_METAL_MODULE_CACHE')
        if cache:
            path=Path(cache)
            if not path.is_absolute():raise ValueError('Absolute Swift module cache required')
            path.mkdir(exist_ok=True,parents=True);argv.extend(['-module-cache-path',str(path)])
        argv.append(str(script.resolve()));result.update(argv=argv,probe_sha256=before,timeout_seconds=TIMEOUT_SECONDS)
        child=subprocess.run(argv,capture_output=True,text=True,timeout=TIMEOUT_SECONDS,check=False)
        result.update(return_code=child.returncode,stdout=child.stdout,stderr=child.stderr)
        if hashlib.sha256(script.read_bytes()).hexdigest()!=before:raise ValueError('Metal visibility source changed during probe')
        value=json.loads(child.stdout)
        if not isinstance(value,dict) or value.get('schema')!='metal-device-visibility-v1' or type(value.get('device_visible')) is not bool or type(value.get('kernel_calls')) is not int or value['kernel_calls']!=0:
            raise ValueError('Invalid Metal visibility response')
        if value['device_visible']:
            if child.returncode!=0 or not isinstance(value.get('device'),str) or not value['device'] or not isinstance(value.get('registry_id'),str) or not value['registry_id'].isdecimal() or type(value.get('max_buffer_length')) is not int or value['max_buffer_length']<=0:
                raise ValueError('Invalid visible Metal device identity')
            result.update(passed=True,device_visible=True,device=value['device'],registry_id=value['registry_id'],max_buffer_length=value['max_buffer_length'])
        elif child.returncode!=2:raise ValueError('Invalid unavailable Metal device return code')
    except (OSError,ValueError,TypeError,subprocess.TimeoutExpired) as error:
        result['error']=type(error).__name__+': '+str(error)
    result['elapsed_seconds']=time.perf_counter()-started
    return result
