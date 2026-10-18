import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
proof=[]
for f in ['research/detail-boss-buffs-rng-30.json','research/detail-boss-buffs-rng-30-full-end-damage.json']:
 r=json.loads((ROOT/f).read_text(encoding='utf-8'));assert r['first_difference'] is None and r['cpu_total']==r['gpu_total'];proof.append({'path':f,'cpu_total':r['cpu_total'],'gpu_total':r['gpu_total'],'all_frame_rng_indices_match':True})
p=ROOT/'research/detail-expansion-next.json';r=json.loads(p.read_text(encoding='utf-8'));w=r['current_work']
w.update(status='verifying_phase_cache_fixes',phase_cache_30_second_proof=proof,active_verifications={'normal_77_session':8504,'normal_log':'research/detail-boss-buffs-phase-final-normal-tests.log','long_boundary_api_session':22336,'tail_log':'research/detail-boss-buffs-phase-final-tail.log'},next_action='Poll sessions 8504 and 22336. Keep at most two heavy GPU processes. Once tail session 22336 succeeds, run scripts/verify-boss-buffs-detail.py --backend both for fresh 40 native/PTX cases. Inspect all logs/reports and require 6 long cases, 2 boundary cases, API success and 77 tests before saving v32 checkpoint. On any failure, retain that case and repair it. Full all-character/effect goal remains active.')
w.pop('verification_sequence',None)
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
