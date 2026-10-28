"""Reject generated actor query scopes that reload an overwritten buffer value."""
import hashlib,re


def function(text,prefix):
    match=re.search(r'\b('+prefix+r'_\d+)\([^;{}]*\)\s*\{',text)
    if not match:raise ValueError('Missing generated scope snapshot function: '+prefix)
    start=match.end();depth=1;end=start
    while end<len(text) and depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    if depth:raise ValueError('Incomplete generated scope function')
    return match.group(1),text[start:end-1],text[max(0,match.start()-80):match.start()]


def audit(cuda,metal):
    result={}
    for target,raw in [('cuda',cuda),('metal',metal)]:
        text=raw.decode();helper,read,annotation=function(text,'actorStateQueryScopeSnapshot');name,body,_=function(text,'actorStatePushQuery')
        if target=='cuda' and '__noinline__' not in annotation:raise ValueError('CUDA scalar snapshot must remain noinline')
        stores=list(re.finditer(r'(?m)^\s*\*[^;\n]+?\s*=\s*[^;\n]+;',body))
        call=re.search(r'\buint\s+(\w+)\s*=\s*'+helper+r'\([^;]+;',body)
        if len(stores)!=1 or not call:raise ValueError('Scope previous value is not materialized before its store')
        returned=re.search(r'\breturn\s+'+re.escape(call.group(1))+r'\s*;',body)
        if not returned or not call.end()<=stores[0].start()<stores[0].end()<=returned.start():raise ValueError('Scope snapshot/store/return order is invalid')
        if re.search(r'(?m)^\s*\*[^;\n]+?\s*=',read):raise ValueError('Snapshot helper must only read')
        result[target]=dict(function=name,snapshot=helper,sha256=hashlib.sha256(raw).hexdigest(),value_before_store=True)
    answer=dict(schema=1,generated_scope_snapshot_verified=True,targets=result,gpu_calls=0,calculation_verified=False)
    if b'stagedScopeSnapshot_' in cuda or b'stagedScopeSnapshot_' in metal:answer['staged']=audit_staged(cuda,metal)
    if b'findCarrier_' in cuda or b'findCarrier_' in metal:answer['resident_scalars']=audit_resident_scalars(cuda,metal)
    return answer


def audit_resident_scalars(cuda,metal):
    """Guard the two observed CUDA lvalue reloads across resident writes.

    Exact source inverses and this generated publication check are distinct
    from arithmetic/native/GPU comparison. No code is rewritten by the audit.
    """
    targets={}
    for target,raw in [('cuda',cuda),('metal',metal)]:
        text=raw.decode();facts={}
        for helper,consumer,field,kind in [('bodyHPBeforeHeal','dispatch','hp','healing'),('carrierCountBeforeAllocate','findCarrier','carrierCount','carrier')]:
            reader,read,annotation=function(text,helper);name,body,_=function(text,consumer)
            if target=='cuda' and '__noinline__' not in annotation:raise ValueError('Resident scalar reader must remain noinline')
            if re.search(r'(?:->|\.)\w+(?:\[[^;\n]+?\])?\s*=(?!=)',read) or re.search(r'(?m)^\s*\*[^;\n]+?\s*=',read):raise ValueError('Resident snapshot reader writes state')
            if not re.search(r'\breturn\s+[^;]*'+field+r'_\d+',read):raise ValueError('Resident snapshot must read the original field')
            calls=list(re.finditer(r'\b(?:uint|ulonglong|ulong)\s+(\w+)\s*=\s*'+reader+r'\([^;]+;',body))
            if len(calls)!=1:raise ValueError('One materialized scalar snapshot required')
            call=calls[0];value=re.escape(call.group(1));tail=body[call.end():]
            if kind=='healing':
                mutate=re.search(r'\bstorageBodyHeal_\d+\([^;]+;',tail)
                store=re.search(r'->hp_\d+\[[^;\n]+?\]\s*=\s*[^;]+;',tail)
                account=re.search(r'->healing_\d+\[[^;\n]+?\]\s*=\s*[^;]+;',tail)
                sync=re.search(r'\bsyncHealthActor_\d+\([^;]+;',tail)
                if not all((mutate,store,account,sync)) or not mutate.end()<=store.start()<account.start()<sync.start():raise ValueError('Healing snapshot/mutation/accounting order changed')
                if not re.search(r'\b'+value+r'\s*\^\s*9223372036854775808(?:ULL|UL)?\b',account.group()):raise ValueError('Healing accounting reloads overwritten HP')
            else:
                mutate=re.search(r'->carrierCount_\d+\s*=\s*'+value+r'\s*\+\s*1U?\s*;',tail)
                store=re.search(r'->carrierDefinition_\d+\[\s*'+value+r'\s*\]\s*=',tail)
                returned=re.search(r'\breturn\s+'+value+r'\s*;',tail)
                if not all((mutate,store,returned)) or not mutate.end()<=store.start()<returned.start():raise ValueError('Carrier allocation does not retain the pre-increment slot')
            facts[kind]=dict(reader=reader,consumer=name,scalar_before_write=True)
        targets[target]=dict(sha256=hashlib.sha256(raw).hexdigest(),**facts)
    return dict(schema=1,generated_resident_scalars_verified=True,targets=targets,gpu_calls=0,calculation_verified=False)


def audit_staged(cuda,metal):
    """Reject the observed resident staged-scope dead-store failure before GPU use.

    This verifies generated publication order, not numerical battle equivalence.
    """
    targets={}
    for target,raw in [('cuda',cuda),('metal',metal)]:
        text=raw.decode();helper,reader,annotation=function(text,'stagedScopeSnapshot');name,body,_=function(text,'stagedPass')
        if target=='cuda' and '__noinline__' not in annotation:raise ValueError('Staged scalar snapshot must remain noinline')
        if re.search(r'(?m)^\s*\*[^;\n]+?\s*=',reader):raise ValueError('Staged snapshot helper must only read')
        calls=list(re.finditer(r'\buint\s+(\w+)\s*=\s*'+helper+r'\([^;]+;',body))
        dispatch=re.search(r'\bdispatch_\d+\([^;]+;',body)
        if len(calls)!=4 or dispatch is None or calls[-1].end()>dispatch.start():raise ValueError('Four staged snapshots required before dispatch')
        stores=list(re.finditer(r'(?m)^\s*\*[^;\n]+?\s*=\s*([^;\n]+);',body))
        published=[m for m in stores if calls[-1].end()<m.start()<dispatch.start()]
        restored=[m for m in stores if m.start()>dispatch.end()]
        if len(published)!=4 or len(restored)!=4 or [m.group(1).strip() for m in restored]!=[m.group(1) for m in calls]:raise ValueError('Staged scope must publish and restore every word across dispatch')
        targets[target]=dict(function=name,snapshot=helper,published_words=4,restored_words=4,sha256=hashlib.sha256(raw).hexdigest())
    return dict(schema=1,generated_staged_scope_verified=True,targets=targets,gpu_calls=0,calculation_verified=False)


def audit_resident_appends(cuda,metal):
    """Each stored index uses the count before increment, on both targets."""
    targets={}
    for target,raw in [('cuda',cuda),('metal',metal)]:
        text=raw.decode();facts=[]
        for consumer,array,count in [('markEntry','enemyBuffRows','enemyBuffCount'),('markEntry','infiniteRows','infiniteRowCount'),('initializeHPWatches','hpWatchSlots','hpWatchCount')]:
            name,body,_=function(text,consumer)
            updates=list(re.finditer(r'(\w+)->('+count+r'_\d+)\s*=\s*\1->\2\s*\+\s*1U?\s*;',body))
            stores=list(re.finditer(r'(\w+)->'+array+r'_\d+\[([^;\n]+?)\]\s*=\s*[^;\n]+;',body))
            if len(updates)!=1 or not stores:raise ValueError('One known resident append required: '+array)
            increment=updates[0];store=stores[-1];base,field=increment.group(1,2);index=store.group(2).strip()
            if store.group(1)!=base:raise ValueError('Resident append changes storage owner')
            if index==base+'->'+field:
                if store.end()>increment.start():raise ValueError('Resident append uses incremented count: '+array)
                mode='store-before-increment'
            else:
                snapshots=list(re.finditer(r'\buint\s+'+re.escape(index)+r'\s*=\s*'+re.escape(base+'->'+field)+r'\s*;',body))
                if len(snapshots)!=1 or not snapshots[0].end()<=increment.start()<store.start():raise ValueError('Resident append lost scalar index: '+array)
                mode='scalar-before-increment'
            facts.append(dict(function=name,array=array,count=count,index_policy=mode))
        targets[target]=dict(sha256=hashlib.sha256(raw).hexdigest(),appends=facts)
    return dict(schema=1,generated_resident_appends_verified=True,targets=targets,gpu_calls=0,calculation_verified=False)
