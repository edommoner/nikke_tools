"""Shared authored stimuli and independent expected counter quantities."""
import copy

def marker(name='marker',threshold=2,refresh='reset',duration=10,**config):
    value=dict(threshold=threshold,actor=dict(kind='body',identity=0,generation=1),
        families=['weapon','skill','dot'],outcomes=['damaging'],refresh=refresh,on_death=True,attackers='squad',world_scope='physical_actor')
    value.update(config)
    return dict(name=name,source='스킬1',type='buff',stat='target_hit_counter',target='target',max_stack=1,duration=duration,
        target_counter=value,trigger=dict(timing=['battle_start','on_attack'],condition=[]))

# Actions: activate, refresh; hit(family,outcome,kind,id,generation,credit,damage);
# death(kind,id,generation). Expected state: live carriers, credit, completions, epochs.
def cases():
    def hit(f=0,o=2,k=0,i=0,g=1,c=1,d=13,who=None):return ('hit',f,o,k,i,g,c,d)+(() if who is None else (who,))
    def row(name,effects,actions,expected):return dict(name=name,effects=effects,actions=actions,expected=expected)
    yield row('credit-families-outcomes-and-actor-generation', [marker(threshold=2.5,families=['weapon','dot'])],
        [(0,('activate',)),(.1,hit(o=0,c=0,d=0)),(.2,hit(o=1,d=0)),(.3,hit(g=2)),(.4,hit(k=1)),(.5,hit(f=1)),(.6,hit(c=.75)),(.7,hit(f=2,c=1.75)),(.8,('death',0,0,1)),(.9,hit())],
        [(1,0,0,1),(1,0,0,1),(1,0,0,1),(1,0,0,1),(1,0,0,1),(1,0,0,1),(1,.75,0,1),(0,0,1,1),(0,0,1,1),(0,0,1,1)])
    for policy,final_credit in [('reset',1.25),('preserve',0)]:
        yield row('refresh-'+policy,[marker(refresh=policy)],[(0,('activate',)),(.1,hit(c=.75)),(.2,('refresh',)),(.3,hit(c=1.25))],
            [(1,0,0,1),(1,.75,0,1),(1,.75 if policy=='preserve' else 0,0,2),
             (0,0,1,2) if policy=='preserve' else (1,final_credit,0,2)])
    yield row('expiry-does-not-preserve-progress',[marker(refresh='preserve',duration=.2)],
        [(0,('activate',)),(.1,hit(c=.75)),(.2,('refresh',)),(.3,hit(c=1.25))],
        [(1,0,0,1),(1,.75,0,1),(1,0,0,2),(1,1.25,0,2)])
    yield row('death-or-threshold-completes-once',[marker(threshold=100)],
        [(0,('activate',)),(.1,hit(c=3)),(.2,('death',0,0,2)),(.3,('death',0,0,1)),(.4,('death',0,0,1)),(.5,hit(c=100))],
        [(1,0,0,1),(1,3,0,1),(1,3,0,1),(0,0,1,1),(0,0,1,1),(0,0,1,1)])
    nested=marker(threshold=1);nested['trigger']['timing']=['battle_start','event:target_counter_complete:marker'];nested['max_trigger']=2
    yield row('completion-refresh-survives-parent-retirement',[nested],
        [(0,('activate',)),(.1,hit()),(.2,hit()),(.3,hit())],
        [(1,0,0,1),(1,0,1,2),(0,0,2,2),(0,0,2,2)])
    first=marker('first',1);first['trigger']['timing']=['battle_start']
    second=marker('second',1);second['trigger']['timing']=['battle_start','event:target_counter_complete:first'];second['max_trigger']=2
    yield row('siblings-latch-before-child-refresh',[first,second],[(0,('activate',)),(.1,hit()),(.2,hit())],
        [(2,0,0,2),(1,0,2,3),(0,0,3,3)])
    yield row('owner-only-credit',[marker(attackers='owner')],
        [(0,('activate',)),(.1,hit(c=2)),(.2,hit(who=0)),(.3,hit(who=0))],
        [(1,0,0,1),(1,0,0,1),(1,1,0,1),(0,0,1,1)])
    yield row('explicit-blocked-credit-policy',[marker(outcomes=['blocked'])],
        [(0,('activate',)),(.1,hit(c=2)),(.2,hit(o=1,c=.75,d=0)),(.3,hit(o=1,c=1.25,d=0))],
        [(1,0,0,1),(1,0,0,1),(1,.75,0,1),(0,0,1,1)])
    yield row('death-without-reward-retires-the-marker',[marker(on_death=False)],
        [(0,('activate',)),(.1,hit()),(.2,('death',0,0,1)),(.3,hit()),(.4,('refresh',))],
        [(1,0,0,1),(1,1,0,1),(0,0,0,1),(0,0,0,1),(0,0,0,1)])

def clone_cases():return copy.deepcopy(list(cases()))
