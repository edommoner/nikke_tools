"""External-event capacity contracts, not a spatial/full-profile approximation."""
import copy
from portable_heavyarms_lock_cases import source_definitions

def query(t,index,who=0,name='록 온',base=5,limit=128):
    return dict(op='named_target_count',time=t,who=who,marker=name,base_count=base,capacity_limit=limit,index=index)

def fixtures():
    effect=copy.deepcopy(source_definitions()[20]);effect.update(duration=.5,duration_bullets=-1)
    effect['trigger']=dict(timing=['battle_start'],condition=[])
    start=[0,0,0,0,0,-1,0,0];attack=[.3,0,7,0,0,-1,0,0]
    rows=[]
    def add(name,effects,script):rows.append(dict(name='named-target-count/'+name,effects=effects,owners=[0]*len(effects),script=script))
    add('exact-expiry',[effect],[start,query(0,0),query(.499,1),query(.5,2)])
    e=dict(effect,target='all_allies')
    add('allied-and-name-filter',[e],[start,query(.1,0,who=4),query(.1,1,name='other')])
    e=copy.deepcopy(effect);e['trigger']['timing']=['on_attack'];e['max_stack']=3
    add('ordered-stacks',[e],[[0,0,7,0,0,-1,0,0],query(.1,0),attack,query(.3,1),[.4,0,7,0,0,-1,0,0],query(.4,2),query(.9,3)])
    other=copy.deepcopy(effect);other.update(name='other-capacity',target_effect='other',fixed_value=3)
    add('independent-markers',[effect,other],[start,query(.1,0),query(.1,1,name='other'),query(.1,2,who=1)])
    e=copy.deepcopy(effect);e['trigger']['timing']=['battle_start','on_attack']
    add('refresh-before-expiry',[e],[start,query(.1,0),attack,query(.6,1)])
    removal=dict(name='remove-count',source='스킬1',type='instant',stat='remove_named_buff',target='self',target_effect=effect['name'],trigger=dict(timing=['on_attack'],condition=[]))
    add('named-removal',[effect,removal],[start,query(.1,0),attack,query(.3,1)])
    return copy.deepcopy(rows)

def native(case):
    from test_target_counter_runtime import manager,NAMES
    from effect_target_count_policy import MODEL,query as read
    bm=manager(case['effects'],case['owners']);rows=[]
    for command in case['script']:
        t=command['time'] if isinstance(command,dict) else command[0];bm.tick(t)
        if isinstance(command,dict):
            q=read(bm,NAMES[command['who']],command['marker'],t,base_count=command['base_count'],capacity_limit=command['capacity_limit'],model=MODEL)
            rows.append(dict(time=float(t),who=command['who'],marker=command['marker'],base_count=command['base_count'],capacity_limit=command['capacity_limit'],capacity=q['capacity'],additional_targets=q['additional_targets']))
        else:bm.notify({0:'battle_start',7:'on_attack'}[command[2]],t,NAMES[command[3]])
    return dict(queries=rows)
