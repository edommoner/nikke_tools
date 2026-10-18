"""Compact read-only progress from mixed unittest/JSON verification logs."""
import collections,json,sys
from pathlib import Path
for name in sys.argv[1:]:
    raw=Path(name).read_bytes();text=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig',errors='replace')
    rows=[]
    for line in text.splitlines():
        if not line.startswith('{'):continue
        try:row=json.loads(line)
        except ValueError:continue
        if isinstance(row,dict) and 'passed' in row:rows.append(row)
    print(json.dumps(dict(log=name,rows=len(rows),failed=sum(not r['passed'] for r in rows),backends=dict(collections.Counter(r.get('backend','unspecified') for r in rows)),tail=text.splitlines()[-1][:120] if text.splitlines() else ''),ensure_ascii=True))
