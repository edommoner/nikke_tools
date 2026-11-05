"""Compose existing native plan/recipient observation with the typed battle."""
from world_destructible_accum_native import observe as prior
from world_heal_share_native import capture
def observe(case):
    with capture(dict(case,names=case['body']['squad'])) as sharing:n,t=prior(case)
    n['healing_recipients']=sharing['receipts'];n['heal_share_events']=sharing['events']
    return n,t
