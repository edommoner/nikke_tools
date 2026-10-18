import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('incoming_api',ROOT/'scripts/verify-incoming-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
b=v.body(20,True)
b.update(compute_backend='cuda_detail',verify_detail=True,patches={},stat_deltas={v.NAMES[3]:{'atk':12000,'hp':100000,'def':250}})
b['enemy']['patterns']=[dict(id='incoming',kind='attack',delay=.1,until={'time':20},spec=dict(coeff=100,atk=100000,target='random:2',hits=16,interval=.5)),v.v.buff('armor',at=.3,duration=2,enemy={'def_mult':1.3,'received_dmg_pct':-20}),dict(id='core',kind='core',delay=2,until={'time':3},core_px=6)]
for k in list(b):
 if k.startswith('_debug'):b.pop(k)
(ROOT/'research/detail-incoming-api-fixture.json').write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
source=(ROOT/'scripts/smoke-detail-boss-buffs.mjs').read_text(encoding='utf-8').replace('smoke-detail-boss-buffs.mjs','smoke-detail-incoming.mjs').replace('detail-boss-buffs-api-verification.json','detail-incoming-api-verification.json')
needle="assert.equal(row.result.compute.cpu_verification.matched,true);"
assert needle in source
source=source.replace(needle,needle+"assert.equal(row.result.compute.cpu_verification.incoming_hits_equal,true);assert.ok(row.result.incoming_hits.length>0);")
source=source.replace("report.boss_timeline=g.results[1].result.boss_timeline;","report.incoming_hits=g.results[1].result.incoming_hits;report.incoming_hits_verified=true;report.boss_timeline=g.results[1].result.boss_timeline;")
(ROOT/'scripts/smoke-detail-incoming.mjs').write_text(source,encoding='utf-8')
print('Prepared fictional owned profile and incoming-combat API smoke; not executed yet.')
