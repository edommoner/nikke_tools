"""Prepare the current production inventory; compilation is not universal parity."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'research/audit-production-heal-sharing.py').read_text(encoding='utf-8').replace('detail_heal_sharing_v41','detail_heal_charge_v42').replace('audit-production-heal-sharing.py','audit-production-heal-charge.py').replace('detail-heal-sharing-coverage.json','detail-heal-charge-coverage.json').replace("'app/heal_sharing_compat.py'","'app/heal_sharing_compat.py','app/heal_charge_compat.py'").replace('==161','==162').replace('==635','==639')
(ROOT/'research/audit-production-heal-charge.py').write_text(s,encoding='utf-8')
