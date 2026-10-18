"""Capture independent sparse-recipient observations, CPU reference stage only."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from enemy_recipient_cases import exercise
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
files=list((ROOT/'app').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/enemy_recipient_cases.py',ROOT/'tests/test_target_counter_runtime.py',ROOT/'tests/test_enemy_recipient_runtime.py',ROOT/'app/detail_effects.cu',ROOT/'app/detail_effects-sm86.cubin',ROOT/'app/detail_effects-sm86.json',ROOT/'app/detail_effects.ptx',ROOT/'app/detail_effects-build.json',ROOT/'data/engine-effect-overrides.json']
before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
case=exercise();assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
report=dict(passed=True,cpu_only=True,cases=[case],source_sha256=before,gpu_storage_connected=False,normal_summon_admission=False)
(ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,observations=len(case['observations']),cpu_only=True)))
