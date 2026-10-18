"""Compile-only coverage and HP-event definitions for the v35 port."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hp_loader',ROOT/'scripts/staged-hp-edge-runtime.py');loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader);loader.install()
sys.path.insert(0,str(ROOT/'scripts'))
from detail_coverage import coverage
r=coverage();previous=json.loads((ROOT/'research/detail-survival-coverage.json').read_text(encoding='utf-8'))
old={x['character'] for x in previous['results'] if x['supported']}
raw_path=ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json';raw=json.loads(raw_path.read_text(encoding='utf-8'))
events={n:[dict(name=e.get('name'),timings=e['trigger']['timing'],stat=e.get('stat'),favorite=e.get('favorite')) for e in effects if isinstance(e,dict) and any(t.startswith(('hp_below:','hp_below_count:','event:ally_hp_below:','event:adjacent_hp_')) for t in e.get('trigger',{}).get('timing',[]))] for n,effects in raw.items() if isinstance(effects,list)}
events={n:e for n,e in events.items() if e}
r.update(stage_only=True,gpu_battle_verified=False,objective_complete=False,newly_compiled=[x['character'] for x in r['results'] if x['supported'] and x['character'] not in old],hp_event_definitions=events,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('research/staging/v35/app/detail_gpu.py','app/survival_compat.py','scripts/staged-hp-edge-runtime.py','scripts/detail_coverage.py','research/audit-staged-hp-edge.py','research/upstream/nikke-calc-master/data/parsed_skills.json')})
(ROOT/'research/detail-hp-edge-staged-coverage.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(compiled=r['supported'],catalog=r['characters'],newly_compiled=r['newly_compiled'],hp_event_characters=list(events),gpu_battle_verified=False),ensure_ascii=True))
