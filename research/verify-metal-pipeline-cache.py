"""Bounded native archive proof, including a valid-hash foreign archive miss."""
import argparse,hashlib,json,os,shutil,struct,subprocess,sys,fcntl,select,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_backend import metal_compile_command
from portable_metal_cache import verify

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    out=args.out.resolve();out.mkdir(exist_ok=False)
    consumer=ROOT/'scripts/run-metal-probe.swift'
    source=out/'probe.metal'
    code='''#include <metal_stdlib>
using namespace metal;
struct State { uint value; uint extra; };
kernel void portableProbe(device const uint* input [[buffer(0)]], device uint* output [[buffer(1)]], device State* states [[buffer(2)]], uint index [[threadgroup_position_in_grid]]) {
 states[index].value=input[index+1];states[index].extra=1;output[index]=states[index].value+states[index].extra;
}
'''
    source.write_text(code)
    rows=[];gpu_calls=0
    def run(name,shader=source,cache=None,required=False,value=7,expected=8,fail=None,publication=None):
        nonlocal gpu_calls
        input_path=out/(name+'.input');output_path=out/(name+'.readback')
        input_path.write_bytes(struct.pack('<II',1,value))
        env=os.environ.copy()
        for key in ['NIKKE_METAL_PIPELINE_CACHE','NIKKE_METAL_PIPELINE_REQUIRED']:env.pop(key,None)
        if cache:env['NIKKE_METAL_PIPELINE_CACHE']=str(cache)
        if required:env['NIKKE_METAL_PIPELINE_REQUIRED']='1'
        command=metal_compile_command(['swift',str(consumer),str(shader),str(input_path),str(output_path),'portableProbe','1','1','8'],env.get('NIKKE_METAL_MODULE_CACHE'))
        if publication is None:p=subprocess.run(command,env=env,capture_output=True,text=True,timeout=120)
        else:
            lock,held,record_path=publication;child=subprocess.Popen(command,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            prefix='';deadline=time.monotonic()+15
            try:
                while 'portable_stage=pipeline_lock' not in prefix:
                    remaining=deadline-time.monotonic();assert remaining>0
                    ready,_,_=select.select([child.stderr],[],[],remaining);assert ready
                    line=child.stderr.readline();assert line;prefix+=line
                time.sleep(.2);assert child.poll() is None
                held.rename(record_path);fcntl.flock(lock,fcntl.LOCK_UN)
                stdout,stderr=child.communicate(timeout=120)
                p=subprocess.CompletedProcess(command,child.returncode,stdout,prefix+stderr)
            finally:
                if held.exists():held.rename(record_path)
                fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
                if child.poll() is None:child.kill();child.communicate()
        row=dict(name=name,exit_code=p.returncode,stderr=p.stderr)
        if fail:
            assert p.returncode!=0 and fail in p.stderr,(name,p.stdout,p.stderr)
            assert 'portable_stage=gpu_dispatch' not in p.stderr and not output_path.exists()
            row.update(rejected_before_dispatch=True,expected_failure=fail)
        else:
            assert p.returncode==0,(name,p.stderr)
            t=json.loads(p.stdout);assert t['command_status']=='completed' and t['runtime_stride_bytes']==8 and t['runtime_physical_stride_verified']
            assert output_path.read_bytes()==struct.pack('<I',expected)
            verify(t,dict(metal_pipeline_cache_enabled=bool(cache),metal_pipeline_cache_required=required),shader.read_bytes(),consumer.read_bytes(),entry='portableProbe')
            row.update(transport=t,output_sha256=hashlib.sha256(output_path.read_bytes()).hexdigest());gpu_calls+=1
        rows.append(row);(out/(name+'.json')).write_text(json.dumps(row,indent=2)+'\n')
        return row
    disabled=run('disabled')
    cache=out/'cache';cold=run('cold',cache=cache)
    key=cold['transport']['pipeline_cache']['key']
    lock=(cache/(key+'.lock')).open('a+b');fcntl.flock(lock,fcntl.LOCK_EX)
    record_path=cache/(key+'.json');held=out/'publication-held-record.json';record_path.rename(held)
    warm=run('warm',cache=cache,required=True,value=11,expected=12,publication=(lock,held,record_path))
    assert warm['transport']['pipeline_lock_wait_seconds']>=.15
    assert not cold['transport']['pipeline_cache']['hit'] and warm['transport']['pipeline_cache']['hit']
    assert warm['transport']['pipeline_cache']['archive_compile_seconds']==0
    assert cold['transport']['pipeline_cache']['key']==warm['transport']['pipeline_cache']['key']
    changed=out/'changed.metal';changed.write_text(code+'\n// exact source change\n')
    miss=run('required-miss',shader=changed,cache=cache,required=True,fail='Required Metal pipeline cache miss')
    assert 'portable_stage=library_compile' not in miss['stderr']
    corrupt=out/'corrupt-cache';shutil.copytree(cache,corrupt)
    p=corrupt/(key+'.metalarc');data=p.read_bytes();p.write_bytes(bytes([data[0]^1])+data[1:])
    bad=run('corrupt',cache=corrupt,required=True,fail='Metal pipeline cache integrity failure')
    assert 'portable_stage=library_compile' not in bad['stderr']
    # A correct byte hash is insufficient: the native API must also reject an
    # archive containing a different kernel instead of silently compiling.
    foreign=out/'foreign.metal';foreign.write_text(code.replace('extra=1','extra=13'))
    other=run('foreign-cold',shader=foreign,cache=out/'foreign-cache',expected=20)
    info=other['transport']['pipeline_cache'];injected=out/'foreign-injected';injected.mkdir()
    shutil.copyfile(out/'foreign-cache'/(info['key']+'.metalarc'),injected/(key+'.metalarc'))
    record=json.loads((cache/(key+'.json')).read_text());record.update(archive_sha256=info['archive_sha256'],archive_bytes=info['archive_bytes'])
    (injected/(key+'.json')).write_text(json.dumps(record))
    rejected=run('foreign-rejected',cache=injected,required=True,fail='Metal binary archive pipeline failure')
    assert 'portable_stage=pipeline_compile' in rejected['stderr']
    assert 'portable_stage=pipeline_archive_compile' not in rejected['stderr']
    report=dict(passed=True,gpu_calls=gpu_calls,successes=4,rejected_before_dispatch=3,concurrent_publication_handoff_verified=True,
        shared_consumer_sha256=hashlib.sha256(consumer.read_bytes()).hexdigest(),cases=rows,
        scope='Native Metal cache identity/integrity and fail-on-archive-miss; not shared battle calculation proof')
    (out/'proof.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,gpu_calls=gpu_calls,rejected_before_dispatch=3)))

if __name__=='__main__':main()
