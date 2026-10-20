"""Retained diagnostic of native skill snapshots and active mode gauge basis."""
import argparse
import array
import datetime
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts'),str(ROOT/'research')]
from portable_runtime import dispatch_programs,pack_programs,decode
from portable_specs import LIMITS as L
spec=importlib.util.spec_from_file_location('skill_study',ROOT/'research/characterize-burst-charge-skills.py')
study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
spec=importlib.util.spec_from_file_location('combat_core',ROOT/'scripts/verify-portable-combat.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--candidate',action='store_true');args=parser.parse_args()
    if not args.candidate:
        if (ROOT/'research/portable-burst-charge-skill-diagnostic.json').exists():
            raise SystemExit('Original failed diagnostic is retained; refusing to rerun or overwrite it')
        assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='85b8b190ec9d9fa8ebd66058947bccfcda72e489'
        subprocess.run(['git','diff','--exit-code','85b8b19','--','gpu'],cwd=ROOT,check=True)
    if args.candidate:
        import portable_runtime as runtime
        original=runtime.execute
        def execute(source,*rest,**kwargs):
            assert source=='gpu/event_runtime.slang'
            return original('research/portable-build/burst-charge-mode-fix-candidate/burst_charge_mode_fix_runtime.slang',*rest,**kwargs)
        runtime.execute=execute
    cases=[]
    for owner in range(5):
        for scenario,expected in [('initial',10.75),('named-activation',10),('named-removal',8.75),('mode-skill',28),
                                  ('mode-remove',28),('mode-limit',19),('mode-switch',28),('base-enter-mode',16)]:
            effects=study.fixtures(owner,scenario)
            weapons=[dict(enabled=False) for _ in range(5)]
            weapons[owner]=dict(enabled=True,base_weapon_type='AR',mode='auto',coefficient=100,capacity=100,interval=1,gauge=2)
            cases.append(dict(name=f'burst-skill-{owner}-'+scenario,effects=effects,owners=[owner]*len(effects),
                environment=dict(burst_references=[dict(burst_energy=2,burst_energy_raw=.25) for _ in range(5)]),
                combat=dict(weapons=weapons,targets=[dict(hp=1000000,defense=0)]),
                script=[[0,24,0,0,0,-1,0,0],[0,2,0,0,-1,0,0,0]],expected=expected))
    programs=[core.compile_case(c) for c in cases]
    folder=ROOT/'research/portable-build'/('burst-skill-diagnostic-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
    packed=pack_programs(programs);(folder/'input.bin').write_bytes(packed)
    raw,evidence=dispatch_programs(programs,backend='metal');(folder/'readback.bin').write_bytes(raw)
    (folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    output=array.array('I');output.frombytes(raw)
    rows=[]
    for i,c in enumerate(cases):
        actual=decode(output[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],programs[i][1])
        rows.append(dict(name=c['name'],passed=actual['status']==0 and actual['queries'][0]['combat']['gauge']==c['expected'],expected_gauge=c['expected'],actual=actual))
    report=dict(passed=all(r['passed'] for r in rows),cases=rows,inputs=cases,captured=str(folder),evidence=evidence,
        input_sha256=hashlib.sha256(packed).hexdigest(),output_sha256=hashlib.sha256(raw).hexdigest(),gpu_retry=False,
        native_study='research/portable-burst-charge-skills-native.json',scope='Diagnostic only; not global validation')
    suffix='candidate' if args.candidate else 'diagnostic'
    (ROOT/f'research/portable-burst-charge-skill-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print([(r['name'],r['passed'],r['expected_gauge'],r['actual']['queries'][0]['combat']['gauge']) for r in rows])
    assert report['passed'],'Skill gauge discrepancy retained with complete input/readback'


if __name__=='__main__':main()
