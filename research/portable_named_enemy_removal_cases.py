"""Literal selected-enemy removal contracts; no compiler or battle in construction."""
import copy
from portable_named_enemy_cases import fixtures as named,BOSS,ADDS,MARK
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant

def fixtures():
    bases=named();rows=[]
    def add(label,base=3,scope='target',remove_mark=False,mark_name=None,payload_owner=0,union=False,count=3):
        c=copy.deepcopy(bases[base]);c['name']='named-enemy-removal-'+label
        c['effects'].pop();c['owners'].pop();c['patterns'][1]['spec']['count']=count
        if mark_name is not None:
            for e in c['effects']:e['name']=mark_name
            c['contract']['mark_name']=mark_name
        name=c['contract']['mark_name'];pool=[BOSS]+[f'__enemy__:wave#{i}' for i in range(1,count+1)]
        marked=copy.deepcopy(c['contract']['present'][0])
        if count!=3:marked=list(pool)
        if union:
            c['effects'].append(field('received_dmg_pct',0,'target',name));c['owners'].append(4);marked=[BOSS,ADDS[0]]
        if not remove_mark:c['effects'].append(field('def_pct',5,'all_enemies','payload'));c['owners'].append(payload_owner)
        removed=name if remove_mark else 'payload'
        c['effects'].append(dict(instant('remove_named_buff',0,'enemies_with_buff:'+name,'named-remove-witness','on_attack'),target_effect=removed,remove_scope=scope));c['owners'].append(0)
        selected=marked or [BOSS];picks=[selected]*3 if not remove_mark else [selected,[BOSS],[BOSS]]
        initial=marked if remove_mark else pool
        gone=initial if scope=='global' else [x for x in initial if x in selected]
        remaining=[x for x in initial if x not in gone]
        c['contract']=dict(kind='remove_named_buff',scope=scope,mark_name=name,removed_name=removed,payload_owner=payload_owner,removed_marker=remove_mark,pool=pool,initial=initial,remaining=remaining,picked=picks,rank_calls=0 if scope=='global' else 3,recipient_calls=0 if scope=='global' else 3,marked=marked,ended=bool(initial and not remaining),global_ignores_target=scope=='global')
        rows.append(c);return c
    for scope in ('target','global'):
        for i,label in enumerate(('missing','boss','add','all')):add(scope+'-'+label,base=i,scope=scope)
    add('opaque-colon-and-spaces',base=2,mark_name=' a:b: 印 ')
    add('empty-selector-name',base=2,mark_name='')
    add('remove-marker-self-one',base=2,remove_mark=True)
    add('remove-marker-self-all',base=3,remove_mark=True)
    add('other-caster-payload',base=2,payload_owner=4)
    add('union-across-casters',base=1,union=True)
    add('all128',count=127)
    add('global-empty-selector-ignored',base=2,scope='global',mark_name='')
    return rows
