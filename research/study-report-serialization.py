"""Offline lossless JSON size study; does not modify reports or GPU sources."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'research/portable-combat-metal.json'
raw = path.read_bytes()
report = json.loads(raw)
compact = (json.dumps(report, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
assert json.loads(compact) == report
result = dict(passed=True, cpu_only=True, production_format_changed=False,
              source_report=path.relative_to(ROOT).as_posix(), source_report_sha256=hashlib.sha256(raw).hexdigest(),
              pretty_bytes=len(raw), lossless_compact_bytes=len(compact), ratio=len(compact) / len(raw),
              no_keys_or_values_removed=True, round_trip_equal=True,
              tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              scope='Offline serialization experiment only;no GPU execution,baseline report mutation or source change')
(ROOT / 'research/portable-report-serialization-study.json').write_text(json.dumps(result, indent=2) + '\n')
print('Unchanged report object:', len(raw), 'bytes pretty,', len(compact), 'bytes compact')
