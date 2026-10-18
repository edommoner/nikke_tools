"""Observed normal browser result, expanded compute details and core input."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json',
       'app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/engine_worker.py','app/gpu_service.py',
       'server.mjs','web/app.js','web/index.html']
observed_source={
    "app/detail_gpu.py": "14f675bc15062bcdffd149d93fb9ff1dd9b86e969aa5aec9a2afe43b71430320",
    "app/detail_effects.cu": "43ce35f827f0e2fee00e79685e1cdcb06d001be0110cc3d616373c437bcf9882",
    "app/detail_effects.ptx": "20f5839e5f324526267529e45a739726380d1d35c984b5e269697c56ba46ab40",
    "app/detail_effects-build.json": "60ac4e7056e6da8ecf09b966707abfeaf5c43921089d3c9d46ae361addaa1fa4",
    "app/detail_effects-sm86.cubin": "84e9945150e4ecf00bacb2222232732df4f8ab38ad0ecd7cd2f36a81e49178dd",
    "app/detail_effects-sm86.json": "1cade57490af20d2740c73fe14451c492aafe39a051c295aaf861e59017a6a11",
    "app/engine_worker.py": "a1b9f46f5c5375f6da7740b37ebc3e8a286fe95973cc19594d7d625a805bb75c",
    "app/gpu_service.py": "7cc9e2b0f87c633bd09092347207dfa7fbb5773fb399cfeadc6b70aff7a2309d",
    "server.mjs": "1a4893b15953a714ce8a095ac9777eb13d38302237933f4d428dcd2a8cc64578",
    "web/app.js": "91847d22a3ffb5238975aadf7e9af8c664db5650b7b85093668ed833041a5389",
    "web/index.html": "8fb146ea8a433f0028f2a6365ab849e851068311e73787ede33e5ca7152f5b99"
}
for f,digest in observed_source.items():
    assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==digest,'UI observation is historical; repeat browser verification: '+f
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,
    evidence='Browser DOM result and expanded technical details; core input reopened and observed as50; screenshot captured.',
    url='http://127.0.0.1:4332/#single',fictional_roster=True,roster_characters=203,
    squad=['리버렐리오','리타','크라운','앨리스','모더니아'],duration=60,shooting_policy='character',
    burst_policy='rules',burst_gauge_mode='accumulate',seed=12345,core_px=50,
    changes={'리버렐리오':{'stat_delta_atk':12345}},baseline_total=871655538,total=893298342,
    member_damage=[240966515,52519939,90241547,165823550,343746791],
    compute=dict(backend='cuda_detail',module_backend='cubin-sm86',device='NVIDIA GeForce RTX 3070 Ti',
        elapsed_ms=8914.05,initialization_ms=7.638,workspace_bytes=306072,
        cpu_verification=dict(total_equal=True,members_equal=True,burst_timeline_equal=True,
                             base_stats_equal=True,seed_equal=True,matched=True)),
    timing_is_standalone_benchmark=False,
    scope='One fictional equipped Liberalio five-member squad with hypothetical ATK and static enabled core. Positive/negative speed immunity and core boundaries are separately exercised in the battle verifier.',
    source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
assert sum(report['member_damage'])==report['total']
(ROOT/'research/detail-charge-immunity-ui-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded normal GPU UI total',report['total'])
