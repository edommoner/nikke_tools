"""Refresh public historical raid facts; no player/account requests."""
import datetime,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
query='{ soloraids { raid_number wave_name monster_obj stats wave_obj } }'
req=urllib.request.Request('https://enikk.app/api/graphql',data=json.dumps({'query':query}).encode(),headers={'Content-Type':'application/json','User-Agent':'NikkeTools/0.2'})
raw=json.load(urllib.request.urlopen(req,timeout=60))
if raw.get('errors'): raise ValueError(raw['errors'])
codes={'Water':'수냉','Fire':'작열','Wind':'풍압','Electronic':'전격','Iron':'철갑'}
rows=[]
for raid in raw['data']['soloraids']:
    monster,stats=raid['monster_obj'],raid['stats']
    code=codes[monster['element_id']['element']]
    defense=stats['level_defence']*monster['defence_ratio']/10000
    number=raid['raid_number']
    rows.append({'id':f'archive:solo:{number}','mode':'solo','season':number,'label':f"ソロレイド S{number:02} / {monster['name_localkey']}（静止近似）",
      'settings':{'enemy-def':defense,'enemy-code':code,'level':400,'duration':raid['wave_obj']['battle_time'],'core':0,'distance':30},
      'source':'https://enikk.app/soloraid', 'source_api':'https://enikk.app/api/graphql','boss_level':stats['lv'],
      'source_defense':stats['level_defence'],'defense_ratio':monster['defence_ratio'],
      'note':f"開催履歴S{number}の敵データ（敵Lv{stats['lv']}）。防御力は基礎値×ボス倍率。指揮官側Lv400、コアなし・距離30mは比較用の仮定です。移動・パーツ・ギミックは未再現です。"})
result={'fetched_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'https://enikk.app/api/graphql','query':query,'presets':sorted(rows,key=lambda r:r['season'],reverse=True)}
prior_path=ROOT/'data/raid-presets.json'
prior=json.loads(prior_path.read_text(encoding='utf-8-sig')) if prior_path.exists() else {}
result['presets'] += [r for r in prior.get('presets',[]) if r.get('mode')=='union']
for k in ('union_fetched_at','union_query'):
 if k in prior: result[k]=prior[k]
(ROOT/'data/raid-presets.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'presets':len(rows),'seasons':[min(r['season'] for r in rows),max(r['season'] for r in rows)],'elements':sorted(set(r['settings']['enemy-code'] for r in rows))},ensure_ascii=True))
