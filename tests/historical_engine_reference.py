"""Explicit CPU-only old-engine binding for immutable historical evidence tests.

These tests retain old GPU buffers/fingerprints and make no current-engine
parity claim. Ordinary product evaluation always keeps the current engine.
"""
import functools,hashlib,json,os,subprocess,sys,types,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD_REVISION='23164e4a88fe46af609cc99b0de38a98313a5f4d'
PINS={'calculator/timeline.py': 'f0504cb63db62b8453396bd7ebfe2b7a023f3161f65338c696d64db06d39b299', 'calculator/buff_manager.py': '803c252e3b07515c12a19feb9006853051ab5d3da365046899162766e40d6ce4', 'data/parsed_nikke.json': '88b565abcf55ccc391491803978a83d28fdb499b61d82e32118c6ea72f0369f6', 'data/parsed_skills.json': '81e2934af7c91b69a49b71721d5f53af25b5ebf006595d3e929db4582ff23137', 'data/base_stat_tables/cube.json': '6d9fe4e50fe780a0245347ae5d86ba21f950bd56345de09c18cd62e68a95bba8'}

def install():
    if 'engine_worker' in sys.modules:raise RuntimeError('Historical engine must be selected before product imports')
    engine=ROOT/'research/upstream/nikke-calc-23164e4'
    for name,digest in PINS.items():
        if hashlib.sha256((engine/name).read_bytes()).hexdigest()!=digest:raise ValueError('Historical reference bytes changed: '+name)
    path=ROOT/'app/engine_worker.py';source=path.read_text()
    anchor="ENGINE = ROOT / 'research/upstream/nikke-calc-master'"
    if source.count(anchor)!=1:raise ValueError('Historical engine adapter anchor changed')
    source=source.replace(anchor,"ENGINE = ROOT / 'research/upstream/nikke-calc-23164e4'")
    source=source.replace("REVISION = '67835ca3033a95482749ea2db35a8ee2a0856a92'","REVISION = '"+OLD_REVISION+"'")
    sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research'),str(ROOT/'tests')]
    module=types.ModuleType('engine_worker');module.__file__=str(path);sys.modules['engine_worker']=module
    exec(compile(source,str(path),'exec'),module.__dict__)
    os.environ['NIKKE_TEST_HISTORICAL_ENGINE']=OLD_REVISION
    # Historical comparison never authorizes any device execution.
    import portable_backend
    def forbidden(*args,**kwargs):raise RuntimeError('Device execution forbidden in historical CPU reference')
    portable_backend.execute=forbidden;portable_backend.execute_batches=forbidden
    return module

def historical_reference(method):
    """Re-run this exact test in a fresh, explicitly pinned CPU process."""
    @functools.wraps(method)
    def run(self,*args,**kwargs):
        if os.environ.get('NIKKE_TEST_HISTORICAL_ENGINE')==OLD_REVISION:
            import engine_worker
            if engine_worker.ENGINE.name!='nikke-calc-23164e4':raise AssertionError('Historical engine marker without historical engine')
            return method(self,*args,**kwargs)
        code="import sys;sys.path.insert(0,'tests');import historical_engine_reference as h;h.install();import unittest; r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName(sys.argv[1]));sys.exit(not r.wasSuccessful())"
        result=subprocess.run([sys.executable,'-W','ignore::ResourceWarning','-c',code,self.id()],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,'Historical '+OLD_REVISION+' comparison failed:\n'+result.stdout+result.stderr)
    return run


def source_preimage(root,name):
    """Verify current bytes and the exact archived source used by an old seal."""
    root=Path(root);raw=(root/'tests/fixtures/reference-engine-upstream-history-v1.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!='8a9a84b4de04ebb8d425054e9ba5131b9bb774045447f8bd15ea51122c9ef961':raise ValueError('Upstream source history changed')
    row=json.loads(raw)['files'].get(name)
    current=(root/name).read_bytes()
    if row is None:return current
    if hashlib.sha256(current).hexdigest()!=row['current_sha256']:raise ValueError('Unreviewed current upstream bytes: '+name)
    old=(root/row['old_path']).read_bytes()
    if hashlib.sha256(old).hexdigest()!=row['old_sha256']:raise ValueError('Historical upstream bytes changed: '+name)
    return old
