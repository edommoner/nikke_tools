"""Normal API fixture: rich 172-effect roster plus temporary stat changes."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('capacity_fixture',ROOT/'scripts/verify-capacity-detail.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
body=v.rich_fixture();body['stat_deltas']={body['squad'][0]:{'atk':12345,'hp':100000,'def':345}}
(ROOT/'research/detail-capacity-api-fixture.json').write_text(json.dumps(body,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Saved fictional owned-data fixture with temporary stat deltas')
