from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ['scripts/build-combat.py','scripts/build-detail-native.py']:
 p=ROOT/name;s=p.read_text(encoding='utf-8');assert 'detail_burst_gauge_v17' in s
 p.write_text(s.replace('detail_burst_gauge_v17','detail_burst_stage_v18'),encoding='utf-8')
