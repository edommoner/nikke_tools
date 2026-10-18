"""Inspect actual HP-edge definitions and compile their complete skill sets."""
import importlib.util,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('hp_real',ROOT/'scripts/verify-staged-hp-edge.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
raw_path=ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json';raw=json.loads(raw_path.read_text(encoding='utf-8'));rows=[]
for character,effects in raw.items():
    if not isinstance(effects,list):continue
    selected=[e for e in effects if any(t.startswith(('hp_below:','hp_below_count:','event:ally_hp_below:','event:adjacent_hp_')) for t in e.get('trigger',{}).get('timing',[]))]
    if not selected:continue
    names=[v.N[0],v.N[1],character]+[n for n in v.N[2:] if n!=character][:2]
    names=list(dict.fromkeys(names))
    if len(names)!=5:names+=[n for n in v.N if n not in names][:5-len(names)]
    b=v.s.v.body(30,True,names)
    for stage in range(4):
        b['profile']['chars'][character]['favorite_stage']=stage
        try:v.s.v.v.a.evaluate({**b,'_compile_gpu_detail':True});r=dict(character=character,favorite_stage=stage,compiled=True)
        except Exception as exc:r=dict(character=character,favorite_stage=stage,compiled=False,issues=getattr(exc,'issues',str(exc)))
        rows.append(r);print(json.dumps(r,ensure_ascii=True),flush=True)
    if character=='A2':print(json.dumps(dict(character=character,all_actual_definitions=effects),ensure_ascii=True),flush=True)
r=dict(stage_only=True,gpu_battle_verified=False,objective_complete=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('research/probe-hp-edge-real-characters.py','scripts/verify-staged-hp-edge.py','research/staging/v35/app/detail_gpu.py','research/upstream/nikke-calc-master/data/parsed_skills.json')})
(ROOT/'research/detail-hp-edge-real-character-compile.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
