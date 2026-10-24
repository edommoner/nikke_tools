"""Literal credit/HP separation and actual scheduler outcomes, declared V2."""
EXPECTED={
 'two-packets-two-credits':(3872,[968.,968.],[0.],[1.,1.]),
 'break-without-damage-overflow':(4840,[968.],[0.],[1.]),
 'hp-after-hit-shield':(3872,[968.,1451.],[0.,3549.],[1.,1451.]),
 'hit-after-hp-shield':(3872,[1451.,968.],[0.,1.],[500.,1.]),
 'hp-factor-cannot-multiply-hit-credit':(3872,[968.,968.],[3.],[1.,1.]),
 'projectile-factor-cannot-multiply-hit-credit':(3872,[968.,968.],[0.],[1.,1.]),
 'large-damage-still-one-credit':(3872,[967500.,967500.],[3.],[1.,1.]),
 'named-coefficient-keeps-credit-one':(3872,[1451.,1451.],[1.],[1.,1.]),
 'named-child-consumes-separate-credit':(0,[968.,484.],[0.],[1.,1.]),
 'death-counter-child-falls-back-to-body':(5324,[968.],[0.],[1.]),
 'respawn-generation-credits-are-isolated':(3872,[968.,968.,968.],[0.],[1.,1.,1.]),
 'other-owner-does-not-intercept':(5808,[],[2.],[]),
 'expiry-does-not-consume-next-credit':(4840,[968.],[1.],[1.]),
 'hp-factor-still-applies-to-hp-shields':(3872,[1451.,1451.],[7098.],[1451.,1451.]),
 'legacy-hp-policy-skips-hit-shield':(5808,[],[2.],[]),
 'zero-coefficient-publishes-no-credit':(3872,[],[2.],[]),
 'threshold-child-consumes-third-credit':(3872,[968.,968.,484.],[0.],[1.,1.,1.]),
 'stale-owner-generation-does-not-intercept':(5808,[],[2.],[]),
}

def verify(case,native):
 name=case['name'].split('/')[-1];body,amounts,remaining,took=EXPECTED[name];rows=native['attacks']
 assert native['battle']['damage'][0]==body,(name,native['battle']['damage'][0],body)
 assert [r['damage'] for r in rows]==amounts and native['remaining']==remaining,(name,rows,native['remaining'])
 assert [p['took'] for r in rows for p in r['receipts']]==took
 assert native['finished'] and all(r['completed'] and len(r['receipts'])==1 and r['receipts'][0]['delivered'] for r in rows)
 for row in rows:
  p=row['receipts'][0]
  if p['handle'][0]==4:assert p['took']==1.
 if name=='respawn-generation-credits-are-isolated':assert [r['receipts'][0]['handle'][2] for r in rows]==[1,2,3]
 return dict(verified=True,reference_model_gap=True,declared_model=True,canonical_consumer_verified=False,actual_battle_scheduler=True,damage_and_credit_independent=True,owner_generation_matched=True,gpu_connected=False,in_game_rules_verified=False)
