"""Candidate Metal check for authored fractional and explicit-zero references."""
import array
import datetime
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_backend import execute
from portable_runtime import pack_programs,decode
from portable_specs import LIMITS as L
from portable_burst_charge_oracle import observe


def main():
    spec=importlib.util.spec_from_file_location('fractional_core',ROOT/'scripts/verify-portable-combat.py')
    core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    cases=json.loads((ROOT/'research/portable-burst-charge-fractional-candidate-inputs.json').read_text())['cases']
    programs=[core.compile_case(c) for c in cases];packed=pack_programs(programs)
    folder=ROOT/'research/portable-build'/('burst-fractional-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
    (folder/'input.bin').write_bytes(packed)
    raw,evidence=execute('research/portable-build/burst-charge-mode-fix-candidate/burst_charge_mode_fix_runtime.slang','portableEvents',packed,L['INPUT_WORDS'],L['OUTPUT_WORDS'],'metal')
    (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    words=array.array('I');words.frombytes(raw);rows=[]
    for i,c in enumerate(cases):
        native=observe(c);actual=decode(words[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],programs[i][1])
        try:
            assert actual['status']==0
            core.contains(native['queries'],c['expected_queries'],c['name']+'.native')
            core.contains(actual,native,c['name']+'.gpu')
        except AssertionError as error:rows.append(dict(name=c['name'],passed=False,error=repr(error),native=native,actual=actual))
        else:rows.append(dict(name=c['name'],passed=True,native=native,actual=actual))
    report=dict(passed=all(c['passed'] for c in rows),cases=rows,captured=str(folder),evidence=evidence,
        scope='Isolated candidate numerical component, not global validation or performance measurement')
    (ROOT/'research/portable-burst-charge-fractional-metal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    assert report['passed'],[(c['name'],c.get('error')) for c in rows if not c['passed']]
    print(len(rows),'fractional/zero references passed Metal and native')


if __name__=='__main__':main()
