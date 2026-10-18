"""Read-only receipt for the shared CPU carrier identity witnesses."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from lifecycle_carrier_cases import callback_identity_cases
files=[p for folder in ('app','scripts') for p in (ROOT/folder).glob('*.py')]
hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
rows=callback_identity_cases();stable=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest for p,digest in hashes.items())
report=dict(scope='CPU callback identity only; no GPU or game proof',source_stable=stable,all_operations_use_current_carrier=all(r['contract_satisfied'] for r in rows),operations=rows,source_sha256=hashes)
(ROOT/'research/legacy-carrier-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(source_stable=stable,operations=rows),indent=2));assert stable
