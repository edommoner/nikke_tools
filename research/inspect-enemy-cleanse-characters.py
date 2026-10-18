import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('inspect_cleanser',ROOT/'scripts/verify-boss-buffs-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
raw=json.loads((ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text(encoding='utf-8'));rows=[]
for n,es in raw.items():
 if not isinstance(es,list) or not any(e.get('stat')=='enemy_buff_cleanse' for e in es if isinstance(e,dict)):continue
 b=v.v.body_for([n]+[x for x in v.v.NAMES if x!=n][:4],30,True)
 try:v.a.evaluate({**b,'_compile_gpu_detail':True});row={'character':n,'accepted':True}
 except v.g.UnsupportedDetail as e:row={'character':n,'accepted':False,'issues':e.issues}
 rows.append(row);print(json.dumps(row,ensure_ascii=True))
(ROOT/'research/detail-enemy-cleanse-characters.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
