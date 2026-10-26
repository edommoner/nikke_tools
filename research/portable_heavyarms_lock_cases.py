"""Complete source profile: no removed or rewritten Lock On definitions."""
import importlib.util,json
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
    return [dict(name='heavyarms-lock-marker/'+str(duration)+'s',body=dict(source.body_for(source.policy.roster_for(NAME),duration),burst_gauge_mode='accumulate',seed=2427)) for duration in (3,30)]
