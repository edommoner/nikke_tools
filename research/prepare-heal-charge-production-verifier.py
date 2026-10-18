"""Prepare the ordinary production suite without changing production files."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'research/verify-heal-sharing-production.py').read_text(encoding='utf-8').replace('detail_heal_sharing_v41','detail_heal_charge_v42').replace('research/verify-heal-sharing-production.py','research/verify-heal-charge-production.py').replace('research/detail-heal-sharing-production-verification.json','research/detail-heal-charge-production-verification.json')
s=s.replace("'test_detail_outgoing_healing_boundary']","'test_detail_outgoing_healing_boundary','test_detail_heal_charge','test_detail_heal_charge_boundary']")
s=s.replace("'app/heal_sharing_compat.py'","'app/heal_sharing_compat.py','app/heal_charge_compat.py','scripts/heal-charge-fixtures.py','scripts/heal-charge-extra-fixtures.py','scripts/verify-heal-charge.py','scripts/verify-heal-charge-extra.py'").replace('==23','==36').replace('whole_squad_cases=178','whole_squad_cases=208').replace('boundary_tests=17','boundary_tests=27')
s=s.replace('Focused ordinary v41 suite; 178 squads and seventeen host boundaries.','Focused ordinary v42 suite; 208 squads and twenty-seven host boundaries.')
(ROOT/'research/verify-heal-charge-production.py').write_text(s,encoding='utf-8');compile(s,'research/verify-heal-charge-production.py','exec')
print('Prepared production36 verifier; not executed.')
