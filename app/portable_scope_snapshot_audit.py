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
    return dict(schema=1,generated_scope_snapshot_verified=True,targets=result,gpu_calls=0,calculation_verified=False)
