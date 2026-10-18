"""Record values observed through the browser DOM after the v22 UI run."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json',
       'app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py',
       'server.mjs','web/app.js','web/index.html']
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,
    evidence='Observed browser DOM: normal single-squad result and expanded technical details; not API-only evidence.',
    url='http://127.0.0.1:4332/#single',fictional_roster=True,roster_characters=203,
    squad=['센티','리타','크라운','앨리스','모더니아'],duration=35,shooting_policy='character',
    burst_policy='rules',burst_gauge_mode='accumulate',seed=12345,
    changes={'센티':{'favorite_stage':0,'stat_delta_atk':12345}},
    original_favorite_stage=3,original_used_cpu_fallback=True,
    fallback_reason='heal_overcharge_store remains unsupported; original fictional Centi favorite stage 3 preserved.',
    baseline_total=189367813,total=169430697,member_damage=[10722108,20137118,15139616,39093031,84338824],
    compute=dict(backend='cuda_detail',module_backend='cubin-sm86',device='NVIDIA GeForce RTX 3070 Ti',
        elapsed_ms=5277.71,initialization_ms=22.519,workspace_bytes=299928,
        cpu_verification=dict(total_equal=True,members_equal=True,burst_timeline_equal=True,
                             base_stats_equal=True,seed_equal=True,matched=True)),
    scope='One fictional equipped five-member squad, charge weapons and real gauge. Favorite 3 baseline fell back; changed favorite 0 result ran on GPU. Not every character or effect.',
    source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
assert sum(report['member_damage'])==report['total']
(ROOT/'research/detail-shields-ui-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded normal GPU UI total',report['total'])
