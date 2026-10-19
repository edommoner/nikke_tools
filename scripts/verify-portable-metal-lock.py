"""Prove the Metal pipeline lock with a held parent lock and real GPU child.
The lock covers compilation only. This is not a GPU performance benchmark.
"""
import fcntl,hashlib,importlib.util,json,select,struct,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_runtime import decode
from portable_specs import LIMITS as L
from portable_backend import source_hashes


def main():
    spec=importlib.util.spec_from_file_location('combat_lock_verifier',ROOT/'scripts/verify-portable-combat.py')
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    case=verifier.fixtures()[0];program,metadata=verifier.compile_case(case)
    build=ROOT/'research/portable-build';shader=build/'event_runtime.metal';assert shader.exists()
    hashes=source_hashes('gpu/event_runtime.slang')
    with tempfile.TemporaryDirectory(prefix='lock-proof-',dir=build) as temp,open(build/'metal-pipeline.lock','a+b') as lock:
        input_path=Path(temp)/'input.bin';output_path=Path(temp)/'output.bin'
        packed=struct.pack('<'+'I'*(1+len(program)),1,*program);input_path.write_bytes(packed)
        fcntl.flock(lock,fcntl.LOCK_EX)
        process=subprocess.Popen(['swift',str(ROOT/'scripts/run-metal-probe.swift'),str(shader),str(input_path),str(output_path),'portableEvents',str(L['INPUT_WORDS']),str(L['OUTPUT_WORDS'])],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        diagnostic='';deadline=time.monotonic()+15
        try:
            while 'portable_stage=pipeline_lock' not in diagnostic:
                remaining=deadline-time.monotonic();assert remaining>0,'Swift never reached the pipeline lock'
                ready,_,_=select.select([process.stderr],[],[],remaining);assert ready
                line=process.stderr.readline();assert line,'Swift exited before reaching the lock';diagnostic+=line
            time.sleep(.2)
            assert process.poll() is None,'Child did not block on the held compilation lock'
            fcntl.flock(lock,fcntl.LOCK_UN)
            stdout,stderr=process.communicate(timeout=120);diagnostic+=stderr
            assert process.returncode==0,diagnostic
            transport=json.loads(stdout);assert transport['pipeline_lock_wait_seconds']>=.19,transport
            assert transport['command_status']=='completed'
            raw=output_path.read_bytes();actual=decode(struct.unpack('<'+'I'*L['OUTPUT_WORDS'],raw),metadata)
            assert actual['status']==0;verifier.contains(actual['queries'],case['expected_queries'],case['name'])
        finally:
            fcntl.flock(lock,fcntl.LOCK_UN)
            if process.poll() is None:process.kill();process.communicate()
    assert hashes==source_hashes('gpu/event_runtime.slang')
    report=dict(passed=True,gpu_execution_verified=True,scope='One real GPU case with an intentionally held parent compilation lock; not a performance benchmark',transport=transport,source_sha256=hashes,
        generated_sha256=hashlib.sha256(shader.read_bytes()).hexdigest(),input_sha256=hashlib.sha256(packed).hexdigest(),output_sha256=hashlib.sha256(raw).hexdigest(),
        validation_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('scripts/run-metal-probe.swift','scripts/verify-portable-metal-lock.py','scripts/verify-portable-combat.py','app/portable_runtime.py')},diagnostic=diagnostic)
    (ROOT/'research/portable-metal-pipeline-lock.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,device=transport['device'],pipeline_lock_wait_seconds=transport['pipeline_lock_wait_seconds'],gpu_execution_verified=True)))


if __name__=='__main__':main()
