import json
from pathlib import Path
p=Path(__file__).resolve().parent/'detail-expansion-next.json'
r=json.loads(p.read_text(encoding='utf-8'))
r['current_work']={'abi':'detail_boss_clock_v31','status':'verification_in_progress','feature':'GPU-owned core/move/idle/groggy lifecycle and live overlays; normal UI editor','quick_report':'research/detail-boss-clock-native-quick.json','full_report':'research/detail-boss-clock-verification.json','objective_complete':False}
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
