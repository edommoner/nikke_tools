"""Prepare a focused ordinary suite without mutating production code."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'research/verify-healing-storage-production.py').read_text(encoding='utf-8').replace('detail_healing_storage_v40','detail_heal_sharing_v41').replace('research/verify-healing-storage-production.py','research/verify-heal-sharing-production.py').replace('research/detail-healing-storage-production-verification.json','research/detail-heal-sharing-production-verification.json')
s=s.replace("modules=['test_detail_healing_storage','test_detail_healing_storage_boundary']","modules=['test_detail_healing_storage','test_detail_healing_storage_boundary','test_detail_heal_sharing','test_detail_heal_sharing_boundary','test_detail_outgoing_healing_boundary']")
s=s.replace("'app/healing_storage_compat.py'","'app/healing_storage_compat.py','app/heal_sharing_compat.py','scripts/heal-sharing-fixtures.py','scripts/verify-heal-sharing.py'").replace('==11','==23').replace('whole_squad_cases=153','whole_squad_cases=178').replace('boundary_tests=7','boundary_tests=17')
s=s.replace('Focused ordinary v40 suite; 153 squads and seven host boundaries.','Focused ordinary v41 suite; 178 squads and seventeen host boundaries.')
(ROOT/'research/verify-heal-sharing-production.py').write_text(s,encoding='utf-8');print('Prepared production verifier; not executed.')
