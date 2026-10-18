"""Independent overlapping receiver observations, shared CPU semantics stage."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from enemy_fanout_cases import exercise
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve()]+[ROOT/p for p in ('scripts/enemy_fanout_cases.py','scripts/enemy_recipient_cases.py','tests/test_target_counter_runtime.py','tests/test_enemy_recipient_runtime.py','data/engine-effect-overrides.json')]
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
case=exercise();assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report=dict(passed=True,cpu_only=True,cases=[case],source_sha256=before,gpu_fanout_connected=False,normal_summon_admission=False)
(ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,observations=len(case['observations']),cpu_only=True)))
