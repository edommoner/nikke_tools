"""Fictional owned Moran squad for ordinary API and browser acceptance."""
import copy,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('scaling_ui_fixture',ROOT/'research/verify-survival-scaling-real.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
_,b,extra=next(x for x in m.fixtures() if x[0]=='raw-목단-incoming-owned-growth')
# The stress oracle adds controlled undying support. Ordinary UI keeps all raw
# character skills and uses a survivable incoming attack without that injection.
b['enemy']['patterns'][0]['spec'].update(atk=40000,hits=10,interval=1)
b={k:v for k,v in b.items() if not k.startswith('_debug')};b.update(compute_backend='cuda_detail',verify_detail=True)
session=json.loads((ROOT/'research/detail-hp-edge-ui-fixture.json').read_text(encoding='utf-8'))
session.update(saved_at=datetime.now(timezone.utc).isoformat(),profile=b['profile'],patches={},deltas=b['stat_deltas'],squad=b['squad'],teams=[b['squad']]+[['']*5 for _ in range(4)],enemyPatterns=b['enemy']['patterns'],enemyParts=[])
session['snapshot'].update(profile=copy.deepcopy(b['profile']),squad=b['squad'],is_demo=True,warnings=['モランの残HP参照をGPU検証する架空の所持・装備データです。'])
settings={'enemy-def':b['enemy']['def'],'enemy-code':b['enemy']['code'],'duration':b['duration'],'level':b['level'],'core':b['enemy']['core_px'],'distance':b['enemy']['distance']}
session['settings']={**settings,'detail-backend':'cuda_verified','shooting-policy':b['shooting_policy'],'burst-policy':b['burst_policy'],'burst-gauge-mode':b['burst_gauge_mode'],'random-seed':b['seed']}
preset=copy.deepcopy(session['customPresets'][0]);preset.update(id='user:gpu-survival-scaling',label='GPU検証：モランの残HP参照',settings=settings,patterns=b['enemy']['patterns'],parts=[])
session['customPresets']=[preset];session['enemyContexts']={'single':dict(settings=settings,parts=[],patterns=b['enemy']['patterns'],presetId=preset['id'])}
for path,data in [('research/detail-survival-scaling-api-fixture.json',b),('research/detail-survival-scaling-ui-fixture.json',session)]:
    (ROOT/path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
text=(ROOT/'scripts/smoke-detail-hp-edge.mjs').read_text(encoding='utf-8').replace('hp-edge','survival-scaling').replace('detail_hp_edge_v35','detail_survival_scaling_v36')
text=text.replace('Ordinary application requests for actual A2 HP drain and mode removal.','Ordinary Moran owned-growth requests with raw skills and survivable incoming damage.')
text=text.replace("'app/survival_compat.py',","'app/survival_compat.py','app/survival_scaling_compat.py',")
text=text.replace("  assert.ok(result.compute.final_hp.A2.hp_pct>0&&result.compute.final_hp.A2.hp_pct<40);","  assert.ok(result.compute.final_hp['목단'].hp_pct>0&&result.compute.final_hp['목단'].hp_pct<=100);")
text=text.replace('evaluation.stat_deltas.A2',"evaluation.stat_deltas['목단']").replace('.base_stats.A2[stat]',".base_stats['목단'][stat]")
(ROOT/'scripts/smoke-detail-survival-scaling.mjs').write_text(text,encoding='utf-8')
print('Prepared ordinary Moran owned-growth fixture; no production acceptance claim.')
