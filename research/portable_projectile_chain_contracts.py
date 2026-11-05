"""Literal handler-completion order, quantities and ordinary carrier semantics."""
from collections import Counter
AMOUNTS={
'plain':[900],'three-packets-one-notice':[900]*3,'zero-hit-count':[],'negative-hit-count':[],'zero-coefficient':[],'empty-name':[900],
'attachment-factor':[1800],'explosion-factor':[1800],'matching-normal-MG-annotation':[900],'mismatched-normal-annotation':[900],
 'two-casts':[900]*2,'exact-literal-name':[900],'other-caster-listener':[900],'nested-handler-order':[900,450,225],
'buff-kind-self-carrier':[900,900,90],'buff-kind-enemy-carrier':[900,900,90],'instant-kind-stack-operation':[900],
'periodic-handler':[900]*3,'empty-accumulation-early-return':[],'parent-fixed-early-return':[],
'named-multiplier-zero-still-notifies':[1],'per-hit-child-before-completion':[900,900,1900],
'instant-target-does-not-select-buff-carrier':[900],'all-projectiles-missing-reference':[],'physical-hits-are-not-handler-completions':[900]*4,'normal-MG-attachment-factor':[1800]}

def verify(case,native):
    data=native['projectile_chain'];events=data['events'];handlers=[e for e in events if e['kind']=='handler'];notices=[e for e in events if e['kind']=='weapon-hit'];packets=[e for e in events if e['kind']=='packet'];ops=[e for e in events if e['kind']=='instant-stack-op']
    assert all(e['sequence']==i for i,e in enumerate(events))
    assert all(n['handler'] in {h['sequence'] for h in handlers} for n in notices)
    for h in handlers:
        owned=[e for e in notices if e['handler']==h['sequence']];assert len(owned)<=1
        if owned:
            n=owned[0];assert n['name']==h['name'] and n['owner']==h['owner'] and n['time']==h['time']
            before=[e['sequence'] for e in events if e.get('handler')==h['sequence'] and e['kind'] in ('packet','named-hit')]
            assert max([h['sequence']]+before)<n['sequence']<h['returned_sequence']
            assert n['returned_sequence']<=h['returned_sequence']
    if 'body' in case:
        assert len(data['definitions'])==87
        owner0=lambda rows:[e for e in rows if e['owner']==0]
        expected={} if case['contract']['duration']==3 else {'부착형 유탄 4':16,'유탄 폭발':1,'유탄 즉발 폭발':9}
        assert dict(Counter(e['name'] for e in owner0(notices)))==expected
        assert dict(Counter(e['name'] for e in owner0(handlers)))==({} if not expected else dict(expected,**{'계승되는 힘 4':1}))
        assert not owner0(ops)
        original=[p for p in data['final_carriers'] if p['owner']==0]
        assert [(p['name'],p['stat'],p['stack'],p['recipients']) for p in original]==([] if not expected else [('유탄','buff_stack_add',6,['__enemy__'])])
        attached=[h for h in owner0(handlers) if h['stat']=='projectile_attachment_damage']
        assert all(h['declared_weapon']==h['base_weapon']=='MG' and h['is_normal'] for h in attached)
        return dict(verified=True,reference_model_gap=False,declared_model=True,in_game_rules_verified=False,original_profile=True,definitions=87,completion_notifications=len(owner0(notices)),attached_handlers=len(attached),buff_kind_instant_dispatches=0)
    kind=case['contract']['kind'];assert [e['amount'] for e in packets]==AMOUNTS[kind],(kind,[e['amount'] for e in packets])
    expected=['source']
    if kind in ('zero-coefficient','empty-name','empty-accumulation-early-return','parent-fixed-early-return','all-projectiles-missing-reference','physical-hits-are-not-handler-completions'):expected=[]
    elif kind=='two-casts':expected=['source']*2
    elif kind=='periodic-handler':expected=['source']*3
    elif kind=='exact-literal-name':expected=['source: 부착 ']
    elif kind=='nested-handler-order':expected=['source','child','grandchild']
    elif kind in ('buff-kind-self-carrier','buff-kind-enemy-carrier'):expected=['source','source','threshold']
    elif kind=='per-hit-child-before-completion':expected=['source','completion-child']
    assert [e['name'] for e in notices]==expected,(kind,[e['name'] for e in notices])
    carriers=data['final_carriers']
    if kind in ('buff-kind-self-carrier','buff-kind-enemy-carrier'):
        assert len(carriers)==1 and carriers[0]['stat']=='buff_stack_add' and carriers[0]['stack']==2
        from world_frame_native import roster_names
        assert carriers[0]['recipients']==(['__enemy__'] if kind=='buff-kind-enemy-carrier' else [roster_names(case)[0]])
        assert not ops
    elif kind in ('instant-kind-stack-operation','instant-target-does-not-select-buff-carrier'):
        assert len(carriers)==1 and carriers[0]['stat']=='' and carriers[0]['stack']==3 and len(ops)==1
    else:assert not ops
    if kind=='other-caster-listener':assert not carriers
    if kind=='exact-literal-name':assert [p['name'] for p in carriers]==['heard']
    if kind in ('zero-hit-count','negative-hit-count'):assert handlers[0]['hit_count']==(0 if kind=='zero-hit-count' else -1) and len(carriers)==1
    if kind in ('matching-normal-MG-annotation','mismatched-normal-annotation','normal-MG-attachment-factor'):
        assert handlers[0]['base_weapon']==handlers[0]['current_weapon']=='MG' and handlers[0]['is_normal']
        assert packets[0]['tag']=='normal_skill'
    if kind=='nested-handler-order':assert handlers[-1]['returned_sequence']==handlers[0]['returned_sequence']
    if kind=='per-hit-child-before-completion':
        assert [e['name'] for e in events if e['kind']=='named-hit']==['source','source','completion-child']
        assert max(e['sequence'] for e in events if e['kind']=='named-hit' and e['name']=='source')<notices[0]['sequence']<handlers[-1]['sequence']
    return dict(verified=True,declared_model=True,in_game_rules_verified=False,reference_model_gap=bool(case['contract'].get('reference_model_gap')),handler_calls=len(handlers),notices=len(notices),packets=len(packets),ordinary_buff_carrier=kind.startswith('buff-kind-'))
