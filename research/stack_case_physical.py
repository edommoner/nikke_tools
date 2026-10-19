"""Authored physical and delayed-recipient stack cases; same backend inputs."""
import copy

def cases(buff,op,notify,query,case):
    rows=[]
    def add(name,effects,script,**kw):rows.append(case(name,effects,script,**kw));return rows[-1]
    never=dict(timing=['battle_start'],condition=[])
    for n in (0.,-0.,.5,-.5,-1.,1.9,1e308):
        add('max-raw-integer-'+repr(n),[buff(max_stack=3),op('buff_max_stack_add',n)],[notify(0),notify(1,7),query(1)])
    for stat in ('buff_max_stack_add','buff_stack_add'):
        for values in (None,{'10':2}):
            e=op(stat);e.pop('fixed_value')
            if values is not None:e['values']=values
            add(stat+'-value-fallback-'+str(bool(values)),[buff(),e],[notify(0),notify(1,7),query(1)])
    immune=buff(name='immune',stat='stack_change_immune',max_stack=1,duration=.5)
    add('expired-unretired-immunity-presence',[buff(),immune,op('buff_stack_add',2)],[notify(0),notify(1,7),query(1)])
    gate=buff(name='gate',duration=-1)
    immune=buff(name='immune',stat='stack_change_immune',max_stack=1,duration=-1,trigger=dict(timing=['event:full_reload'],condition=['self_state:gate']))
    remove=op('buff_stack_add',name='remove gate',target_effect='gate',trigger=dict(timing=['hit_count'],condition=[]));remove['stat']='remove_named_buff'
    add('immune-runtime-predicate-is-not-rechecked',[buff(),gate,immune,remove,op('buff_stack_add',2)],[notify(0),notify(.5,8),notify(1,7),query(1)])
    for stat in ('buff_max_stack_add','buff_stack_add'):
        lazy=buff(stat='stack_change_immune',target='allies_top_atk:1')
        add('lazy-marker-'+stat+'-without-query',[lazy,op(stat,2)],[notify(0),notify(1,7)])
    seed=buff(stat='buff_max_stack_add',trigger=never)
    child=buff(name='child',max_stack=1,trigger=dict(timing=['stack_reach:seed:4'],condition=[]))
    change=op('buff_stack_add',1,name='change',trigger=dict(timing=['event:full_reload'],condition=[]))
    add('init-can-target-ephemeral-buff-definition',[seed,op('buff_stack_init',3),change,child],[notify(0,7),notify(1),query(1)])
    no_crit=buff(name='no crit',stat='crit_rate',fixed_value=-15,target='all_allies',duration=-1,max_stack=1,trigger=never)
    seed=buff(duration_bullets=2,target='all_allies',max_stack=3)
    maximum=op('buff_max_stack_add',2,target='all_allies',trigger=dict(timing=['full_charge_fire'],condition=[]))
    c=add('max-per-target-overrides-rise-at-representative-cap',[no_crit,seed,maximum],[notify(0),notify(0),notify(0),[0,4,0,0,0,-1,0,0],[.25,4,0,0,0,-1,0,0],[.5,4,0,0,0,-1,0,0],notify(.6),notify(.7,11),query(.7)],stack_bullet_reference=True)
    c['combat']['weapons']=[dict(enabled=True,capacity=100,interval=.25,reload=1,coefficient=100),dict(enabled=True,capacity=100,interval=1,reload=1,coefficient=100)]+[dict(enabled=False) for _ in range(3)]
    c['expected_final']=dict(carriers=[dict(definition=1,recipient_stack_overrides=[3]*5,stacks=3,activated=.6,end=2.6)])
    rank=copy.deepcopy(c);rank['name']='stack-per-target-overrides-and-representative-ranking'
    gift=buff(name='ranked gift',fixed_value=100,target='allies_top_atk:1',max_stack=1,duration=-1,trigger=dict(timing=['full_charge'],condition=[]))
    rank['effects'].append(gift);rank['owners']=[0,0,0,4];rank['base_atk']=[1000,990,100,100,100]
    rank['script']=rank['script'][:-2]+[notify(.65,10,4),query(.65),notify(.7,11),query(.7,1)]
    rank['expected_queries']=[dict(time=.65),dict(time=.7)];rank['expected_final']=dict(carriers=[dict(definition=1,recipient_stack_overrides=[3]*5),{},dict(definition=3,recipients=1)])
    rows.append(rank)
    seed=buff(fixed_value=50,max_stack=1)
    gift=buff(name='ranked gift',fixed_value=100,max_stack=1,duration=-1,target='allies_top_atk:1',trigger=dict(timing=['full_charge_fire'],condition=[]))
    add('zero-single-layer-still-affects-recipient-ranking',[seed,op('debuff_stack_remove',1),gift],[notify(0),notify(.5,7),notify(.6,11),query(.6)],base_atk=[1000,1200,100,100,100])
    add('expired-unretired-carrier-still-participates-in-ranking',[buff(fixed_value=50,duration=.5,max_stack=1),copy.deepcopy(gift)],[notify(0),notify(1,11),query(1)],base_atk=[1000,1200,100,100,100])
    for refresh in (False,True):
        seed=buff(duration_bullets=1,max_stack=5,trigger=dict(timing=['full_charge'],condition=[]))
        init=op('buff_stack_init',3,trigger=dict(timing=['full_charge_fire'],condition=[]))
        script=[[0,4,0,0,0,-1,0,0],notify(.1,11),[.25,4,0,0,0,-1,0,0],[.5,4,0,0,0,-1,0,0]]
        if refresh:script.append(notify(.6,10))
        script.append(query(.6))
        c=add('initialized-bullet-lifetime-then-refresh-'+str(refresh),[copy.deepcopy(no_crit),seed,init],script,stack_bullet_reference=True)
        c['combat']['weapons']=[dict(enabled=True,capacity=100,interval=.25,reload=1,coefficient=100)]+[dict(enabled=False) for _ in range(4)]
    return rows
