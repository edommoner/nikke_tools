"""Compose existing native lifesteal and accumulation observation without tags."""
from world_damage_accum_native import capture
from world_destructible_lifesteal_native import observe as prior
def observe(case):
    with capture(case['body']['squad'],identity_rows=True) as data:n,t=prior(case)
    n['damage_accumulation']=data
    return n,t
