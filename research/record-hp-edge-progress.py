"""Durable v35 port state; accepted v34 remains the ordinary application."""
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'research/detail-expansion-next.json';j=json.loads(p.read_text(encoding='utf-8'))
j.update(generated_at=datetime.now(timezone.utc).isoformat(),objective_complete=False)
j['current_work']=dict(phase='v35 installed after native/PTX HP39 and boundary5; production95/API/browser acceptance running',stage='research/staging/v35',abi='detail_hp_edge_v35',
    previous_turn_classification='progress: v34 normal87/API/browser acceptance, checkpoint and immutable production archive completed',
    initial_eight_native_frame_damage_cases_passed=True,initial_archive='research/ports/v35-initial-no-notification-log',
    authored_cases=24,namespace_cases=3,real_skill_squad_cases=12,both_backend_39_case_suites_passed=True,
    staged_archive='research/ports/v35-hp-edge-staged-verified',rejected_namespace_archive='research/ports/v35-before-self-event-namespace-fix',
    workspace_bytes_per_squad=1074184,
    compiler_coverage=dict(accepted=150,catalog=203,newly_compiled=['A2'],favorite_contexts=589,total_favorite_contexts=812,compilation_is_not_battle_parity=True),
    live_handles=dict(normal95=69993,ordinary_api_completed=59590,preview_v35=17274),
    ordinary_API_and_browser_passed=True,ordinary_total=194933444,ordinary_original_total=197889526,ordinary_delta=-2956082,
    CPU_only_next_dependencies=dict(lost_hp_scaling_cases=8,cover_revival_cases=9),
    pending=['Freeze app files, tests and scripts/verify*.py until normal95 completes. Poll session69993; log research/detail-hp-edge-normal-tests.log. Never restart just because observation timed out.',
      'Ordinary API session59590 ended0; report research/detail-hp-edge-api-verification.json passed. First API assertion assumed total damage must increase; corrected to exact base-stat edits plus independent CPU parity. The actual delta is negative on both engines, not a GPU mismatch. Original failing script/log preserved in research/ports/v35-api-monotonicity-assumption.',
      'Task preview port4332 restarted as session17274, leaving4317 unchanged. Browser restored research/detail-hp-edge-ui-fixture.json and verified GPU+CPU and pure GPU totals. Current previewTab tab16/browser2 is results with CPU badge, marked Deliverable and full-page screenshot emitted. Browser proof research/detail-hp-edge-browser-verification.json passed.',
      'Normal95 must finish passed with zero skipped, then run research/finalize-hp-edge-docs.py, research/save-hp-edge-checkpoint.py, research/archive-hp-edge-v35.py sequentially. These are prepared but NOT run yet; guard on normal95. Do not rerun immutable stage promotion.',
      'All-character/effect goal remains incomplete. CPU-only references now ready: research/detail-lost-hp-cpu-reference.json eight cases, research/detail-cover-revival-cpu-reference.json nine cases. Do not claim their GPU implementation.'])
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded live v35 stage, existing evidence and remaining promotion gates.')
