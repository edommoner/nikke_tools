"""Check the declared outgoing-healing extension independently of CUDA."""
import importlib.util,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker
from calculator.buff_manager import BuffManager
from calculator import timeline
from unittest.mock import patch
path=ROOT/'research/staging/v39/app/outgoing_healing_compat.py'
spec=importlib.util.spec_from_file_location('outgoing_reference',path);bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge);bridge.install()
rows=[]
for name,received,outgoing,source,expected in [('none',0,0,'source',1),('source-only',0,50,'source',1.5),('recipient-only',25,0,'source',1.25),('multiply-separate-layers',25,50,'source',1.875),('source-clamps-negative',50,-150,'source',0),('recipient-clamps-negative',-150,50,'source',0),('legacy-no-source',25,50,None,1.25)]:
    bm=object.__new__(BuffManager);calls=[]
    def live(who,stat,t):
        calls.append((who,stat,t));return received if stat=='heal_received_pct' else outgoing
    bm._live_sum=live;value=bm.heal_received_mult('recipient',.5,heal_source=source)
    expected_calls=[('recipient','heal_received_pct',.5)]+([('source','outgoing_heal_pct',.5)] if source else [])
    rows.append(dict(name=name,value=value,expected=expected,calls=calls,passed=value==expected and calls==expected_calls))
assert all(r['passed'] for r in rows)
# The bridge changes no pinned files and retains trace locations.
bridge.install()
assert getattr(BuffManager.heal_received_mult,'_nikke_outgoing_healing',False)
assert timeline.simulate.__code__.co_firstlineno==4547
cube=engine_worker.spec.CUBES['렐릭 힐링 큐브'];assert cube['stat']=='outgoing_heal_pct' and not cube.get('unsupported')
files=['research/probe-outgoing-healing-cpu-reference.py','research/staging/v39/app/outgoing_healing_compat.py','app/engine_worker.py','app/engine_compat.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/runner/spec.py','research/upstream/nikke-calc-master/data/base_stat_tables/cube.json']
if (ROOT/'app/outgoing_healing_compat.py').exists():
    assert (ROOT/'app/outgoing_healing_compat.py').read_bytes()==path.read_bytes()
    files.append('app/outgoing_healing_compat.py')
result=dict(passed=True,cpu_extension=True,unmodified_upstream_implements_effect=False,in_game_rules_verified=False,gpu_verified=False,objective_complete=False,cases=rows,cube_supported=True,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-outgoing-healing-cpu-reference.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('CPU outgoing model: 7 independent arithmetic/source tests passed; healing cube enabled; GPU unverified.')
