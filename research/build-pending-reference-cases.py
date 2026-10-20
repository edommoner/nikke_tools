"""Pending coefficient scaling is sampled at fire time,not an activation hit count."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 cases=[]
 scenarios={'missing':(None,0),'zero':(0,0),'one':(1,1),'three':(3,3),'fraction':(3.9,3),'after-cast-change':(3,5),'full-start-change':(3,5),'zero-at-fire':(3,0),'late-init':(0,3),'large':(300,300),'buff':(None,2),'precedence':(5,5)}
 for owner in range(5):
  fillers=[i for i in range(5) if i!=owner];stages=[0]*5;stages[fillers[0]]=1;stages[fillers[1]]=2;stages[owner]=3
  for scenario,(initial,scale) in scenarios.items():
   for coefficient in (1.1,33.333):
    def effect(name,kind,stat,value,timing,**kw):return dict(name=name,type=kind,stat=stat,source='스킬3',fixed_value=value,target='self',trigger=dict(timing=[timing],condition=[]),**kw)
    effects=[dict(effect('no-critical','buff','crit_rate',-15,'battle_start',duration=-1),target='all_allies')];owners=[owner]
    if initial is not None:effects.append(effect('initial','instant','gauge_charge',initial,'battle_start',gauge_id='Reference'));owners.append(owner)
    if scenario in ('buff','precedence'):
     marker=effect('Reference','buff','',0,'battle_start',duration=-1,max_stack=3);marker['trigger']['timing'].append('full_burst_start');effects.append(marker);owners.append(owner)
    packet=dict(effect('pending-reference','damage','bonus_damage',coefficient,'burst_cast'),target='boss',scaling='stack_count',scaling_ref='Reference');effects.append(packet);owners.append(owner)
    if scenario in ('after-cast-change','full-start-change','late-init'):
     effects.append(effect('change-reference','instant','gauge_charge',3 if scenario=='late-init' else 2,'burst_cast' if scenario=='after-cast-change' else 'full_burst_start',gauge_id='Reference'));owners.append(owner)
    if scenario=='zero-at-fire':effects.append(effect('empty-reference','instant','gauge_consume',-1,'full_burst_start',gauge_id='Reference'));owners.append(owner)
    damage=[0]*5;damage[owner]=max(1,round((coefficient*scale/100)*1000*1.5)) if scale else 0
    cases.append(dict(name=f'pending-reference-{owner}-{scenario}-{coefficient}',pending_scale_reference=True,pending_reference_context=dict(owner=owner,stages=stages),effects=effects,owners=owners,combat=dict(trace='full',initial_gauge=100,weapons=[dict(enabled=False,stage=s,cooldown=40) for s in stages],targets=[dict(hp=1e12,defense=0)]),script=[[.2,24,0,0,0,-1,0,0],[.2,2,0,0,0,0,0,0],[1,24,0,0,0,-1,0,0],[1,2,0,0,0,1,0,0]],expected_queries=[dict(damage=[0]*5,pending_burst=dict(count=1,enqueued=1,fired=0)),dict(damage=damage,pending_burst=dict(count=0,enqueued=1,fired=1))]))
 (ROOT/'tests/fixtures/portable-pending-reference.json').write_text(json.dumps(dict(cases=cases),ensure_ascii=False,indent=2)+'\n');print(len(cases),'pending reference inputs authored')
if __name__=='__main__':main()
