"""After all gates: evaluate eliminating the now-redundant round-end clear.

Both variants retain the common physical-mode end reset. No CPU result enters
GPU input, no output words are normalized, and production remains fixed.
"""
import argparse,array,copy,hashlib,importlib.util,io,json,statistics,subprocess,sys,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research'
sys.path[:0]=[str(R/d) for d in ('app','scripts')]
from portable_backend import execute,source_hashes
from portable_runtime import pack_programs
from portable_specs import LIMITS as L
SOURCE='2e1a265a58622cde3bdeef9c4bd9c9e3ad0d4e9c'

def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,r):(P/(n+'.json')).write_text(json.dumps(r,indent=2)+'\n')

def prepare(variant):
    folder=P/'portable-build'/('session-end-'+variant);folder.mkdir(parents=True,exist_ok=True)
    raw=subprocess.check_output(['git','archive',SOURCE,'gpu'],cwd=R)
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:archive.extractall(folder,filter='data')
    if variant=='central':
        path=folder/'gpu/combat_runtime.slang';text=path.read_text()
        old='s.frameAmmoActive[who] = 0; clearMode(s,who,when);'
        assert text.count(old)==1;text=text.replace(old,'clearMode(s,who,when);');path.write_text(text,newline='\n')
    source=folder/'session_end.slang';source.write_text('#include "gpu/event_runtime.slang"\n')
    return source.relative_to(R).as_posix()

def run(source,programs):
    raw,evidence=execute(source,'portableEvents',pack_programs(programs),L['INPUT_WORDS'],L['OUTPUT_WORDS'],'metal')
    words=array.array('I');words.frombytes(raw)
    if sys.byteorder!='little':words.byteswap()
    assert all(words[i*L['OUTPUT_WORDS']]==0 for i in range(len(programs)))
    assert hashlib.sha256(raw).hexdigest()==evidence['output_sha256']
    return raw,evidence

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',required=True,choices=('parity','timing'));args=parser.parse_args()
    gates=load('portable-session-identity-global-gates');order=load('portable-session-identity-timing-order')
    assert gates['passed'] and gates['complete'] and len(gates['gates'])==21
    assert order['passed'] and order['windows_execution_and_transfer_terminal'] and not order['verification_processes']
    original=source_hashes('gpu/event_runtime.slang')
    spec=importlib.util.spec_from_file_location('end_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    sources={k:prepare(k) for k in ('redundant','central')}
    if args.phase=='parity':
        programs=[v.compile_case(c) for c in v.fixtures()];rows={};expected=None
        for variant,source in sources.items():
            raw,evidence=run(source,programs)
            if expected is None:expected=raw
            assert raw==expected;rows[variant]=evidence
        result=dict(passed=True,positive_inputs=len(programs),all_output_words_equal=True,variants=rows)
    else:
        parity=load('portable-session-end-parity');assert parity['passed'] and parity['production_source_sha256']==original
        workloads={}
        for workload in ('exit-once','exit-every-frame'):
            c=copy.deepcopy(next(c for c in v.fixtures() if c['name']=='mode-round-limit-restores-magazine'))
            c['combat']['trace']='summary';c['script']=[[3,24,0,0,0,-1,0,0],[3,2,0,0,-1,0,0,0]]
            if workload=='exit-every-frame':
                c['effects'][1]['duration_bullets']=1
                c['effects'].append(dict(name='reenter every end',source='스킬1',type='instant',stat='force_skill_use',fixed_value=0,target='self',target_skill='스킬3',trigger=dict(timing=['event:state_end:mode'],condition=[])))
                c['owners']=[0]*len(c['effects'])
            programs=[v.compile_case(c)]*64;rows={k:[] for k in sources};expected=None
            for sample in range(4):
                for variant,source in sources.items():
                    raw,evidence=run(source,programs)
                    if expected is None:expected=raw
                    assert raw==expected
                    rows[variant].append(dict(warmup=sample==0,**evidence))
                    print(workload,sample,variant,evidence['transport']['gpu_seconds'],flush=True)
            medians={k:statistics.median(x['transport']['gpu_seconds'] for x in values[1:]) for k,values in rows.items()}
            workloads[workload]=dict(median_gpu_seconds=medians,central_to_redundant_ratio=medians['central']/medians['redundant'],samples=rows)
        result=dict(passed=True,production_change_adopted=False,workloads=workloads,
                    scope='Sequential 64-input batches, 3 seconds, one warmup and three samples; all output bytes equal; desktop GPU activity not excluded.')
    assert source_hashes('gpu/event_runtime.slang')==original
    result.update(source_commit=SOURCE,production_source_sha256=original,timing_order=order)
    save('portable-session-end-'+('parity' if args.phase=='parity' else 'benchmark'),result)

if __name__=='__main__':main()
