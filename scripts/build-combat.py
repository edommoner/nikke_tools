"""Build checked-in PTX using the local NVIDIA NVRTC; not required at runtime."""
import ctypes as C,os,json,hashlib,argparse
from pathlib import Path
from detail_build_contract import checked_detail_abi
root=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--source',choices=['combat','detail_effects'],default='combat');source=ap.parse_args().source
source_bytes=(root/f'app/{source}.cu').read_bytes()
abi=checked_detail_abi(source_bytes,(root/'app/detail_gpu.py').read_bytes()) if source=='detail_effects' else None
binpath=Path(os.environ.get('CUDA_PATH',r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.3'))/'bin'
dll_dir=os.add_dll_directory(str(binpath))
lib=C.WinDLL(str(next(binpath.glob('nvrtc64_*.dll'))))
prog=C.c_void_p()
lib.nvrtcCreateProgram.argtypes=[C.POINTER(C.c_void_p),C.c_char_p,C.c_char_p,C.c_int,C.c_void_p,C.c_void_p]
lib.nvrtcCompileProgram.argtypes=[C.c_void_p,C.c_int,C.POINTER(C.c_char_p)]
for name in ['nvrtcGetProgramLogSize','nvrtcGetPTXSize']:getattr(lib,name).argtypes=[C.c_void_p,C.POINTER(C.c_size_t)]
for name in ['nvrtcGetProgramLog','nvrtcGetPTX']:getattr(lib,name).argtypes=[C.c_void_p,C.c_void_p]
lib.nvrtcDestroyProgram.argtypes=[C.POINTER(C.c_void_p)]
try:
 assert lib.nvrtcCreateProgram(C.byref(prog),source_bytes,(source+'.cu').encode(),0,None,None)==0
 options=(C.c_char_p*3)(b'--gpu-architecture=compute_52',b'--std=c++11',b'--fmad=false')
 code=lib.nvrtcCompileProgram(prog,3,options)
 size=C.c_size_t();lib.nvrtcGetProgramLogSize(prog,C.byref(size));log=C.create_string_buffer(size.value);lib.nvrtcGetProgramLog(prog,log)
 if code:raise RuntimeError(log.value.decode())
 lib.nvrtcGetPTXSize(prog,C.byref(size));ptx=C.create_string_buffer(size.value);lib.nvrtcGetPTX(prog,ptx)
 assert (root/f'app/{source}.cu').read_bytes()==source_bytes,'CUDA source changed during compilation; result discarded.'
 (root/f'app/{source}.ptx').write_bytes(ptx.value+b'\n');print(f'{source}.ptx: {len(ptx.value)} bytes')
 (root/f'app/{source}-build.json').write_text(json.dumps({**({'abi':abi} if abi else {}),'source_sha256':hashlib.sha256(source_bytes).hexdigest(),'ptx_sha256':hashlib.sha256((root/f'app/{source}.ptx').read_bytes()).hexdigest(),'options':[x.decode() for x in options]},indent=2)+'\n',encoding='utf-8')
finally:
 if prog:lib.nvrtcDestroyProgram(C.byref(prog))
