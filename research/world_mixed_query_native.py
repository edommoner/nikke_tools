"""Compose read-only native observers; no additional numerical/target query."""
from unittest.mock import patch
import world_heal_share_native as healing
from world_focus_aim_native import observe as focus_observe
from world_late_attack_random_native import capture_queries
from world_frame_native import roster_names


def observe(case):
    with capture_queries(roster_names(case),with_selectors=True) as (queries,samples),patch.object(healing,'projectile_native',focus_observe):
        native,trace=healing.observe(case)
    native['mixed_query']=dict(queries=queries,samples=samples)
    return native,trace
