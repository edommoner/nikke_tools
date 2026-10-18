"""One-process exact-case reuse. All existing comparator assertions are retained.

No cross-build/disk result cache. Different comparator implementations, case
names, inputs, witnesses or backends never share an observation. Only successful
comparisons are reused. Source changes and reference rebindings invalidate reuse.
"""
import atexit, copy, hashlib, inspect, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
_session=None

class VerificationSession:
    def __init__(self, device_factory=None):
        self.device_factory=device_factory
        self.device=None;self.cache={};self.requests=0;self.executed=0;self.reused=0
        self.epoch=None;self.cases={}

    def fingerprint(self):
        # Cheap within-process mutation guard; no historical result reuse.
        upstream=ROOT/'research/upstream/nikke-calc-master'
        files=sorted(list((ROOT/'app').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+
                     list((ROOT/'app').glob('detail_effects*'))+
                     list(upstream.rglob('*.py'))+list((upstream/'data').rglob('*.json'))+
                     list((ROOT/'data').glob('*.json')))
        stamps=tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in files if p.is_file())
        bm=sys.modules.get('calculator.buff_manager');timeline=sys.modules.get('calculator.timeline')
        bindings=tuple((name,id(value)) for owner in (getattr(bm,'BuffManager',None),timeline,
            sys.modules.get('calculator.damage')) if owner is not None
            for name,value in sorted(vars(owner).items()) if callable(value))
        return stamps,bindings

    def compare(self,oracle,name,body,extra,backend='native'):
        self.requests+=1
        epoch=self.fingerprint()
        if epoch!=self.epoch:
            self.cache.clear();self.epoch=epoch
        fn=oracle.compare
        path=Path(inspect.getsourcefile(fn)).resolve()
        key=(str(path),hashlib.sha256(path.read_bytes()).hexdigest(),fn.__qualname__,name,backend,
             json.dumps([body,extra],sort_keys=True,ensure_ascii=False,allow_nan=False))
        case_id=hashlib.sha256(json.dumps(key).encode()).hexdigest()
        case=self.cases.setdefault(case_id,dict(id=case_id,name=name,backend=backend,
            comparator=str(path.relative_to(ROOT)),requests=0,executions=0))
        case['requests']+=1
        if key in self.cache:
            self.reused+=1
            return copy.deepcopy(self.cache[key])
        if self.device is None:
            if self.device_factory is None:
                from gpu_selector import Cuda
                self.device_factory=Cuda
            self.device=self.device_factory()
        self.executed+=1
        case['executions']+=1
        result=fn(self.device,name,copy.deepcopy(body),copy.deepcopy(extra),backend)
        if result.get('passed'):
            self.cache[key]=copy.deepcopy(result)
        return result

    def stats(self):
        return dict(requested_cases=self.requests,executed_cases=self.executed,
                    reused_exact_cases=self.reused,cases=list(self.cases.values()),
                    scope='Migrated recovery tests; exact comparator and inputs only')

    def close(self):
        if self.device is not None:self.device.close();self.device=None

def session():
    global _session
    if _session is None:_session=VerificationSession()
    return _session

def compare(*args,**kwargs):return session().compare(*args,**kwargs)
def stats():return session().stats()
def close():
    if _session is not None:_session.close()
atexit.register(close)
