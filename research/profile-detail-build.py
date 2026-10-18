"""Measure only this task's compiler child, without another build/JIT job."""
import argparse,ctypes as C,hashlib,json,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class MemoryCounters(C.Structure):
 _fields_=[('cb',C.c_uint32),('PageFaultCount',C.c_uint32)]+[(name,C.c_size_t) for name in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage')]
ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=('native','ptx'),required=True);args=ap.parse_args()
driver='scripts/build-detail-native.py' if args.stage=='native' else 'scripts/build-combat.py'
command=[sys.executable,str(ROOT/driver)]+(['--sm','86'] if args.stage=='native' else ['--source','detail_effects'])
source=(ROOT/'app/detail_effects.cu').read_bytes();started=time.perf_counter();child=subprocess.Popen(command,cwd=ROOT)
api=C.WinDLL('psapi',use_last_error=True).GetProcessMemoryInfo
api.argtypes=[C.c_void_p,C.POINTER(MemoryCounters),C.c_uint32];api.restype=C.c_int
peak_commit=peak_working=sampled_commit=samples=0;sample_errors=[]
print(json.dumps(dict(stage=args.stage,child_pid=child.pid)),flush=True)
try:
 while child.poll() is None:
  counters=MemoryCounters();counters.cb=C.sizeof(counters)
  if api(C.c_void_p(int(child._handle)),C.byref(counters),C.sizeof(counters)):
   samples+=1;peak_commit=max(peak_commit,counters.PeakPagefileUsage);peak_working=max(peak_working,counters.PeakWorkingSetSize);sampled_commit=max(sampled_commit,counters.PrivateUsage)
  elif not sample_errors:sample_errors.append(C.get_last_error())
  time.sleep(.25)
 code=child.wait()
except BaseException:
 if child.poll() is None:child.terminate();child.wait()
 raise
report=dict(passed=code==0 and source==(ROOT/'app/detail_effects.cu').read_bytes(),exit_code=code,seconds=time.perf_counter()-started,stage=args.stage,generated_at=datetime.now(timezone.utc).isoformat(),child_pid=child.pid,peak_commit_bytes=peak_commit,peak_working_set_bytes=peak_working,max_sampled_private_bytes=sampled_commit,samples=samples,sample_errors=sample_errors,source_sha256=hashlib.sha256(source).hexdigest(),driver_sha256=hashlib.sha256((ROOT/driver).read_bytes()).hexdigest(),scope='Compiler process time and memory only; no GPU simulation speed claim',memory_references=['https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo','https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters_ex'])
(ROOT/f'research/damage-basis-outlining-{args.stage}-build.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report),flush=True);raise SystemExit(code)
