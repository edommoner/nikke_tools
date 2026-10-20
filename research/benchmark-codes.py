"""Compare early integer code checks with the verified common predicate loop."""
import hashlib,importlib.util,io,json,statistics,struct,subprocess,sys,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='dd7d62b98a63f9fa99892dd964809775b136a9d6'
sys.path[:0]=[str(R/d) for d in ('app','scripts')]
from portable_backend import execute,source_hashes
from portable_runtime import pack_programs
from portable_specs import ABI,LIMITS as L
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def prepare(variant):
    folder=P/'portable-build'/('enemy-code-'+variant);folder.mkdir(parents=True,exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',SOURCE,'gpu'],cwd=R))) as archive:archive.extractall(folder,filter='data')
    if variant=='early':
        path=folder/'gpu/event_runtime.slang';s=path.read_text()
        old='''        if (kind == C_TARGET_CODE)
        {
            uint code=commands[s.inputBase+P_WORLD_META_BASE];
            if(code!=0 && code!=uint(name)) return false;
        }
'''
        assert s.count(old)==1;s=s.replace(old,'')
        needle='uint kind = commands[at]; int name = int(commands[at+1]); uint64_t arg = loadNumber(at+2);';assert s.count(needle)==1
        replacement='''uint kind = commands[at]; int name = int(commands[at+1]);
        if (kind == C_TARGET_CODE)
        {
            uint code=commands[s.inputBase+P_WORLD_META_BASE];
            if(code!=0 && code!=uint(name)) return false;
            continue;
        }
        uint64_t arg = loadNumber(at+2);'''
        path.write_text(s.replace(needle,replacement))
    path=folder/(variant+'_code_runtime.slang');path.write_text('#include "gpu/event_runtime.slang"\n');return path.relative_to(R).as_posix()
def workloads(v):
    rows={}
    for name,world,conditions in [('ordinary',None,[]),('one-match','전격',['target_code:전격']),('three-match','전격',['target_code:전격']*3),('one-miss','풍압',['target_code:전격']),('unspecified',None,['target_code:전격'])]:
        effect=dict(name='gate',source='스킬1',type='buff',stat='atk_pct',fixed_value=10,target='self',duration=-1,max_stack=1,trigger=dict(timing=['on_attack'],condition=conditions))
        script=sum(([[i/10,0,7,0,0,-1,0,0],[i/10,2,0,0,0,i,0,0]] for i in range(32)),[])
        case=dict(name=name,effects=[effect],script=script,environment=dict(enemy_code=world))
        rows[name]=dict(programs=64,input=pack_programs([v.compile_case(case)]*64))
    return rows
def main():
    assert ABI==0x5045566A
    order=load('portable-enemy-codes-timing-order');g=load('portable-enemy-codes-global-gates');pre=load('portable-enemy-codes-pre-optimization')
    assert order['passed'] and order['windows_execution_and_transfer_terminal'] and not order['verification_processes']
    assert g['passed'] and g['complete'] and len(g['gates'])==29 and pre['passed'] and pre['source_commit']==SOURCE
    production=source_hashes('gpu/event_runtime.slang');assert production==pre['source_sha256'];current=load('portable-combat-metal');assert current['output_sha256']==pre['output_sha256']
    spec=importlib.util.spec_from_file_location('code_main',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    authored=workloads(v);paths={name:prepare(name) for name in ('control','early')}
    import portable_runtime
    original=portable_runtime.execute;parity={}
    def compare(source,entry,packed,iw,ow,backend):
        assert source=='gpu/event_runtime.slang' and backend=='metal' and not parity
        outputs=[]
        for variant,path in paths.items():
            raw,e=execute(path,entry,packed,iw,ow,backend);outputs.append(raw);parity[variant]=e
        assert outputs[0]==outputs[1] and parity['control']['output_sha256']==current['output_sha256']
        save('portable-enemy-codes-candidate-parity',dict(passed=True,inputs=2006,source_commit=SOURCE,all_input_and_output_bytes_equal=True,parity=parity))
        return outputs[0],parity['control']
    report=P/'portable-combat-metal.json';saved=report.read_bytes();portable_runtime.execute=compare
    try:sys.argv=[sys.argv[0],'--backend','metal'];v.main()
    finally:report.write_bytes(saved);portable_runtime.execute=original
    rows={}
    for name,work in authored.items():
        samples={variant:[] for variant in paths};expected=None
        for sample in range(4):
            for variant,path in paths.items():
                raw,e=execute(path,'portableEvents',work['input'],L['INPUT_WORDS'],L['OUTPUT_WORDS'],'metal')
                if expected is None:expected=raw
                assert raw==expected
                for i in range(work['programs']):assert struct.unpack_from('<I',raw,i*L['OUTPUT_WORDS']*4)[0]==0
                samples[variant].append(dict(warmup=sample==0,**e));print(name,sample,variant,e['transport']['gpu_seconds'],flush=True)
        medians={k:statistics.median(x['transport']['gpu_seconds'] for x in a[1:]) for k,a in samples.items()}
        ranges={k:[min(x['transport']['gpu_seconds'] for x in a[1:]),max(x['transport']['gpu_seconds'] for x in a[1:])] for k,a in samples.items()}
        rows[name]=dict(programs=work['programs'],median_gpu_seconds=medians,early_to_control_ratio=medians['early']/medians['control'],ranges=ranges,samples=samples)
    assert production==source_hashes('gpu/event_runtime.slang')
    save('portable-enemy-codes-benchmark',dict(passed=True,source_commit=SOURCE,production_source_sha256=production,production_change_adopted=False,tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),inputs=2006,all_input_and_output_bytes_equal=True,parity=parity,workloads=rows,timing_order=order,scope='Sequential warmup and3 samples per variant on Apple M5,32 activations/queries per program. No full-roster/CUDA-speed/peak-memory claim; desktop GPU activity is not excluded.'))
if __name__=='__main__':main()
