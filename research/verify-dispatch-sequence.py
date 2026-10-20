"""Run all previous core inputs plus44 repeats across the2048 boundary.

Compare raw words, including expected failures, with the completed proof. No
CPU trajectory or synthesized GPU output is used. CPU references remain proved
by that byte-identical prior readback; this is a transport-specific gate.
"""
import argparse,array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_runtime import dispatch_programs,pack_programs
from portable_specs import LIMITS as L
from portable_backend import source_hashes
PRIOR='7492276247a23f81ca48d8f17336abb7860b2a62'
class Collected(BaseException):pass

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=['metal','cuda'],default='metal');args=parser.parse_args()
    before=source_hashes('gpu/event_runtime.slang')
    tracked=['app/portable_backend.py','app/portable_runtime.py','scripts/run-metal-probe.swift','scripts/verify-portable-combat.py','research/verify-dispatch-sequence.py','tests/test_portable_batch_sequence.py']
    hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in tracked}
    prior=json.loads(subprocess.check_output(['git','show',PRIOR+':research/portable-combat-metal.json'],cwd=R));assert prior['passed']
    assert before==prior['source_sha256']
    spec=importlib.util.spec_from_file_location('sequence_core',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    programs=[]
    def collect(p,**kwargs):programs.extend(p);raise Collected()
    report=R/f'research/portable-combat-{args.backend}.json';saved=report.read_bytes() if report.exists() else None
    old_argv=sys.argv;sys.argv=[sys.argv[0],'--backend',args.backend];v.run_programs=collect
    try:
        try:v.main()
        except Collected:pass
    finally:
        sys.argv=old_argv
        if saved is None:report.unlink(missing_ok=True)
        else:report.write_bytes(saved)
    assert len(programs)==2006
    old_packed=pack_programs(programs);assert hashlib.sha256(old_packed).hexdigest()==prior['input_sha256']
    # Third dispatch is short; positives after expected failures also exercise
    # reinitialization of the same output buffer rather than fresh allocations.
    full=programs+programs[:44];assert len(full)>L['BATCH']
    raw,evidence=dispatch_programs(full,backend=args.backend,batch_size=1024)
    stride=L['OUTPUT_WORDS']*4;prefix=memoryview(raw)[:2006*stride];tail=memoryview(raw)[2006*stride:]
    assert hashlib.sha256(prefix).hexdigest()==prior['output_sha256']
    assert tail==memoryview(raw)[:44*stride]
    statuses=[struct.unpack_from('<I',raw,i*stride)[0] for i in range(2050)]
    assert statuses==prior['actual_statuses']+prior['actual_statuses'][:44]
    assert [e['transport']['cases'] for e in evidence['dispatches']]==[1024,1024,2]
    assert source_hashes('gpu/event_runtime.slang')==before
    for p,h in hashes.items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,p
    result=dict(passed=True,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),previous_proof_commit=PRIOR,programs=2050,prior_programs=2006,repeated_programs=44,batch_size=1024,dispatch_counts=[1024,1024,2],previous_input_sha256=prior['input_sha256'],previous_output_sha256=prior['output_sha256'],prefix_output_sha256=hashlib.sha256(prefix).hexdigest(),repeat_output_sha256=hashlib.sha256(tail).hexdigest(),all_previous_output_words_equal=True,repeated_output_words_equal=True,actual_statuses=statuses,validation_sha256=hashes,**evidence,scope='Transport regression including all2006 prior inputs and44 exact repeats, using one pipeline/context and two reused buffers. Does not certify additional effects or characters.')
    (R/f'research/portable-dispatch-sequence-{args.backend}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,backend=args.backend,programs=2050,dispatches=[1024,1024,2],previous_output_sha256=result['prefix_output_sha256'])))
if __name__=='__main__':main()
