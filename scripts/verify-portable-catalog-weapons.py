"""Execute all catalog weapons without character effects; never full-character proof.
Static real metadata is packed before GPU dispatch. CPU observations are evaluated
only after readback and are never used as a shot schedule or GPU state input.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker as adapter
from detail_coverage import body_for
from portable_weapon_oracle import observe
from portable_runtime import run_programs
import importlib.util
spec=importlib.util.spec_from_file_location('combat_verifier',ROOT/'scripts/verify-portable-combat.py')
verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('metal','cuda'),default='metal')
    args=parser.parse_args()
    path=ROOT/f'research/portable-catalog-weapons-{args.backend}.json'
    path.write_text(json.dumps(dict(passed=False,gpu_execution_verified=False,stage='preparing'))+'\n')
    names=[n for n,d in adapter.META.items() if isinstance(d,dict) and not n.startswith(('_','test_')) and not adapter.spec.is_preview(n)]
    # Track both common code and the pinned engine's static metadata/reference.
    tracked=[p for folder in ('app','scripts') for p in (ROOT/folder).glob('*.py')]
    tracked += [p for folder in ('calculator','runner','data') for p in (ROOT/'research/upstream/nikke-calc-master'/folder).rglob('*') if p.suffix in ('.py','.json')]
    tracked += [ROOT/'data/engine-effect-overrides.json']
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(tracked))}
    cases=[]
    for name in names:
        squad=[name]+[n for n in ('모더니아','루주','마스트 : 로망틱 메이드','도라','얀') if n!=name][:4]
        audit=adapter.evaluate({**body_for(squad),'_audit_portable':True})
        assert audit['weapon_input_preflight_passed'],(name,audit['weapon_adapter_issue'])
        w=audit['normalized_weapon']
        # Only the weapon is under test. No character effect or burst is implied.
        w['stage']=0;w['gauge']=0
        cases.append(dict(name=name,combat=dict(weapons=[w]+[dict(enabled=False) for _ in range(4)],targets=[dict(hp=1e12)],trace='summary'),
                          effects=[dict(name='no critical',source='스킬1',type='buff',stat='crit_rate',fixed_value=-15,target='self',duration=-1,trigger=dict(timing=['battle_start'],condition=[]))],
                          script=[[3,24,0,0,0,-1,0,0],[3,2,0,0,-1,0,0,0]]))
    result=run_programs([verifier.compile_case(c) for c in cases],backend=args.backend)
    result.update(passed=False,stage='readback-before-CPU-reference',catalog_characters=len(names),full_character_verified=0,
                  character_effects_included=False,normal_ui_connected=False,cpu_trace_used_as_gpu_input=False,validation_sha256=hashes)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    rows=[]
    for c,gpu in zip(cases,result['results']):
        queries,_=observe(c)
        actual=gpu['queries'][0]
        cpu=queries[0]
        verifier.contains(actual,dict(damage=cpu['damage'],combat=dict(weapons=[{k:cpu['combat']['weapons'][0][k] for k in ('ammo','shots')}])) ,c['name'])
        rows.append(dict(character=c['name'],passed=True,normalized_weapon=c['combat']['weapons'][0],cpu_query=cpu))
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in hashes}
    result.update(passed=True,stage='verified',cases=rows,scope='All real static weapon metadata for three seconds; character effects, controls, burst, enemy world and full battles excluded')
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(passed=True,weapon_cases=len(rows),device=result['transport']['device'],full_character_verified=0)))


if __name__=='__main__':main()
