"""CPU groundwork for range/part geometry; no production GPU support claim."""
import hashlib,itertools,json,sys
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a
from calculator import boss_pattern as boss
from calculator.buff_manager import in_optimal_range,optimal_range_of
from calculator.timeline import CharState

def audit():
    reach=[];areas=[];optimal=[]
    values=[-100,0,99,100-2*boss._EPS,100-.5*boss._EPS,100,150,300]
    for parts,explosion,pierce in itertools.product([False,True],repeat=3):
        for er,pr in itertools.product(values,repeat=2):
            params=dict(parts_skill=parts,explosion=explosion,pierce=pierce,explosion_range=er,pierce_range=pr)
            reach.append(dict(input=params,expected=boss.hit_reach(**params)))
    assert {row['expected'] for row in reach}==set(range(6))
    assert boss.hit_reach(pierce=True,pierce_range=100-2*boss._EPS)==1
    assert boss.hit_reach(pierce=True,pierce_range=100-.5*boss._EPS)==2
    assert all(row['expected']==5 for row in reach if row['input']['parts_skill'])
    for cdn in [None,100.0]:
        state=SimpleNamespace(_explosion_cdn=cdn);geom=SimpleNamespace(pierce_px=2.5,explosion_scale=.2)
        for pierce,explosion in itertools.product([False,True],repeat=2):
            for pr,er in itertools.product([-100,0,50,100,300],repeat=2):
                buffs=dict(pierce_range=pr,explosion_range=er)
                value=CharState._area_radius(state,geom,buffs,pierce,explosion)
                areas.append(dict(input=dict(explosion_cdn=cdn,pierce_px=2.5,explosion_scale=.2,pierce=pierce,explosion=explosion,buffs=buffs),expected=value))
    assert CharState._area_radius(SimpleNamespace(_explosion_cdn=100),geom,{'pierce_range':100},True,False)==5
    assert CharState._area_radius(SimpleNamespace(_explosion_cdn=100),geom,{'explosion_range':50},False,True)==30
    for name,weapon in [('앨리스','SR'),('하란','SR'),('앨리스','AR'),('N102','RL')]:
        lo,hi=optimal_range_of(name,weapon)
        for low,high in itertools.product([0,50,100],repeat=2):
            buffs=dict(optimal_range_min_pct=low,optimal_range_max_pct=high)
            for distance in [None,0,lo-1,lo,hi,hi+1,hi*2,hi*2+1]:
                for listed in [False,True]:
                    enemy=dict(distance=distance,optimal_range_weapons=[weapon] if listed else [])
                    optimal.append(dict(input=dict(enemy=enemy,name=name,weapon_type=weapon,buffs=buffs),base_range=[lo,hi],expected=in_optimal_range(enemy,name,weapon,buffs)))
    assert in_optimal_range({'distance':None,'optimal_range_weapons':['SR']},'앨리스','SR',{})
    assert not in_optimal_range({'distance':None},'앨리스','SR',{})
    source=ROOT/'research/upstream/nikke-calc-master/data/parsed_skills.json';raw=json.loads(source.read_text(encoding='utf-8'))
    definitions=[dict(character=name,effect=eff) for name,effects in raw.items() for eff in effects if eff.get('stat') in ('pierce_range','explosion_range','optimal_range_min','optimal_range_max_pct','effect_range_pct')]
    files=['scripts/audit-range-geometry.py','research/upstream/nikke-calc-master/calculator/boss_pattern.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']
    return dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_only=True,gpu_implemented=False,combat_integrated=False,semantic_assertions_passed=True,
        reach=reach,areas=areas,optimal=optimal,raw_definitions=definitions,source_definition_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        scope='Authored reach-stage, area-radius and optimal-range CPU primitives. Full live parts, coordinates, hit selection and destruction are not implemented by this audit.',
        source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})

if __name__=='__main__':
    report=audit();(ROOT/'research/detail-range-geometry-cpu-references.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:len(report[key]) for key in ['reach','areas','optimal','raw_definitions']}))
