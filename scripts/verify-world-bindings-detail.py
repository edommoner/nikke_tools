"""World identity queries plus reuse of the shared landing witnesses."""
import argparse,hashlib,importlib.util,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a
from detail_boss import empty_world
from detail_world import packed_enemy
from gpu_selector import Cuda
import detail_gpu as g

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
v=load('world_binding_impacts','scripts/verify-typed-impacts-detail.py')

def identities(device,backend):
    names=v.v.NAMES
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=a.META[n]) for n in names]
    stats={n:dict(atk=1000,hp=10000,**{'def':100}) for n in names}
    rows=[]
    for count in (0,3,32):
        program=g.compile_effects(chars,[])
        # Half of this table is destroyed by one authored area landing. The
        # other half is unbreakable. The identity and parent do not change.
        parts=[dict(name=str(i),hp=10 if i%2==0 else 0,reach=1) for i in range(count)]
        enemy=packed_enemy({'def':0,'core_px':0},parts)
        script=[];expected=[]
        def query(kind,identity,dead=False,expected_generation=0,present=True):
            script.append([0,2,133,0,kind+8*identity,len(expected),expected_generation,0])
            row=[int(present),kind,identity,1,int(not dead),0 if kind==1 else -1,0 if kind==1 else -1,1 if kind==1 else 0] if present else [0]*8
            expected.append(row+[0]*40)
        query(0,0)
        for i in range(count):query(1,i)
        query(1,count,present=False);query(0,0,expected_generation=2,present=False)
        if count:
            script.append([0,7,0,0,1,-1,10,-1])
            for i in range(count):query(1,i,dead=i%2==0,expected_generation=1)
        original=json.dumps(program,sort_keys=True)
        result=g.run(device,[program],script,[enemy],[stats],module_backend=backend)
        assert result['queries'][0]==expected,(count,result['queries'][0],expected)
        assert result['totals'][0]==[10*count,0,0,0,0]
        assert json.dumps(program,sort_keys=True)==original
        # Explicit and synthesized diagnostic tables must describe the same pool.
        program['world']=empty_world(count)
        explicit=g.run(device,[program],script,[enemy],[stats],module_backend=backend)
        assert explicit['queries']==result['queries'] and explicit['totals']==result['totals']
        rows.append(dict(name=f'configured-world-{count}-parts',passed=True,queries=len(expected),workspace_bytes=result['workspace_bytes']))
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');args=ap.parse_args()
    files=list((ROOT/'app').glob('*.py'))+[ROOT/'scripts'/name for name in ('verify-world-bindings-detail.py','verify-typed-impacts-detail.py','resource_frame_capture.py','verify-gauge-detail.py','verify-extended-detail.py','detail_coverage.py')]+[ROOT/'tests/test_world_actor_runtime.py',ROOT/'app/detail_effects.cu',ROOT/'data/engine-effect-overrides.json']
    files += [ROOT/'app'/name for name in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};start=time.perf_counter();device=Cuda()
    try:rows=identities(device,args.backend)+v.squads(device,args.backend)
    finally:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=all(row['passed'] for row in rows),backend=args.backend,cases=rows,source_stable=True,source_sha256=before,seconds=time.perf_counter()-start,cpu_trace_used_as_gpu_input=False,
        scope='Shared configured identity and body/fixed-part live lookups. Summon live pool, per-target routing and autonomous multi_hit producers remain unsupported. No new character admission.')
    (ROOT/f'research/world-bindings-{args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(rows),seconds=report['seconds'])),flush=True)

if __name__=='__main__':main()
