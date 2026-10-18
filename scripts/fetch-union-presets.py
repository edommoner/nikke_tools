"""Append historical union-raid enemy facts from Enikk's public API."""
import json,urllib.request,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def query(q):
 req=urllib.request.Request('https://enikk.app/api/graphql',data=json.dumps({'query':q}).encode(),headers={'Content-Type':'application/json','User-Agent':'NikkeTools/0.3'})
 raw=json.load(urllib.request.urlopen(req,timeout=60))
 if raw.get('errors'):raise ValueError(raw['errors'])
 return raw['data']
numbers=query('{ unionRaidNumbers }')['unionRaidNumbers']
q='{'+ ' '.join(f'r{n}:unionraidbosses(raidNumber:{n}){{ wave_order difficulty_type monster_obj stats }}' for n in numbers)+'}'
data=query(q)
archive=json.loads((ROOT/'data/raid-presets.json').read_text(encoding='utf-8-sig'))
solo=[{**r,'mode':'solo'} for r in archive['presets'] if r.get('mode','solo')=='solo']
codes={'Water':'수냉','Fire':'작열','Wind':'풍압','Electronic':'전격','Iron':'철갑'}
rows=[]
for number in numbers:
 for boss in data[f'r{number}']:
  m=boss['monster_obj'];name=m['name_localkey'];kind=boss['difficulty_type']
  for stat in boss['stats']:
   stage=stat['level'];defense=stat['level_defence']*m['defence_ratio']/10000
   rows.append({'id':f'archive:union:{number}:{boss["wave_order"]}:{kind}:{stage}','mode':'union','season':number,'boss_name':name,'difficulty':kind,'stage':stage,
    'label':f'ユニオン R{number} / {name} / {kind} {stage}',
    'settings':{'enemy-def':defense,'enemy-code':codes[m['element_id']['element']],'level':400,'duration':180,'core':0,'distance':30},
    'boss_level':stat['lv'],'source_defense':stat['level_defence'],'defense_ratio':m['defence_ratio'],
    'source':'https://enikk.app/unionraid','source_api':'https://enikk.app/api/graphql',
    'note':f'ユニオンR{number}・{kind} {stage} / {name}。敵Lv{stat["lv"]}の基礎防御×ボス倍率。ニケLv400、180秒、コアなし・距離30mは比較用の仮定。生存・移動・パーツ破壊は未再現。'})
archive['union_fetched_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();archive['union_query']=q;archive['presets']=solo+rows
(ROOT/'data/raid-presets.json').write_text(json.dumps(archive,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'solo':len(solo),'union_conditions':len(rows),'union_seasons':[min(numbers),max(numbers)]}))
