"""Compile the isolated PRNG prototype without changing combat artifacts."""
import ctypes as C,hashlib,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];source=ROOT/'research/ports/detail_random.cu';output=source.with_suffix('.ptx')
binpath=Path(os.environ.get('CUDA_PATH',r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.3'))/'bin'
with os.add_dll_directory(str(binpath)):
 lib=C.WinDLL(str(next(binpath.glob('nvrtc64_*.dll'))));prog=C.c_void_p()
 lib.nvrtcCreateProgram.argtypes=[C.POINTER(C.c_void_p),C.c_char_p,C.c_char_p,C.c_int,C.c_void_p,C.c_void_p]
 lib.nvrtcCompileProgram.argtypes=[C.c_void_p,C.c_int,C.POINTER(C.c_char_p)]
 for name in ('nvrtcGetProgramLogSize','nvrtcGetPTXSize'):getattr(lib,name).argtypes=[C.c_void_p,C.POINTER(C.c_size_t)]
 for name in ('nvrtcGetProgramLog','nvrtcGetPTX'):getattr(lib,name).argtypes=[C.c_void_p,C.c_void_p]
 lib.nvrtcDestroyProgram.argtypes=[C.POINTER(C.c_void_p)]
 def check(code):
  if code:raise RuntimeError(f'NVRTC {code}')
 try:
  check(lib.nvrtcCreateProgram(C.byref(prog),source.read_bytes(),b'detail_random.cu',0,None,None))
  options=[b'--gpu-architecture=compute_52',b'--std=c++11',b'--fmad=false'];args=(C.c_char_p*len(options))(*options)
  code=lib.nvrtcCompileProgram(prog,len(options),args)
  size=C.c_size_t();check(lib.nvrtcGetProgramLogSize(prog,C.byref(size)));log=C.create_string_buffer(size.value);check(lib.nvrtcGetProgramLog(prog,log))
  if code:raise RuntimeError(log.value.decode('utf-8','replace'))
  check(lib.nvrtcGetPTXSize(prog,C.byref(size)));blob=C.create_string_buffer(size.value);check(lib.nvrtcGetPTX(prog,blob));output.write_bytes(blob.value+b'\n')
  source.with_suffix('.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'ptx_sha256':hashlib.sha256(output.read_bytes()).hexdigest()},indent=2)+'\n',encoding='utf-8')
  print(json.dumps({'ptx_bytes':output.stat().st_size,'combat_integrated':False}))
 finally:
  if prog:lib.nvrtcDestroyProgram(C.byref(prog))
