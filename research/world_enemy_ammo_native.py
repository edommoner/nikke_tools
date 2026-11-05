"""Original battle/weapon/HP observation under the declared ammo provider."""
from enemy_ammo_model import enemy_ammo
from world_logical_geometry_native import observe as logical_battle

def observe(case):
    with enemy_ammo(case['enemy_ammo']) as magazines:native,trace=logical_battle(case)
    native['enemy_ammo']=magazines
    return native,trace
