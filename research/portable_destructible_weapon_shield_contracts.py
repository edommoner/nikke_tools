"""Literal native V3 outcomes; no portable packing, GPU or game admission."""
EXPECTED={
 'auto-hp-factor':(0,4,[1451.]*4,[4196.]),
 'auto-hit-credit':(1936,4,[968.]*2,[0.]),
 'auto-break-no-overflow':(2904,4,[1451.],[0.]),
 'scatter-hp-factor':(0,4,[484.]*12,[4192.]),
 'scatter-hit-break-before-third':(3230,4,[323.]*2,[0.]),
 'scatter-hp-then-hit-then-body':(3230,4,[484.,323.],[0.,0.]),
 'scatter-hit-then-hp':(0,4,[323.]+[484.]*11,[0.,4676.]),
 'scatter-counter-child-keeps-shot-buff-snapshot':(0,4,[484.]*3+[1021.]*9,[0.]),
 'scatter-counter-skill-consumes-separate-credit':(3553,4,[323.,484.],[0.]),
 'full-charge-hp-context':(0,2,[2902.]*2,[4196.]),
 'charge-scatter-hp-context':(0,2,[968.]*6,[4192.]),
 'tap-hit-credit':(968,3,[968.]*2,[0.]),
 'weapon-change-False':(0,4,[2902.]*4,[0.]),
 'weapon-change-True':(0,4,[1451.]*2+[2902.]*2,[1294.]),
 'empty-owner-keeps-body':(3872,4,[],[10000.]),
 'world-expiry-keeps-later-body':(1936,4,[1451.]*2,[7098.]),
 'core-context-is-preserved':(0,4,[2801.]*4,[0.]),
 'two-muzzles-hit-credit':(4840,4,[968.]*3,[0.]),
 'last-squad-owner':(0,[0,0,0,0,4],[1451.]*4,[4196.]),
 'two-allied-attackers':([2904,3872,0,0,0],[4,4,0,0,0],[968.],[0.]),
 'rl-explosion-charge-context':(0,2,[4838.]*2,[324.]),
 'hp-policy-skips-hit-shield':(3872,4,[],[2.]),
}

def verify(case,native):
 name=case['name'].split('/')[-1];body,shots,amounts,remaining=EXPECTED[name]
 if isinstance(body,int):body=[body,0,0,0,0]
 if isinstance(shots,int):shots=[shots,0,0,0,0]
 assert native['battle']['damage']==body,(name,native['battle']['damage'],body)
 assert native['battle']['shots']==shots,(name,native['battle']['shots'],shots)
 ammo=[1000-count for count in shots]
 if name.startswith('weapon-change-'):ammo[0]=998 # Two infinite-mode shots, then two base shots.
 assert native['battle']['ammo']==ammo,(name,native['battle']['ammo'],ammo)
 gauges={'scatter-hp-factor':3.,'scatter-hit-break-before-third':3.,'scatter-hp-then-hit-then-body':3.,'scatter-hit-then-hp':3.,'scatter-counter-child-keeps-shot-buff-snapshot':3.,'scatter-counter-skill-consumes-separate-credit':3.25,'full-charge-hp-context':.5,'charge-scatter-hp-context':1.5,'tap-hit-credit':.75,'two-muzzles-hit-credit':2.,'two-allied-attackers':2.,'rl-explosion-charge-context':.5}
 assert native['battle']['gauge']==gauges.get(name,1.),(name,native['battle']['gauge'])
 rows=native['attacks'];assert [r['damage'] for r in rows]==amounts and native['remaining']==remaining,(name,rows,native['remaining'])
 assert native['finished'] and all(r['completed'] and len(r['receipts'])==1 and r['receipts'][0]['delivered'] for r in rows)
 for r in rows:
  p=r['receipts'][0]
  if p['handle'][0]==4:assert p['took']==1.
 if name=='scatter-counter-skill-consumes-separate-credit':assert [r['family'] for r in rows]==[0,1]
 else:assert all(r['family']==0 for r in rows)
 if name=='last-squad-owner':assert all(r['owner']==4 for r in rows)
 if name=='weapon-change-True':assert [r['weapon_mode_skill'] for r in rows]==[True,True,False,False]
 return dict(verified=True,reference_model_gap=True,declared_model=True,canonical_consumer_verified=False,actual_battle_scheduler=True,actual_weapon_methods=True,native_per_shot_buff_snapshot=True,pellet_target_selection=True,gpu_connected=False,in_game_rules_verified=False)
