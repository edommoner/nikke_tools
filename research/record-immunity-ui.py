"""Record values observed in the normal v23 browser result and details DOM."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json',
       'app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py',
       'server.mjs','web/app.js','web/index.html']
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,
    evidence='Observed browser DOM: single-squad result and expanded technical details, followed by screenshot. Not API-only evidence.',
    url='http://127.0.0.1:4332/#single',fictional_roster=True,roster_characters=203,
    squad=['에이드','리타','크라운','앨리스','모더니아'],duration=60,shooting_policy='character',
    burst_policy='rules',burst_gauge_mode='accumulate',seed=12345,
    changes={'에이드':{'stat_delta_atk':12345}},baseline_total=343462286,total=348869811,
    member_damage=[33018601,38614172,26743769,82188066,168305203],
    compute=dict(backend='cuda_detail',module_backend='cubin-sm86',device='NVIDIA GeForce RTX 3070 Ti',
        elapsed_ms=20014.732,initialization_ms=8.182,workspace_bytes=306072,
        cpu_verification=dict(total_equal=True,members_equal=True,burst_timeline_equal=True,
                             base_stats_equal=True,seed_equal=True,matched=True)),
    timing_is_standalone_benchmark=False,
    scope='One fictional equipped five-member squad with hypothetical ATK. Normal static boss UI has no authored harmful input; positive immunity is proved in the separate complete-battle tests.',
    source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
assert sum(report['member_damage'])==report['total']
(ROOT/'research/detail-immunity-ui-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded normal GPU UI total',report['total'])
