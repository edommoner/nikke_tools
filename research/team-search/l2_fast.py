"""ctypes L2 interface. Construction never silently builds or falls back.

Run `python3.12 l2_fast.py build [--wasm]` first. Binaries and build receipts
are content addressed by source bytes, compiler version and exact flags.
"""
import argparse, ctypes as C, hashlib, json, os, pathlib, shutil, subprocess, sys
from l2_compile import compile_profiles, unpack
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CACHE=HERE/'l2_fast/.cache'
FLAGS=['-O2','-std=c++17','-ffp-contract=off']

def build(wasm=False):
    sources=['l2.cpp','l2.h','cli.cpp'];folder=HERE/'l2_fast'
    if wasm:
        sys.path.insert(0,str(ROOT/'app'));from portable_wasm import toolchain, FLAGS as WASM_FLAGS
        compiler,env=toolchain(ROOT);flags=list(WASM_FLAGS)+['-sEXPORTED_FUNCTIONS=["_l2_create","_l2_destroy","_l2_score_many","_alloc","_release","_l2_generate"]'];target='l2.wasm'
    else:
        compiler=shutil.which('clang++')
        if not compiler:raise FileNotFoundError('clang++ unavailable')
        env=os.environ.copy();flags=FLAGS;target='libl2.dylib' if sys.platform=='darwin' else 'libl2.so'
    version=subprocess.check_output([str(compiler),'--version'],env=env).decode()
    record=dict(sources={s:hashlib.sha256((folder/s).read_bytes()).hexdigest() for s in sources},compiler=version,flags=flags,wasm=wasm)
    identity=hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest();out=CACHE/identity;out.mkdir(parents=True,exist_ok=True)
    import fcntl
    with (out/'build.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        outputs=[out/target] if wasm else [out/target,out/'l2-cli']
        receipt=out/'build.json'
        if receipt.exists() and all(x.exists() for x in outputs):
            saved=json.loads(receipt.read_text())
            if all(saved['outputs'].get(x.name)==hashlib.sha256(x.read_bytes()).hexdigest() for x in outputs):return out/target
        base=[str(compiler),*flags,str(folder/'l2.cpp')]
        if wasm:subprocess.run([*base,'-o',str(out/target)],env=env,check=True)
        else:
            subprocess.run([*base,'-shared','-fPIC','-o',str(out/target)],env=env,check=True)
            subprocess.run([*base,str(folder/'cli.cpp'),'-o',str(out/'l2-cli')],env=env,check=True)
        receipt.write_text(json.dumps(dict(identity=identity,**record,outputs={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in outputs}),indent=2)+'\n')
    return out/target

def library_path():
    # Resolve the current content address without building, by checking receipts.
    sources={s:hashlib.sha256((HERE/'l2_fast'/s).read_bytes()).hexdigest() for s in ('l2.cpp','l2.h','cli.cpp')}
    compiler=shutil.which('clang++')
    version=subprocess.check_output([compiler,'--version']).decode() if compiler else ''
    for receipt in sorted(CACHE.glob('*/build.json')):
        r=json.loads(receipt.read_text())
        if not r['wasm'] and r['sources']==sources and r['compiler']==version and r['flags']==FLAGS:
            for name,digest in r['outputs'].items():
                if name.startswith('libl2'):
                    path=receipt.parent/name
                    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==digest:return path
    raise RuntimeError('L2 native library not built; run l2_fast.py build')

class Score:
    def __init__(self,profiles,library=None):
        self.profiles=profiles;self.chars=profiles['characters'];self.duration=profiles['settings']['duration']
        self.raw=compile_profiles(profiles);payload,self.metadata=unpack(self.raw);self.names=self.metadata['names'];self.index={n:i for i,n in enumerate(self.names)}
        self.lib=C.CDLL(str(library or library_path()));lib=self.lib
        lib.l2_create.argtypes=[C.POINTER(C.c_double),C.c_size_t];lib.l2_create.restype=C.c_void_p
        lib.l2_destroy.argtypes=[C.c_void_p]
        lib.l2_score_many.argtypes=[C.c_void_p,C.POINTER(C.c_uint32),C.c_size_t,C.POINTER(C.c_double),C.POINTER(C.c_double)];lib.l2_score_many.restype=C.c_int
        self.table=lib.l2_create((C.c_double*(len(payload)//8)).from_buffer_copy(payload),len(payload)//8)
        if not self.table:raise ValueError('invalid L2 table')
    @classmethod
    def load(cls,path,**kwargs):return cls(json.loads(pathlib.Path(path).read_text()),**kwargs)
    def close(self):
        if getattr(self,'table',None):self.lib.l2_destroy(self.table);self.table=None
    def __del__(self):self.close()
    def _indices(self,squads):
        rows=[]
        for squad in squads:
            if len(squad)!=5 or len(set(squad))!=5:raise ValueError('expected five distinct characters')
            rows.extend(self.index[n] for n in squad)
        return (C.c_uint32*len(rows))(*rows)
    def score_indices(self,indices,members=False):
        if not self.table:raise RuntimeError('closed L2 scorer')
        if len(indices)%5:raise ValueError('incomplete squad')
        n=len(indices)//5;totals=(C.c_double*n)();values=(C.c_double*(n*5))() if members else None
        rc=self.lib.l2_score_many(self.table,indices,n,totals,values)
        if rc:raise ValueError('invalid squad indices')
        return (totals,values) if members else totals
    def score_many(self,squads):return list(self.score_indices(self._indices(squads)))
    def member_scores(self,squad):
        _,v=self.score_indices(self._indices([squad]),True);return dict(zip(squad,v))
    def __call__(self,squad):return self.score_many([squad])[0]

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['build']);p.add_argument('--wasm',action='store_true');a=p.parse_args();print(build(a.wasm))
