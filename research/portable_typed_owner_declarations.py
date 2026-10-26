"""Two explicit audit effects after, and separate from, all original definitions."""
import copy

def declarations(case,original):
    rows=case.get('declared_owner_counter',[])
    if not rows:return []
    from coordinate_typed_actor_policy import FIELD_MODE
    if case.get('typed_actor_policy')!={'mode':FIELD_MODE} or len(rows)!=2:raise ValueError('Declared owner audit requires its two effects and owner policy')
    marker,field=rows
    if marker.get('stat')!='target_hit_counter' or field.get('type')!='buff' or field.get('target')!='target' or field.get('trigger',{}).get('timing')!=['event:target_counter_complete:'+marker.get('name','')]:raise ValueError('Declared owner audit must use a real counter completion field')
    if marker.get('name') in {r['effect']['name'] for r in original} or field.get('name') in {r['effect']['name'] for r in original}:raise ValueError('Declared owner audit cannot shadow an original definition')
    return [(copy.deepcopy(e),case['names'][0]) for e in rows]
