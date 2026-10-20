"""Evaluate skipping an empty stat-notice continuation after all correctness gates."""
import hashlib, importlib.util, io, json, statistics, struct, subprocess, sys, tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='ed68e6847fe8e7f0d13ed81a6af6dec6837ca915'
sys.path[:0]=[str(R/d) for d in ('app','scripts')]
from portable_backend import execute,source_hashes
from portable_runtime import pack_programs
from portable_specs import LIMITS as L,ABI
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def prepare(variant):
    folder=P/'portable-build'/('named-states-'+variant);folder.mkdir(parents=True,exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',SOURCE,'gpu'],cwd=R))) as archive:archive.extractall(folder,filter='data')
    if variant=='skip-empty':
        path=folder/'gpu/event_runtime.slang';s=path.read_text();needle='if (f.event == 2 && (buff.buffEvent >> 2) != 0)';assert s.count(needle)==1
        s=s.replace(needle,'if (f.event == 2 && (buff.buffEvent >> 2) != 0 && f.value != 0)');path.write_text(s)
    path=folder/(variant+'_named_runtime.slang');path.write_text('#include "gpu/event_runtime.slang"\n');return path.relative_to(R).as_posix()
def workloads(v):
    rows={}
    for name,target,observed in [('ordinary','self',False),('observed-one','self',True),('lazy-no-notice','allies_top_atk:1',True),('empty-no-notice','allies_with_buff:missing',True),('observed-twenty-one',['self']*21,True)]:
        effects=[dict(name='modifier',source='스킬1',type='buff',stat='dot_dmg_pct' if observed else 'atk_pct',fixed_value=1,target=target,duration=-1,max_stack=1,trigger=dict(timing=['on_attack'],condition=[]))]
        if observed:effects.append(dict(name='observer',source='스킬1',type='buff',stat='atk_pct',fixed_value=1,target='self',duration=-1,max_stack=1000,trigger=dict(timing=['event:stat_applied:dot_dmg_pct'],condition=[])))
        case=dict(name=name,effects=effects,script=[[i/100,0,7,0,0,-1,0,0] for i in range(32)])
        batch=16 if name=='observed-twenty-one' else 64
        rows[name]=dict(programs=batch,input=pack_programs([v.compile_case(case)]*batch))
    return rows
def main():
    assert ABI==0x50455669
    order=load('portable-named-states-timing-order');g=load('portable-named-states-global-gates');pre=load('portable-named-states-pre-optimization')
    assert order['passed'] and order['windows_execution_and_transfer_terminal'] and not order['verification_processes']
    assert g['passed'] and g['complete'] and len(g['gates'])==27 and pre['passed'] and pre['source_commit']==SOURCE
    production=source_hashes('gpu/event_runtime.slang');assert production==pre['source_sha256']
    current=load('portable-combat-metal');assert current['output_sha256']==pre['output_sha256']
    spec=importlib.util.spec_from_file_location('named_main',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    authored=workloads(v);paths={name:prepare(name) for name in ('control','skip-empty')}
    import portable_runtime
    original=portable_runtime.execute;parity={}
    def compare(source,entry,packed,iw,ow,backend):
        assert source=='gpu/event_runtime.slang' and backend=='metal' and not parity
        outputs=[]
        for variant,path in paths.items():
            raw,e=execute(path,entry,packed,iw,ow,backend);outputs.append(raw);parity[variant]=e
        assert outputs[0]==outputs[1] and parity['control']['output_sha256']==current['output_sha256']
        save('portable-named-states-candidate-parity',dict(passed=True,inputs=1893,source_commit=SOURCE,all_input_and_output_bytes_equal=True,parity=parity))
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
        rows[name]=dict(programs=work['programs'],median_gpu_seconds=medians,skip_to_control_ratio=medians['skip-empty']/medians['control'],ranges=ranges,samples=samples)
    assert production==source_hashes('gpu/event_runtime.slang')
    save('portable-named-states-benchmark',dict(passed=True,source_commit=SOURCE,production_source_sha256=production,production_change_adopted=False,tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),inputs=1893,all_input_and_output_bytes_equal=True,parity=parity,workloads=rows,timing_order=order,scope='Sequential warmup and3 measured samples per variant, Apple M5. No full-roster/CUDA-speed/peak-memory claim. Desktop GPU activity not excluded.'))
if __name__=='__main__':main()
