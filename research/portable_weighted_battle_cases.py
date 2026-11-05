"""Original four Bay stages; incoming patterns are literal, effects untouched."""
import copy,hashlib,json

def fixtures():
    import engine_worker
    from portable_original_identity_inventory import selected_profile_bodies
    from portable_original_incoming_profiles import attack
    rows=[]
    for name,stage,source in selected_profile_bodies(['베이']):
        body=copy.deepcopy(source);body.update(duration=30,seed=4301)
        p=engine_worker.evaluate(dict(body,_portable_static_inputs=True));names=[c['name'] for c in p['chars']]
        nodes=[dict(id='world',kind='idle',until=dict(time=30)),*[attack('incoming-'+str(t),t,100000.,target='slot:5',ignore=True,pierce=True) for t in (.1,4.,10.,14.,19.,25.,29.)]]
        body['enemy']['patterns']=copy.deepcopy(nodes)
        original=[dict(row=i,owner=r['owner'],effect=copy.deepcopy(r['effect'])) for i,r in enumerate(p['effects']) if r['effect'].get('stat')=='received_dmg_split']
        assert len(original)==2 and {r['effect']['target'] for r in original}=={'all_allies','self_cover'}
        rows.append(dict(name=f'weighted-incoming/Bay/favorite-{stage}/30s',body=body,names=names,patterns=nodes,
            allocation=dict(policy='declared-weighted-incoming-v1',caster_weight=8.,other_weight=3.,cover_weight=262.),
            contract=dict(scenario='phases',favorite_stage=stage,definitions=len(p['effects']),original_markers=original,
                original_definitions_sha256=hashlib.sha256(json.dumps(p['effects'],sort_keys=True,ensure_ascii=False).encode()).hexdigest())))
    broken=copy.deepcopy(rows[0]);broken['name']='weighted-incoming/Bay/break-no-revive-reburst/65s';broken['body']['duration']=65
    broken['patterns'][0]['until']['time']=65
    next(p for p in broken['patterns'] if p['id']=='incoming-10.0')['spec']['atk']=5000000.
    broken['patterns'] += [attack('incoming-'+str(t),t,100000.,target='slot:5',ignore=True,pierce=True) for t in (35.,45.,50.,60.)]
    broken['body']['enemy']['patterns']=copy.deepcopy(broken['patterns']);broken['contract']['scenario']='break-no-revive-reburst';rows.append(broken)
    from detail_coverage import body_for
    revived=copy.deepcopy(broken);revived['name']='weighted-incoming/Bay/Biscuit-revive-reburst/65s'
    revived['body']=dict(copy.deepcopy(body_for(['베이','미란다','드레이크','N102','비스킷'],65)),duration=65,seed=4301,burst_gauge_mode='accumulate')
    revived['body']['enemy']['patterns']=copy.deepcopy(revived['patterns'])
    revived['declared_burst_sequence']=[{'1':['미란다'],'2':[second],'3':['드레이크']} for second in ('베이','비스킷','베이')]
    prepared=engine_worker.evaluate(dict(revived['body'],_portable_static_inputs=True));revived['names']=[c['name'] for c in prepared['chars']]
    revived['contract']=dict(scenario='Biscuit-revive-reburst',favorite_stage=0,definitions=len(prepared['effects']),original_markers=[dict(row=i,owner=r['owner'],effect=copy.deepcopy(r['effect'])) for i,r in enumerate(prepared['effects']) if r['effect'].get('stat')=='received_dmg_split'],original_definitions_sha256=hashlib.sha256(json.dumps(prepared['effects'],sort_keys=True,ensure_ascii=False).encode()).hexdigest())
    rows.append(revived)
    inactive=copy.deepcopy(rows[0]);inactive['name']='weighted-incoming/Bay/inactive-transparency/3s';inactive['body']['duration']=3
    inactive['patterns']=inactive['patterns'][:2];inactive['patterns'][0]['until']['time']=3
    inactive['body']['enemy']['patterns']=copy.deepcopy(inactive['patterns']);inactive['contract']['scenario']='inactive';rows.append(inactive)
    return rows
