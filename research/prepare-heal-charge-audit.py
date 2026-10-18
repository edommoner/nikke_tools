"""Prepare the isolated definition inventory without changing production."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'research/audit-heal-sharing.py').read_text(encoding='utf-8').replace('heal-sharing','heal-charge').replace('heal_sharing_compat','heal_charge_compat').replace('staging/v41','staging/v42').replace("'app/healing_storage_compat.py'","'app/healing_storage_compat.py','app/heal_sharing_compat.py'")
(ROOT/'research/audit-heal-charge.py').write_text(s,encoding='utf-8')
