"""Whole-squad v41 parity, GPU first, CPU independently observed afterward."""
import argparse,hashlib,importlib.util,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
d=load('sharing_definitions','research/heal-sharing-fixtures.py');g=d.g;v=d.v
def fixtures(group):
    if group=='new':return [(v,*x) for x in [*d.fixtures(),*d.real_fixtures()]]
    storage=load('sharing_storage_oracle','scripts/verify-healing-storage.py')
    extra=load('sharing_storage_extra','scripts/healing-storage-extra-fixtures.py')
    old=load('sharing_prior_oracles','scripts/verify-healing-storage-regressions.py')
    cases=[(storage,*x) for x in storage.d.fixtures()]+[(storage,*x) for x in extra.fixtures()]+old.fixtures()
    assert len(cases)==153;return cases
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);ap.add_argument('--group',choices=['new','legacy'],default='new');ap.add_argument('--output',required=True);ap.add_argument('--resume',action='store_true');args=ap.parse_args()
    planned=fixtures(args.group)
    paths=list((ROOT/'scripts').glob('*.py'))+list((ROOT/'app').glob('*.py'))
    paths += [ROOT/p for p in ['research/verify-heal-sharing.py','research/heal-sharing-fixtures.py','research/staging/v41/app/heal_sharing_compat.py','research/staging/v41/app/detail_gpu.py','research/staging/v41/app/detail_effects.cu','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json','research/upstream/nikke-calc-master/data/parsed_nikke.json','research/upstream/nikke-calc-master/runner/spec.py']]
    paths += [ROOT/'research/staging/v41/app'/n for n in (['detail_effects.ptx','detail_effects-build.json'] if args.backend=='ptx' else ['detail_effects-sm86.cubin','detail_effects-sm86.json'])]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hashes={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(paths))}
    output=ROOT/args.output;rows=[]
    if args.resume and output.exists():
        previous=json.loads(output.read_text(encoding='utf-8'));assert previous['source_sha256']==hashes,'Source changed; refuse stale resume'
        rows=[r for r in previous['cases'] if r['passed']]
    done={r['name'] for r in rows};device=v.s.v.v.v.Cuda()
    def save():
        assert hashes=={p:sha(ROOT/p) for p in hashes}
        report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(r['passed'] for r in rows),abi=g.DETAIL_ABI,backend=args.backend,group=args.group,stage_only=True,objective_complete=False,cpu_model_extended=True,in_game_rules_verified=False,cpu_trace_used_as_gpu_input=False,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,source_sha256=hashes)
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return report['passed']
    try:
        for oracle,name,b,x in planned:
            if name in done:continue
            try:row=oracle.compare(device,name,b,x,args.backend)
            except Exception as e:row=dict(name=name,passed=False,error=repr(e));print(json.dumps(row),flush=True)
            rows.append(row);save()
            if not row['passed']:break
    finally:device.close()
    raise SystemExit(0 if save() else 1)
