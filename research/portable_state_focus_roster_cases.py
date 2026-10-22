"""Complete newly packable profiles; preserve public equipment and all effects."""
import importlib.util
from pathlib import Path

PROFILES = ('비스킷', '리틀 머메이드', '릴리')


def fixtures():
    spec = importlib.util.spec_from_file_location(
        'state_focus_roster_factory', Path(__file__).with_name('verify-world-projectile-rosters.py'))
    real = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(real)
    rows = []
    for character in PROFILES:
        for duration in (3, 30):
            body = dict(real.body_for(real.policy.roster_for(character), duration),
                        burst_gauge_mode='accumulate')
            rows.append(dict(name=f'state-focus-real/{character}/{duration}s',
                             character=character, favorite_stage=0, duration=duration, body=body))
    return rows
