"""Resolve shared CPU reference adapters in tests; no packaging or run cache."""

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
    # Routes may return temporary wrapper objects. Retain them until resolution
    # ends so Python cannot recycle an earlier id and report a false cycle.
    seen={}
    while True:
        adapter,domain=leaf(adapter,domain)
        if id(adapter) in seen:raise ValueError('Cyclic native comparison adapter routing')
        seen[id(adapter)]=adapter;route=getattr(adapter,'native_comparison_adapter',None)
        if route is None:break
        if not callable(route):raise ValueError('Native comparison adapter route must be callable')
        adapter=route(domain)
        if adapter is None:return None
        if not callable(getattr(adapter,'compare',None)):raise ValueError('Native comparison adapter must preserve its comparator')
    fn=adapter.compare
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

