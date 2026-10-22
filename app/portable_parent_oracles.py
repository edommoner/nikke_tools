"""One-parent preflight oracles, never a saved-result or independent-audit cache."""
import contextlib,copy,hashlib,os,pickle,threading
from pathlib import Path
from unittest.mock import patch


def stamp(value):
    # Only fingerprint live trusted Python objects; never deserialize pickle.
    return hashlib.sha256(pickle.dumps(value,protocol=5)).hexdigest()


def leaf(adapter,domain):
    seen=set()
    while domain is not None:
        branches=getattr(adapter,'adapters',getattr(adapter,'ADAPTERS',None))
        if not isinstance(branches,dict) or not isinstance(domain,(tuple,list)) or len(domain)!=2 or not isinstance(domain[0],str) or domain[0] not in branches:break
        if id(adapter) in seen:raise ValueError('Cyclic native adapter routing')
        seen.add(id(adapter));adapter,domain=branches[domain[0]],domain[1]
    return adapter,domain


def provider(adapter,domain):
    """Recognize existing compare call sites, leaving other protocols fresh."""
    adapter,domain=leaf(adapter,domain);fn=adapter.compare
    g=getattr(fn,'__globals__',None);code=getattr(fn,'__code__',None)
    if not isinstance(g,dict) or code is None:return None
    names=code.co_names
    native=getattr(adapter,'native_reference',None)
    if native is not None and g.get('native_reference') is native and 'native_reference' in names:
        return (g,'native_reference',native,domain,'reference')
    real=g.get('real')
    if 'real' in names and 'native_reference' in names and callable(getattr(real,'native_reference',None)):
        return (real,'native_reference',real.native_reference,domain[0]['body'],'tuple')
    suite=getattr(adapter,'suite',None)
    if g.get('suite') is suite and suite is not None and 'inspect_native' in names and callable(getattr(suite,'inspect_native',None)):
        return (suite,'inspect_native',suite.inspect_native,domain[0],'tuple')
    return None


class ParentOracles:
    """Owned by one live run invocation; data never crosses a process or file."""
    def __init__(self,manifest,capture):
        self.pid=os.getpid();self.thread=threading.get_ident();self.capture=Path(capture).resolve()
        self.package_id=manifest['package_id'];self.golden=copy.deepcopy(manifest['golden'])
        self.adapter=None;self.entries=[];self.records=[];self.closed=False;self.used=False
        self.hits=0;self.fresh=0;self.rejections=0;self.next_index=0
        self.usable=True;self.native_cases=0;self.case_count=0

    def check(self,manifest,capture):
        if self.closed or self.pid!=os.getpid() or self.thread!=threading.get_ident():raise ValueError('Preflight oracles require their live parent owner')
        if self.package_id!=manifest['package_id'] or self.golden!=manifest['golden'] or self.capture!=Path(capture).resolve():raise ValueError('Preflight oracle package/capture mismatch')

    def prepare(self,adapter,entries):
        if self.adapter is not None:raise ValueError('Preflight oracle snapshot already prepared')
        self.adapter=adapter
        # Drop the large per-entry word arrays. Domains retain the same objects
        # the existing comparators use; saved input is independently streamed.
        self.entries=[(name,None,domain) for name,_,domain in entries]
        self.case_count=len(entries);self.native_cases=sum(domain is not None for _,_,domain in entries)

    def before(self,index):
        domain=self.entries[index][2]
        if domain is None or not self.usable:return None
        try:
            domain_stamp=stamp(domain);target=provider(self.adapter,domain)
            return target,stamp(target[3]) if target is not None else None,domain_stamp
        except (TypeError,pickle.PicklingError,AttributeError):
            self.usable=False;return None

    def remember(self,index,before,value,digest):
        expected=self.golden['entries'][index]['native_sha256']
        if digest(value)!=expected:raise ValueError('Preflight native fingerprint changed')
        record=None
        if before is not None:
            target,fingerprint,domain_stamp=before
            if stamp(self.entries[index][2])!=domain_stamp:raise ValueError('Native oracle mutated its comparison input')
            record=dict(target=None,domain_stamp=domain_stamp)
            if target is not None:
                if stamp(target[3])!=fingerprint:raise ValueError('Native oracle mutated its comparison input')
                if target[4]=='reference' or isinstance(value,dict) and set(value)=={'battle','skill_trace'}:
                    record.update(target=target,stamp=fingerprint,value=copy.deepcopy(value),digest=digest,expected=expected)
        if index!=len(self.records):raise ValueError('Preflight oracle order changed')
        self.records.append(record)

    def finish(self):
        if not self.usable:
            # Unknown object protocols use a fresh prepare and fresh native
            # execution in the original path, not possibly mutated domains.
            self.entries.clear();self.records.clear();self.adapter=None

    def fallback_receipt(self):
        return dict(scope='live-parent-preflight',reused_native_cases=0,fresh_native_cases=self.native_cases,rejection_cases=self.case_count-self.native_cases,
                    fallback_reason='unfingerprintable-domain',saved_results_used=False,independent_audit_reuse=False)

    def start(self,manifest,capture):
        self.check(manifest,capture)
        if not self.usable or self.used or self.adapter is None or len(self.records)!=len(self.entries):raise ValueError('Preflight oracles incomplete or already consumed')
        self.used=True

    @contextlib.contextmanager
    def comparison(self,index):
        if self.closed or not self.used or self.pid!=os.getpid() or self.thread!=threading.get_ident() or index!=self.next_index:raise ValueError('Preflight oracle comparison owner/order changed')
        self.next_index+=1
        record=self.records[index];domain=self.entries[index][2]
        if domain is None:self.rejections+=1;yield;return
        if record is None or stamp(domain)!=record['domain_stamp']:raise ValueError('Preflight comparison domain changed')
        if record['target'] is None:
            self.fresh+=1;yield
            if stamp(domain)!=record['domain_stamp']:raise ValueError('Comparator mutated its preflight input')
            return
        target=record['target'];owner,key,original,arg,kind=target
        current=owner.get(key) if isinstance(owner,dict) else getattr(owner,key)
        if current is not original or stamp(arg)!=record['stamp']:raise ValueError('Preflight oracle provider/input changed')
        if record['digest'](record['value'])!=record['expected']:raise ValueError('Preflight oracle value changed')
        calls=0
        def cached(*args,**kwargs):
            nonlocal calls
            if self.pid!=os.getpid() or self.thread!=threading.get_ident() or len(args)!=1 or args[0] is not arg or kwargs or stamp(arg)!=record['stamp']:
                raise ValueError('Unexpected preflight oracle request')
            calls+=1;value=copy.deepcopy(record['value'])
            return value if kind=='reference' else (value['battle'],value['skill_trace'])
        if isinstance(owner,dict):
            owner[key]=cached
            try:yield
            finally:owner[key]=original
        else:
            with patch.object(owner,key,cached):yield
        if stamp(arg)!=record['stamp'] or stamp(domain)!=record['domain_stamp']:raise ValueError('Comparator mutated its preflight input')
        if calls:self.hits+=1
        else:self.fresh+=1

    def receipt(self):
        return dict(scope='live-parent-preflight',reused_native_cases=self.hits,fresh_native_cases=self.fresh,rejection_cases=self.rejections,saved_results_used=False,independent_audit_reuse=False)

    def close(self):
        self.closed=True;self.entries.clear();self.records.clear();self.adapter=None
