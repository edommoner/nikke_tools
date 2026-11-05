"""Complete source profile: no removed or rewritten Lock On definitions."""
import copy,importlib.util,json
from pathlib import Path
NAME='스노우 화이트 : 헤비암즈'

def source_definitions():
    path=Path(__file__).resolve().parent/'upstream/nikke-calc-master/data/parsed_skills.json'
    return json.loads(path.read_text(encoding='utf-8'))[NAME]

def factory():
    path=Path(__file__).resolve().parent/'verify-world-projectile-rosters.py'
    spec=importlib.util.spec_from_file_location('heavyarms_lock_roster_factory',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def fixtures():
    source=factory()
    rows=[dict(name='heavyarms-lock-marker/'+str(duration)+'s',body=dict(source.body_for(source.policy.roster_for(NAME),duration),burst_gauge_mode='accumulate',seed=2427)) for duration in (3,30)]
    for base,queries in zip(rows[:],(88,820),strict=True):
        case=copy.deepcopy(base);case['name']+='-three-adds'
        assert 'patterns' not in case['body']['enemy']
        case['body']['enemy']['patterns']=[dict(id='lock-wave',kind='summon',spec=dict(count=3,hp=1e30))]
        case.update(expected_marker_target='__enemy__:lock-wave#1',expected_natural_queries=queries);rows.append(case)
    return rows
