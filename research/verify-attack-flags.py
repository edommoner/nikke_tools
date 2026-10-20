"""One shared component driver, retaining all input/readback bytes before checks."""
import argparse
import array
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'app'),str(ROOT/'scripts')]
from portable_runtime import dispatch_programs, pack_programs, decode
from portable_specs import LIMITS as L
from portable_attack_flag_oracle import observe, compare
from portable_attack_flag_validation import rejection_programs


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--backend',choices=['metal','cuda'],default='metal')
    parser.add_argument('--native-only',action='store_true')
    args=parser.parse_args()
    spec=importlib.util.spec_from_file_location('attack_flag_core',ROOT/'scripts/verify-portable-combat.py')
    core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    cases=json.loads((ROOT/'tests/fixtures/portable-attack-flags.json').read_text())['cases']
    programs=[core.compile_case(c) for c in cases]
    bad, rejects=rejection_programs(cases,core.compile_case)
    evidence={};captured=None;output=None
    if not args.native_only:
        raw,evidence=dispatch_programs(programs+bad,backend=args.backend)
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        folder=ROOT/'research/portable-build'/('attack-flag-component-'+stamp);folder.mkdir(parents=True)
        (folder/'readback.bin').write_bytes(raw)
        (folder/'input.bin').write_bytes(pack_programs(programs+bad))
        captured=dict(directory=str(folder),evidence=evidence)
        (folder/'receipt.json').write_text(json.dumps(captured,indent=2)+'\n')
        output=array.array('I');output.frombytes(raw)
        if sys.byteorder!='little':output.byteswap()
        assert len(output)==(len(programs)+len(bad))*L['OUTPUT_WORDS']
    rows=[]
    for i,c in enumerate(cases):
        actual=None
        try:
            if output is None:
                native=observe(c);core.contains(native['queries'],c['expected_queries'],c['name'])
            else:
                actual=decode(output[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],programs[i][1])
                assert actual['status']==0,actual['status']
                native=compare(c,actual,core.contains)
        except AssertionError as error:
            rows.append(dict(name=c['name'],passed=False,error=str(error),actual=actual))
        else:rows.append(dict(name=c['name'],passed=True,native=native))
    statuses=[] if output is None else [output[(len(cases)+i)*L['OUTPUT_WORDS']] for i in range(len(bad))]
    passed=all(r['passed'] for r in rows) and (output is None or statuses==[r['status'] for r in rejects])
    paths=['app/portable_damage_specs.py','app/portable_runtime.py','app/portable_specs.py',
           'scripts/portable_attack_flag_oracle.py','scripts/portable_attack_flag_validation.py',
           'tests/fixtures/portable-attack-flags.json','research/verify-attack-flags.py','scripts/portable_weapon_oracle.py','scripts/portable_enemy_oracle.py']
    result=dict(passed=passed,cases=rows,rejected_cases=rejects,actual_rejection_statuses=statuses,raw_rejections_verified=output is not None,
                captured=captured,cpu_trace_used_as_gpu_input=False,**evidence,
                validation_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    suffix='native' if args.native_only else args.backend
    (ROOT/f'research/portable-attack-flags-{suffix}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    assert passed,[(r['name'],r.get('error')) for r in rows if not r['passed']]
    print(len(rows),'attack flag cases passed',suffix,';raw rejection cases',len(rejects),'verified' if output is not None else 'constructed only')


if __name__=='__main__':main()
