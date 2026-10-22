"""Literal HP-share contracts; no packing, simulation or GPU-derived inputs."""
import copy
from portable_healing_storage_cases import fixtures as storage_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(storage_fixtures()[0]);base.update(duration=.25,effects=[],owners=[],patterns=[dict(id='idle',kind='idle')],base_atk=[2000,1800,1600,1400,1200])
    for ally in base['environment']['allies']:ally.update(base_hp=10000,base_defense=0)
    for weapon in base['combat']['weapons']:weapon.update(interval=1,capacity=5,reload=.4,stage=0)
    names=roster_names(base);rows=[]
    def link(target='all_allies',name='share',value=1,**kw):return field('heal_split',value,target,name,**kw)
    def heal(value=50,target='self',timing='battle_start'):return instant('heal_hp_pct',value,target,'heal',timing)
    def add(label,links,hp,weights,*,value=50,heal_target='self',timing='battle_start',drain='all_allies',before=(),plans=1,notices=1):
        c=copy.deepcopy(base);c.update(name='heal-share-'+label,effects=[instant('current_hp_reduce',50,drain,'drain'),*before,*links,heal(value,heal_target,timing)])
        c['owners']=[0]*len(c['effects']);c['contract']=dict(hp=hp,weights=weights,plans=plans,notices=notices);rows.append(c);return c
    add('no-link',[],[10000,5000,5000,5000,5000],[(0,1)])
    for value in (0,1,-7):add('presence-'+str(value),[link(value=value)],[6000]*5,[(i,1) for i in range(5)])
    add('same-owner-two-carriers',[link(name='first'),link(name='second')],[6000]*5,[(i,2) for i in range(5)])
    add('self-two-carriers',[link('self','first'),link('self','second')],[10000,5000,5000,5000,5000],[(0,2)])
    add('overlap-ranked',[link('allies_top_atk:3','first'),link('allies_top_atk:2','second')],[7000,7000,6000,5000,5000],[(0,2),(1,2),(2,1)])
    add('chain-connectivity',[link(names[:2],'first'),link(names[1:],'second')],[6000,7000,6000,6000,6000],[(0,1),(1,2),(2,1),(3,1),(4,1)],value=60)
    add('duplicate-authored-members',[link([names[0],names[0],names[1]])],[7000,7000,5000,5000,5000],[(0,1),(1,1)],value=40)
    add('full-member-not-redistributed',[link()],[6000,6000,6000,6000,10000],[(i,1) for i in range(5)],drain='allies_top_atk:4')
    c=add('full-member-storage',[link()],[6000,6000,6000,6000,10000],[(i,1) for i in range(5)],drain='allies_top_atk:4',before=[field('heal_overcharge_store',20,'all_allies','storage')]);c['contract']['storage']=[0,0,0,0,1000]
    add('recipient-multiplier-once',[link()],[6200]*5,[(i,1) for i in range(5)],value=20,before=[field('outgoing_heal_pct',50,'self','outgoing'),field('heal_received_pct',100,'self','original-received'),field('heal_received_pct',200,names[1],'distributed-received')])
    add('all-original-recipients',[link()],[9000]*5,[(i,1) for i in range(5)],value=40,heal_target='all_allies',plans=5,notices=5)
    add('negative-not-shared',[link()],[3000,5000,5000,5000,5000],[],value=-20,plans=0)
    add('zero-not-shared',[link()],[5000]*5,[],value=0,plans=0)
    add('expired-link',[link(duration=.1)],[9000,5000,5000,5000,5000],[(0,1)],value=40,timing='every:0.2s')
    c=add('down-member-excluded',[link()],[6000,6000,6000,6000,0],[(i,1) for i in range(4)],value=40,timing='every:0.2s');c['patterns']=[dict(id='down',kind='attack',delay=.1,spec=dict(atk=1e8,coeff=100,target='slot:5',pierce=True,hits=1))]
    c=add('stack-count-does-not-weight',[link(max_stack=3)],[6000]*5,[(i,1) for i in range(5)],timing='every:0.2s');c['effects'][1]['trigger']['timing']=['battle_start','every:0.05s']
    c=add('adjacent-full-edges',[link()],[10000]*5,[(i,1) for i in range(5)],value=250,before=[field('atk_pct',11,'self','hp-witness',timing='event:adjacent_hp_max')]);c['owners'][1]=2;c['observe_periodic_skills']=True
    # sync_hp notifies every adjacent observer for each healed member, in squad
    # order. The listener owned by slot2 consumes only two of eight notices.
    c['contract']['portion_edges']=[(0,[1]),(1,[0,2]),(2,[1,3]),(3,[2,4]),(4,[3])]
    remove=dict(instant('remove_named_buff',1,names[2],'remove-share','event:adjacent_hp_max'),target_effect='share',max_trigger=1)
    nested=dict(instant('heal_hp_pct',20,names[2],'nested-heal','event:adjacent_hp_max'),max_trigger=1)
    c=add('nested-mask-snapshot',[link()],[10000]*5,[(i,1) for i in range(5)],value=250,before=[remove,nested],plans=2,notices=2)
    c['contract'].update(plan_sequence=[[(i,1) for i in range(5)],[(2,1)]],notice_order=[2,0],original_amounts=[25000,2000],
        portion_sequence=[(0,5000),(1,5000),(2,2000),(2,5000),(3,5000),(4,5000)],
        resumes_after=dict(kind='shared-return',owner=2,amount=2000),
        resumes_at=dict(kind='portion-call',owner=2,amount=5000))
    return rows
