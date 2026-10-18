"""Ten charge lifecycle collisions with independent per-frame GPU readbacks."""
import argparse,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=load('charge_oracle','scripts/verify-heal-charge.py');extra=load('charge_extra','scripts/heal-charge-extra-fixtures.py')
def compare(device,name,b,x,backend):
    captured={};original=m.g.evaluate_full
    def observe(*a,**kw):
        result=original(*a,**kw);captured.update(result);return result
    with patch.object(m.g,'evaluate_full',observe):row=m.compare(device,name,b,x,backend)
    if name=='charge-extra-release-inside-HP-edge':
        # This pool fills and discharges synchronously, so no positive
        # quantity survives to the end-of-frame query. Only discharge heals
        # slot1 here; compare its HP gain to the independent input-ATK cap.
        actor=b['squad'][0];frames=captured['_incoming_frames'];before=frames[0]['state'][actor]['hp'];gain=max(f['state'][actor]['hp'] for f in frames)-before
        expected=min(captured['base_stats'][actor]['atk']*1.5,captured['compute']['final_hp'][actor]['max_hp']-before)
        row['checks']['positive_charge_control']=expected>0 and m.v.s.v.close(gain,expected)
        row['GPU_immediate_release_HP_gain']=gain;row['independent_ATK_cap_expected_HP_gain']=expected
        row['positive_control_scope']='Nonzero same-frame discharge via recipient HP gain; no positive pool quantity remains at frame end.'
        row['passed']=all(row['checks'].values())
        print(json.dumps(dict(name=name,passed=row['passed'],immediate_release_HP_gain=gain,independent_expected=expected)),flush=True)
    return row
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
    paths=list((ROOT/'scripts').glob('*.py'))+list((ROOT/'app').glob('*.py'))
    paths += [ROOT/p for p in ['scripts/verify-heal-charge-extra.py','scripts/verify-heal-charge.py','scripts/heal-charge-fixtures.py','scripts/heal-charge-extra-fixtures.py','app/heal_charge_compat.py','app/detail_gpu.py','app/detail_effects.cu','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/data/parsed_skills.json','research/upstream/nikke-calc-master/data/parsed_nikke.json','research/upstream/nikke-calc-master/runner/spec.py']]
    paths += [ROOT/'app'/n for n in (['detail_effects.ptx','detail_effects-build.json'] if args.backend=='ptx' else ['detail_effects-sm86.cubin','detail_effects-sm86.json'])]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hashes={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(paths))}
    planned=list(extra.fixtures(m.d));assert len(planned)==10;rows=[];device=m.v.s.v.v.v.Cuda()
    def save():
        assert hashes=={p:sha(ROOT/p) for p in hashes}
        r=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(r['passed'] for r in rows),abi=m.g.DETAIL_ABI,backend=args.backend,group='extra',stage_only=False,objective_complete=False,cpu_model_extended=True,in_game_rules_verified=False,cpu_trace_used_as_gpu_input=False,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,actual_workspace_bytes_per_squad=sorted({r['workspace_bytes'] for r in rows if 'workspace_bytes' in r}),source_sha256=hashes)
        (ROOT/args.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return r['passed']
    try:
        for name,b,x in planned:
            try:row=compare(device,name,b,x,args.backend)
            except Exception as e:row=dict(name=name,passed=False,error=repr(e));print(json.dumps(row),flush=True)
            rows.append(row);save()
            if not row['passed']:break
    finally:device.close()
    raise SystemExit(0 if save() else 1)
