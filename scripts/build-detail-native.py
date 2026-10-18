"""Build an optional native CUDA module. PTX remains the portable fallback.
Uses the installed CUDA NVRTC CUBIN API; never invokes a compiler at runtime.
"""
import ctypes as C,os,json,hashlib,argparse,sys
from pathlib import Path
from detail_build_contract import checked_detail_abi
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from impact_specs import gpu_source_matches as impact_matches
from lifecycle_specs import gpu_source_matches as lifecycle_matches
from world_condition_specs import gpu_source_matches as world_conditions_match
from enemy_recipient_specs import gpu_source_matches as enemy_fields_match
if not impact_matches() or not lifecycle_matches() or not world_conditions_match() or not enemy_fields_match():raise ValueError('Regenerate shared CUDA definitions before building')
ap=argparse.ArgumentParser();ap.add_argument('--sm',type=int,default=86);args=ap.parse_args()
if not 50<=args.sm<=99:raise ValueError('Unsupported architecture range')
source=ROOT/'app/detail_effects.cu';binary=ROOT/f'app/detail_effects-sm{args.sm}.cubin';manifest=binary.with_suffix('.json')
source_bytes=source.read_bytes()
abi=checked_detail_abi(source_bytes,(ROOT/'app/detail_gpu.py').read_bytes())
binpath=Path(os.environ.get('CUDA_PATH',r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.3'))/'bin'
with os.add_dll_directory(str(binpath)):
 lib=C.WinDLL(str(next(binpath.glob('nvrtc64_*.dll'))));prog=C.c_void_p()
 lib.nvrtcCreateProgram.argtypes=[C.POINTER(C.c_void_p),C.c_char_p,C.c_char_p,C.c_int,C.c_void_p,C.c_void_p]
 lib.nvrtcCompileProgram.argtypes=[C.c_void_p,C.c_int,C.POINTER(C.c_char_p)]
 for name in ('nvrtcGetProgramLogSize','nvrtcGetCUBINSize'):getattr(lib,name).argtypes=[C.c_void_p,C.POINTER(C.c_size_t)]
 for name in ('nvrtcGetProgramLog','nvrtcGetCUBIN'):getattr(lib,name).argtypes=[C.c_void_p,C.c_void_p]
 lib.nvrtcDestroyProgram.argtypes=[C.POINTER(C.c_void_p)]
 options=[f'--gpu-architecture=sm_{args.sm}','--std=c++11','--fmad=false']
 def check(code):
  if code:raise RuntimeError(f'NVRTC error {code}')
 try:
  check(lib.nvrtcCreateProgram(C.byref(prog),source_bytes,b'detail_effects.cu',0,None,None))
  array=(C.c_char_p*len(options))(*(o.encode() for o in options));code=lib.nvrtcCompileProgram(prog,len(options),array)
  size=C.c_size_t();check(lib.nvrtcGetProgramLogSize(prog,C.byref(size)));log=C.create_string_buffer(size.value);check(lib.nvrtcGetProgramLog(prog,log))
  if code:raise RuntimeError(log.value.decode('utf-8','replace'))
  check(lib.nvrtcGetCUBINSize(prog,C.byref(size)));buf=C.create_string_buffer(size.value);check(lib.nvrtcGetCUBIN(prog,buf))
  assert source.read_bytes()==source_bytes,'CUDA source changed during compilation; result discarded.'
  binary.write_bytes(buf.raw)
  manifest.write_text(json.dumps({'abi':abi,'sm':args.sm,'source_sha256':hashlib.sha256(source_bytes).hexdigest(),'binary_sha256':hashlib.sha256(buf.raw).hexdigest(),'options':options},indent=2)+'\n',encoding='utf-8')
  print(f'{binary.name}: {len(buf.raw)} bytes',flush=True)
 finally:
  if prog:lib.nvrtcDestroyProgram(C.byref(prog))
