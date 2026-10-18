"""Keep the failed ordinary acceptance, bound to its immutable source snapshot."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'research/detail-normal-acceptance.json';r=json.loads(path.read_text(encoding='utf-8'))
assert not r['passed'] and r['interrupted_after_known_failure'] and len(r['failures'])==4
archive=ROOT/'research/ports/v34-production-before-burst-wait-fix'
for p,h in r['source_sha256'].items():assert hashlib.sha256((archive/p).read_bytes()).hexdigest()==h,p
r['source_archive']='research/ports/v34-production-before-burst-wait-fix'
out=ROOT/'research/detail-survival-rejected-normal-acceptance.json';assert not out.exists()
out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Preserved rejected normal acceptance with all archived sources validated.')
