"""Audit the existing generation-aware CPU mutation lifecycle for next admission."""
import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/d) for d in ('app','scripts','tests')]
from enemy_mutation_cases import exercise
result=exercise();assert result['passed'] and len(result['observations'])==22
result.update(scope='Existing native CPU mutation/cleanse/extend reference only; not new GPU operator admission',cpu_trace_used_as_gpu_input=False,
 semantics=dict(targets='resolve_enemy_mutation uses explicit current-target context when available',membership='enemy_mutation_targets intersects canonical labels then generation/alive visibility',immunity='presence in active target list plus enemy_field_visible; runtime predicates/expiry are not re-evaluated'),
 source_sha256={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in ['app/enemy_recipient_runtime.py','app/enemy_recipient_specs.py','scripts/enemy_mutation_cases.py','scripts/enemy_recipient_cases.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']})
(R/'research/portable-stack-enemy-contract.json').write_text(json.dumps(result,indent=2)+'\n');print('Native enemy mutation lifecycle:',len(result['observations']),'observations passed')
