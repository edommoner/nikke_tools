"""One component driver for CUDA/Metal, retaining raw evidence before checks."""
import argparse
import array
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_runtime import dispatch_programs,pack_programs,decode
from portable_specs import LIMITS as L
from portable_burst_charge_oracle import observe
from portable_burst_charge_validation import rejection_programs


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=['metal','cuda'],default='metal');parser.add_argument('--native-only',action='store_true')
    args=parser.parse_args()
    spec=importlib.util.spec_from_file_location('burst_charge_core',ROOT/'scripts/verify-portable-combat.py')
    core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    cases=json.loads((ROOT/'tests/fixtures/portable-burst-charge-speed.json').read_text())['cases']
    programs=[core.compile_case(c) for c in cases];bad,rejects=rejection_programs(cases,core.compile_case)
    captured=None;output=None;evidence={}
    if not args.native_only:
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        folder=ROOT/'research/portable-build'/('burst-charge-component-'+stamp);folder.mkdir(parents=True)
        packed=pack_programs(programs+bad);(folder/'input.bin').write_bytes(packed)
        raw,evidence=dispatch_programs(programs+bad,backend=args.backend)
        (folder/'readback.bin').write_bytes(raw)
        captured=dict(directory=str(folder),input_sha256=hashlib.sha256(packed).hexdigest(),raw_sha256=hashlib.sha256(raw).hexdigest(),evidence=evidence)
        (folder/'receipt.json').write_text(json.dumps(captured,indent=2)+'\n')
        output=array.array('I');output.frombytes(raw)
        if sys.byteorder!='little':output.byteswap()
        assert len(output)==(len(cases)+len(bad))*L['OUTPUT_WORDS']
    rows=[]
    for i,c in enumerate(cases):
        actual=None
        try:
            native=observe(c);core.contains(native['queries'],c['expected_queries'],c['name']+'.native')
            if output is not None:
                actual=decode(output[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],programs[i][1])
                assert actual['status']==0,actual['status']
                core.contains(actual['queries'],c['expected_queries'],c['name']+'.gpu')
                core.contains(actual,native,c['name']+'.native_gpu')
        except Exception as error:rows.append(dict(name=c['name'],passed=False,error=repr(error),actual=actual))
        else:rows.append(dict(name=c['name'],passed=True,native=native,actual=actual))
    statuses=[] if output is None else [output[(len(cases)+i)*L['OUTPUT_WORDS']] for i in range(len(bad))]
    passed=all(r['passed'] for r in rows) and (output is None or statuses==[r['status'] for r in rejects])
    paths=['app/portable_burst_charge_specs.py','scripts/portable_burst_charge_oracle.py','tests/fixtures/portable-burst-charge-speed.json','research/verify-burst-charge-speed.py']
    result=dict(passed=passed,cases=rows,captured=captured,rejected_cases=rejects,actual_rejection_statuses=statuses,cpu_trace_used_as_gpu_input=False,**evidence,
        validation_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    suffix='native' if args.native_only else args.backend
    (ROOT/f'research/portable-burst-charge-speed-{suffix}.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    assert passed,[(r['name'],r.get('error')) for r in rows if not r['passed']]
    print(len(rows),'burst charge cases passed',suffix)


if __name__=='__main__':main()
