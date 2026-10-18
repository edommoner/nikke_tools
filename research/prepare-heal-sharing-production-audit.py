"""Prepare the current production inventory script; no GPU execution."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'research/audit-production-healing-storage.py').read_text(encoding='utf-8').replace('detail_healing_storage_v40','detail_heal_sharing_v41').replace('audit-production-healing-storage.py','audit-production-heal-sharing.py').replace('detail-healing-storage-coverage.json','detail-heal-sharing-coverage.json').replace("'app/healing_storage_compat.py'","'app/healing_storage_compat.py','app/heal_sharing_compat.py'").replace("==159","==161").replace("==627","==635")
(ROOT/'research/audit-production-heal-sharing.py').write_text(s,encoding='utf-8')
