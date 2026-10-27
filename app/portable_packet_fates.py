"""Every skill-history row remains present; suppressions have explicit ownership."""
from portable_lock_typed_layout import LOCK_END,OUTPUT,lock_view
MAGIC=0x50463031
HEAD=LOCK_END
FLAGS=HEAD+16
CAPACITY=128
END=FLAGS+CAPACITY

def native_fates(case,trace,dispositions):
    flags=[0]*len(trace)
    for event in dispositions:
        owner=case['names'].index(event['caster'])
        sources=[i for i,e in enumerate(case['effects']) if e.get('type')=='damage' and e.get('name')==event['name'] and case['owners'][i]==owner]
        if 'source_row' in event:
            source=event['source_row']
            if type(source) is not int or source not in sources:raise AssertionError('Suppressed native packet has invalid registration identity')
            sources=[source]
        elif case.get('source_effect_identity'):
            raise AssertionError('Suppressed native packet is missing registration identity')
        if len(sources)!=1:raise AssertionError('Suppressed native packet has ambiguous source identity')
        matches=[i for i,r in enumerate(trace) if r['row']==sources[0] and (r['created'],r['landed'],r['amount'])==(event['created'],event['landed'],event['amount'])]
        if len(matches)!=1 or flags[matches[0]]:raise AssertionError('Suppressed native packet missing/duplicated in complete skill history')
        i=matches[0];r=trace[i]
        if (r['hit'],r['hits'],r['recipients'],r['share'])!=(1,1,[0],r['amount']):raise AssertionError('Unexpected suppressed native BODY proposal')
        flags[i]=1
    return [dict(index=i,disposition='suppressed_native_body' if flag else 'ordinary_world_route',requested_recipients=r['recipients'],actor_effects_allowed=not bool(flag)) for i,(r,flag) in enumerate(zip(trace,flags))]

def compare_and_project(block,native):
    if len(block)!=OUTPUT:raise AssertionError('Complete fate readback required')
    fates=native['receipt_fates'];trace=native['skill_trace']
    if len(fates)!=len(trace) or len(trace)>CAPACITY:raise AssertionError('Fate/history length differs')
    for i,(fate,row) in enumerate(zip(fates,trace)):
        if fate['disposition'] not in ('ordinary_world_route','suppressed_native_body') or fate!=dict(index=i,disposition=fate['disposition'],requested_recipients=row['recipients'],actor_effects_allowed=fate['disposition']=='ordinary_world_route'):raise AssertionError('Invalid complete packet fate contract')
    flags=[int(r['disposition']=='suppressed_native_body') for r in fates];count=sum(flags)
    if list(block[HEAD:FLAGS])!=[MAGIC,count,count,count]+[0]*12:raise AssertionError('Suppressed packet queue/disposition counters differ')
    if list(block[FLAGS:END])!=flags+[0]*(CAPACITY-len(flags)):raise AssertionError('Complete packet fate vector differs')
    if any(block[END:]):raise AssertionError('Unowned fate tail contains data')
    # All new bank words were checked above. The old arena projector keeps its
    # original strict tail rule and sees exactly its original word ownership.
    projection=list(block[:HEAD])+[0]*(OUTPUT-HEAD)
    return lock_view(projection)

def shader_layout():
    return '// Generated from portable_packet_fates.py.\n'+''.join('static const uint PF_'+k+' = '+str(v)+'U;\n' for k,v in dict(HEAD=HEAD,FLAGS=FLAGS,CAPACITY=CAPACITY,END=END,MAGIC=MAGIC).items())

def check(root):
    from pathlib import Path
    if END>OUTPUT or (Path(root)/'gpu/packet_fates_layout.slang').read_text()!=shader_layout():raise ValueError('Packet fate layout differs')
