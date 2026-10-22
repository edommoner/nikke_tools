"""Read-only direct-call topology, not a PTX partitioner or compiler predictor.

PTX 8.4 call syntax: https://docs.nvidia.com/cuda/archive/12.4.1/parallel-thread-execution/index.html#control-flow-instructions-call
Indirect calls remain explicit gaps, even with a calltargets/prototype operand.
"""
from collections import Counter
import hashlib,re
from portable_ptx_stats import function_records,_declarations,_close,_SYMBOL,_TYPE

_CALL=re.compile(r'(?<![\w.])(call(?:\.[A-Za-z0-9_]+)*)\s+([^;]*);')


def _operands(text):
    result=[];start=0;depth=0
    for i,char in enumerate(text):
        if char=='(':depth+=1
        elif char==')':
            depth-=1
            if depth<0:raise ValueError('Unbalanced PTX call operands')
        elif char==',' and depth==0:result.append(text[start:i].strip());start=i+1
    if depth:raise ValueError('Unbalanced PTX call operands')
    result.append(text[start:].strip())
    if any(not s for s in result):raise ValueError('Empty PTX call operand')
    return result


def _named_registers(text):
    names=set()
    pattern=r'\.reg\s+(?:\.align\s+\d+\s+)?(?:\.v[24]\s+)?\.'+_TYPE+r'\s+([^;)]+)'
    for match in re.finditer(pattern,text):
        for element in match.group(1).split(','):
            item=re.fullmatch(r'\s*('+_SYMBOL+r')(?:<([1-9][0-9]*)>)?\s*',element)
            if item:
                name,count=item.groups();names.add(name)
                if count:
                    # Range registers with % are recognized without expanding
                    # potentially huge declarations. Named ranges get a prefix.
                    names.add((name,int(count)))
    return names


def _is_register(name,registers):
    if name.startswith('%') or name in registers:return True
    for declaration in registers:
        if isinstance(declaration,tuple):
            prefix,count=declaration;suffix=name[len(prefix):] if name.startswith(prefix) else ''
            if suffix.isdigit() and int(suffix)<count:return True
    return False


def _components(graph):
    """Iterative Kosaraju: no recursion budget depends on module function count."""
    seen=set();order=[]
    for root in sorted(graph):
        if root in seen:continue
        stack=[(root,False)]
        while stack:
            node,done=stack.pop()
            if done:order.append(node);continue
            if node in seen:continue
            seen.add(node);stack.append((node,True))
            stack.extend((child,False) for child in sorted(graph[node],reverse=True) if child not in seen)
    reverse={n:set() for n in graph}
    for node,children in graph.items():
        for child in children:reverse[child].add(node)
    seen=set();groups=[]
    for root in reversed(order):
        if root in seen:continue
        group=[];stack=[root]
        while stack:
            node=stack.pop()
            if node in seen:continue
            seen.add(node);group.append(node);stack.extend(reverse[node]-seen)
        groups.append(sorted(group))
    return sorted(groups,key=lambda g:(-len(g),g))


def callgraph_statistics(raw):
    records=list(function_records(raw));definitions={};prototypes=set()
    for record in records:
        if record['body'] is None:prototypes.add(record['name']);continue
        name=record['name']
        if name in definitions:raise ValueError('Duplicate PTX function definition: '+name)
        definitions[name]=record
    if not definitions:raise ValueError('No PTX function definitions found')
    graph={name:set() for name in definitions};rows=[];indirect_total=0;unknown=set();externals=set()
    for name,record in definitions.items():
        body=record['body'];registers=_named_registers(record['header']+'\n'+body)
        virtual,local=_declarations(body);direct=Counter();external=Counter();unresolved=Counter();indirect=[]
        calls=list(_CALL.finditer(body))
        if len(calls)!=len(re.findall(r'(?<![\w.])call(?:\.[A-Za-z0-9_]+)*\b',body)):
            raise ValueError('Unterminated or unsupported PTX call instruction')
        for call in calls:
            if call.group(1) not in ('call','call.uni'):raise ValueError('Unsupported PTX call modifier')
            args=_operands(call.group(2));index=1 if args[0].startswith('(') else 0
            for operand in args:
                if operand.startswith('(') and _close(operand,0,'(',')')!=len(operand):raise ValueError('Unsupported PTX call parameter list')
            if index>=len(args) or re.fullmatch(_SYMBOL,args[index]) is None:raise ValueError('Unsupported PTX call target')
            target=args[index];tail=args[index+1:]
            if len(tail)>2 or (tail and not tail[0].startswith('(') and len(tail)!=1):raise ValueError('Unsupported PTX call operands')
            if _is_register(target,registers):
                if not tail or tail[-1].startswith('(') or re.fullmatch(_SYMBOL,tail[-1]) is None:raise ValueError('Indirect PTX call requires target list or prototype')
                indirect.append(dict(line=record['line']+record['header'].count('\n')+body[:call.start()].count('\n'),has_target_list_or_prototype=bool(tail and not tail[-1].startswith('('))))
            elif len(tail)>1 or (tail and not tail[0].startswith('(')):
                # An unrecognized named pointer must not become a direct edge.
                unresolved[target]+=1
            elif target in definitions:direct[target]+=1;graph[name].add(target)
            elif target in prototypes:external[target]+=1
            else:unresolved[target]+=1
        loads=Counter(re.findall(r'(?<![\w.])((?:ld|st)(?:\.[A-Za-z0-9_]+)+)\s',body))
        row=dict(name=name,kind=record['kind'],line=record['line'],lines=record['lines'],definition_sha256=record['definition_sha256'],virtual_register_count=sum(virtual.values()),declared_local_bytes=local,
                 direct_calls=dict(sorted(direct.items())),external_calls=dict(sorted(external.items())),unresolved_calls=dict(sorted(unresolved.items())),indirect_calls=indirect,load_store_opcodes=dict(sorted(loads.items())))
        rows.append(row);indirect_total+=len(indirect);unknown.update(unresolved);externals.update(external)
    roots=[r['name'] for r in rows if r['kind']=='entry']
    # These are reachable definitions under direct edges only, not legal link
    # units: parameter ABI, global/constant ownership and tool support are unproved.
    closure=[]
    for root in roots:
        reached=set();stack=[root]
        while stack:
            node=stack.pop()
            if node in reached:continue
            reached.add(node);stack.extend(graph[node]-reached)
        closure.append(dict(entry=root,defined_function_count=len(reached),functions=sorted(reached)))
    components=_components(graph)
    cyclic=[g for g in components if len(g)>1 or g[0] in graph[g[0]]]
    return dict(schema=1,ptx_sha256=hashlib.sha256(raw).hexdigest(),functions=len(rows),function_rows=rows,entry_closures=closure,
                strongly_connected_components=components,cyclic_components=cyclic,indirect_call_count=indirect_total,external_symbols=sorted(externals),unresolved_symbols=sorted(unknown),
                direct_graph_complete=not (indirect_total or unknown or externals),partition_legal_verified=False,compiler_memory_attribution_verified=False,compiler_verified=False,calculation_verified=False,
                scope='Lexical direct-call graph and declaration/instruction counts only. Indirect/external/unresolved calls remain gaps; no PTX body, source rewriting, compile, link, driver or GPU execution.')
