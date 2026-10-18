"""Complete raw-definition taxonomy; acceptance and evidence stay separate."""
import collections,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from effect_spec import describe_effect,FAMILIES,RECOVERY_ORDER,COMPAT_LAYERS

source=ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json'
raw=json.loads(source.read_text(encoding='utf-8'))
families=collections.Counter();stats={};facets={key:collections.Counter() for key in ('types','fields','targets','timings','conditions')}
unclassified=[];count=0
for character,effects in raw.items():
    if not isinstance(effects,list):continue
    for index,effect in enumerate(effects):
        count+=1;description=describe_effect(effect);families[description['family']]+=1
        if description['family']=='unclassified':unclassified.append([character,index,effect.get('stat')])
        key=json.dumps(effect.get('stat'),ensure_ascii=False)
        row=stats.setdefault(key,{**description,'definitions':0,'characters':set(),'types':set()})
        row['definitions']+=1;row['characters'].add(character);row['types'].add(effect.get('type'))
        facets['types'][str(effect.get('type'))]+=1
        facets['fields'].update(effect.keys())
        facets['targets'][json.dumps(effect.get('target'),ensure_ascii=False,sort_keys=True)]+=1
        for field in ('timings','conditions'):
            source_key='timing' if field=='timings' else 'condition'
            for value in effect.get('trigger',{}).get(source_key,[]):
                facets[field][json.dumps(value,ensure_ascii=False,sort_keys=True)]+=1
for row in stats.values():row['characters']=sorted(row['characters']);row['types']=sorted(row['types'])
report={'passed':not unclassified,'scope':'All parsed skill definitions; semantic classification is not execution support or in-game verification.',
        'raw_definitions':count,'stat_forms':len(stats),'families':dict(families),
        'family_count':len(FAMILIES),'unclassified':unclassified,'stats':stats,
        'facets':{k:dict(v) for k,v in facets.items()},'recovery_order':RECOVERY_ORDER,
        'reference_layer_order':COMPAT_LAYERS,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
(ROOT/'research/effect-spec-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ('passed','raw_definitions','stat_forms','family_count','unclassified')}))
raise SystemExit(0 if report['passed'] else 1)
