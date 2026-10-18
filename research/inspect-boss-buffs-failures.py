import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for f in (sys.argv[1:] or ['detail-boss-buffs-native-verification.log','detail-boss-buffs-tests.log']):
 raw=(ROOT/'research'/f).read_bytes();s=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
 for line in s.splitlines():
  try:r=json.loads(line)
  except ValueError:continue
  if not r.get('passed',True):print(json.dumps(dict(file=f,name=r.get('name'),failed=[k for k,v in r.get('checks',{}).items() if not v],difference=r.get('world_frame_difference'),cpu_total=r.get('cpu_total'),gpu_total=r.get('gpu_total')),ensure_ascii=True))
