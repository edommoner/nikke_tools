"""CPU-only byte/ABI/ownership checks for a two-unit diagnostic PTX candidate.

This constructs new experimental sources; it never compiles, links, or edits
saved PTX/cache. The existing unchanged-source assembler is not an entry point.
Link rules: PTX8.4 section11.6 (one visible definition for an extern symbol).
"""
import hashlib,json,re
from pathlib import Path
from portable_ptx_stats import function_records,load_saved_ptx,_COMMENTS,_SYMBOL,_TYPE,_close,ptx_statistics
from portable_ptx_callgraph import callgraph_statistics,_operands


def sha(raw):return hashlib.sha256(raw).hexdigest()


def _signature(record):
    header=record['header'].strip()
    linkage=re.match(r'(?:(?:\.(?:visible|weak|extern))\s+)*',header).group()
    if '.weak' in linkage:raise ValueError('Weak function ownership is unsupported')
    header=header[len(linkage):];kind='.'+record['kind']
    if not header.startswith(kind):raise ValueError('Function kind mismatch')
    at=len(kind)
    while at<len(header) and header[at].isspace():at+=1
    returns=''
    if at<len(header) and header[at]=='(':
        end=_close(header,at,'(',')');returns=header[at+1:end-1];at=end
    name=re.match(r'\s*('+_SYMBOL+r')',header[at:])
    if name is None or name[1]!=record['name']:raise ValueError('Function symbol mismatch')
    at+=name.end()
    while at<len(header) and header[at].isspace():at+=1
    inputs=''
    if at<len(header) and header[at]=='(':
        end=_close(header,at,'(',')');inputs=header[at+1:end-1];at=end
    suffix=header[at:].strip()
    # Entry launch attributes remain verbatim in the remainder. Device function
    # attributes need an explicit prototype conversion before admitting them.
    if record['kind']=='func' and suffix:raise ValueError('Unsupported device function attribute')
    def parameters(text):
        result=[]
        for param in _operands(text) if text.strip() else []:
            m=re.fullmatch(r'\s*\.(param|reg)\s+(?:\.align\s+([1-9][0-9]*)\s+)?\.('+_TYPE+r')\s+'+_SYMBOL+r'((?:\s*\[\s*[1-9][0-9]*\s*\])*)\s*',param)
            if m is None:raise ValueError('Unsupported PTX parameter ABI')
            space,align,typ,dims=m.groups();result.append((space,int(align) if align else None,typ,tuple(map(int,re.findall(r'\d+',dims)))))
        return result
    return dict(kind=record['kind'],returns=parameters(returns),inputs=parameters(inputs)),header,linkage


def _module_state(source,records,allow_external=False):
    code=_COMMENTS.sub(lambda m:''.join('\n' if c=='\n' else ' ' for c in m.group()),source)
    chars=list(code)
    for record in records:
        chars[record['start']:record['end']]=' '*(record['end']-record['start'])
    code=''.join(chars);at=0;directives={};globals_=[]
    while at<len(code):
        while at<len(code) and (code[at].isspace() or code[at]==';'):at+=1
        if at==len(code):break
        directive=re.match(r'\.(version|target|address_size)\s+([^\n]+)',code[at:])
        if directive:
            key,value=directive.groups();value=value.strip()
            if key in directives:raise ValueError('Duplicate PTX module directive')
            if key=='version' and re.fullmatch(r'\d+\.\d+',value) is None:raise ValueError('Unsupported PTX version')
            if key=='address_size' and value not in ('32','64'):raise ValueError('Unsupported PTX address size')
            if key=='target' and re.fullmatch(r'sm_\d+(?:\s*,\s*[A-Za-z0-9_]+)*',value) is None:raise ValueError('Unsupported PTX target')
            directives[key]=source[at:at+directive.end()].strip();at+=directive.end();continue
        declaration=re.match(r'(?P<link>(?:(?:\.visible|\.extern|\.weak|\.common)\s+)*)\.(?P<space>global|const)\s+(?:\.align\s+(?P<align>[1-9][0-9]*)\s+)?\.(?P<type>'+_TYPE+r')\s+(?P<name>'+_SYMBOL+r')(?P<dims>(?:\s*\[\s*[1-9][0-9]*\s*\])*)\s*(?:=(?P<init>[^;]*))?;',code[at:],re.S)
        if declaration is None:raise ValueError('Unsupported PTX module state or directive at character '+str(at))
        d=declaration.groupdict()
        if d['link'].strip() not in ('','.visible') and not (allow_external and d['link'].strip()=='.extern'):raise ValueError('External/weak/common state ownership is unsupported')
        if '.extern' in d['link'] and d['init'] is not None:raise ValueError('External state has an initializer')
        if d['type']=='pred':raise ValueError('Unsupported module predicate storage')
        if any(row['name']==d['name'] for row in globals_):raise ValueError('Duplicate PTX module state symbol')
        end=at+declaration.end();raw=source[at:end].strip()
        # Only the linkage is removed; the declaration, initialization and all
        # symbol references remain byte-for-byte in the sole owner unit.
        original_linkage=source[at:at+len(d['link'])]
        bare=raw[len(original_linkage):] if original_linkage else raw
        globals_.append(dict(name=d['name'],space=d['space'],alignment=int(d['align']) if d['align'] else None,type=d['type'],dimensions=list(map(int,re.findall(r'\d+',d['dims']))),raw=raw,bare=bare,external='.extern' in d['link'],has_initializer=d['init'] is not None,sha256=sha(raw.encode())))
        at=end
    if set(directives)!=set(('version','target','address_size')):raise ValueError('Missing PTX module directives')
    return directives,globals_


def partition_candidate(raw,focus=None):
    source=raw.decode('utf-8').rstrip('\0');records=list(function_records(raw));graph=callgraph_statistics(raw)
    if not graph['direct_graph_complete']:raise ValueError('Partition requires closed direct-call graph')
    definitions={r['name']:r for r in records if r['body'] is not None}
    if focus is None:focus=ptx_statistics(raw)['max_virtual_function']['name']
    if focus not in definitions or definitions[focus]['kind']!='func':raise ValueError('Focus must be a defined device function')
    signatures={};headers={};linkages={}
    for record in records:
        sig,header,linkage=_signature(record);name=record['name']
        if record['body'] is not None and '.extern' in linkage:raise ValueError('Extern function has a body')
        if name in signatures and signatures[name]!=sig:raise ValueError('Prototype ABI differs from definition: '+name)
        signatures[name]=sig
        if record['body'] is not None or name not in headers:headers[name]=header;linkages[name]=linkage
    if set(signatures)!=set(definitions):raise ValueError('Undefined function declarations are not supported')
    directives,globals_=_module_state(source,records)
    collisions=set(definitions)&{g['name'] for g in globals_}
    if collisions:raise ValueError('Function and state symbols collide')
    byname={r['name']:r for r in graph['function_rows']}
    focus_imports=set(byname[focus]['direct_calls'])-{focus}
    exported={focus}|focus_imports
    # Every global/const definition has one owner (remainder), even if only
    # focus references it. Never duplicate immutable constants across units.
    preamble='\n'.join(directives[k] for k in ('version','target','address_size'))+'\n\n'
    focus_state=[];remainder_state=[]
    for state in globals_:
        decl=state['bare'];uninitialized='.'+state['space']+(' .align '+str(state['alignment']) if state['alignment'] else '')+' .'+state['type']+' '+state['name']+''.join('['+str(d)+']' for d in state['dimensions'])+';'
        focus_state.append('.extern '+uninitialized)
        remainder_state.append('.visible '+decl)
    units={};body_rows=[]
    for unit,owned,state in (('focus',{focus},focus_state),('remainder',set(definitions)-{focus},remainder_state)):
        chunks=[preamble]
        # Emit complete prototypes first so source order is not a call-order
        # dependency; parameter names/types/align/array extents come from defs.
        for name,record in definitions.items():
            if record['kind']!='func':continue
            prefix='.extern ' if name not in owned else '.visible ' if name in exported else '.visible ' if '.visible' in linkages[name] else ''
            if name in owned or (unit=='focus' and name in focus_imports) or (unit=='remainder' and name==focus):chunks.append(prefix+headers[name]+';\n')
        chunks.extend(['\n','\n'.join(state),'\n'])
        for name,record in definitions.items():
            if name not in owned:continue
            body=source[record['body_start']:record['end']]
            prefix='.visible ' if name in exported or '.visible' in linkages[name] else ''
            chunks.append(prefix+headers[name]+'\n'+body+'\n')
            body_rows.append(dict(name=name,owner=unit,body_sha256=sha(body.encode()),abi=signatures[name]))
        units[unit+'.ptx']=''.join(chunks).encode()
    # Reparse both candidate units, proving body coverage and ABI retention.
    seen={}
    for unit,data in units.items():
        unit_records=list(function_records(data));unit_source=data.decode()
        unit_directives,unit_state=_module_state(unit_source,unit_records,allow_external=True)
        if unit_directives!=directives or {g['name'] for g in unit_state}!={g['name'] for g in globals_}:raise ValueError('Candidate module ownership changed')
        for state,original in zip(unit_state,globals_,strict=True):
            for key in ('name','space','alignment','type','dimensions'):
                if state[key]!=original[key]:raise ValueError('Candidate state ABI changed')
            if unit=='focus.ptx':
                if not state['external'] or state['has_initializer']:raise ValueError('Focus duplicated state definition')
            elif state['external'] or state['bare']!=original['bare']:raise ValueError('Remainder state definition changed')
        for record in unit_records:
            sig,_,_=_signature(record)
            if sig!=signatures[record['name']]:raise ValueError('Candidate ABI changed')
            if record['body'] is not None:
                if record['name'] in seen:raise ValueError('Candidate function has duplicate owners')
                text=data.decode();seen[record['name']]=sha(text[record['body_start']:record['end']].encode())
    if seen!={row['name']:row['body_sha256'] for row in body_rows}:raise ValueError('Candidate lost or changed function bodies')
    report=dict(schema=1,purpose='cpu-checked-ptx-partition-candidate',input_sha256=sha(raw),focus=focus,definitions=len(definitions),function_bodies=body_rows,global_state=[{k:v for k,v in g.items() if k not in ('raw','bare')}|dict(owner='remainder') for g in globals_],cross_unit_function_exports=sorted(exported),directives=directives,
                function_body_abi_coverage_verified=True,state_single_owner_structural_verified=True,partition_legal_verified=False,compiler_verified=False,calculation_verified=False,nvrtc_calls=0,ptxas_calls=0,link_calls=0,driver_calls=0,gpu_calls=0,
                scope='Candidate body bytes and parameter ABI checked; assembler/linker legality, tool compatibility, relocations and execution remain unverified')
    return report,units


def saved_partition(cache_entry,phases,destination,focus=None):
    destination=Path(destination);destination.mkdir(exist_ok=False)
    report=dict(schema=1,purpose='cpu-checked-ptx-partition-candidate',passed=False,compiler_verified=False,calculation_verified=False,nvrtc_calls=0,ptxas_calls=0,link_calls=0,driver_calls=0,gpu_calls=0)
    try:
        raw,key=load_saved_ptx(cache_entry,phases)
        report.update(input_sha256=sha(raw),cache_key=key,receipt_match=True)
        candidate,units=partition_candidate(raw,focus)
        report.update(candidate);report['artifacts']=[]
        for name,data in units.items():
            with (destination/name).open('xb') as stream:stream.write(data)
            report['artifacts'].append(dict(path=name,bytes=len(data),sha256=sha(data)))
        report['passed']=True
    except BaseException as error:
        report['error']=type(error).__name__+': '+str(error)
        raise
    finally:
        with (destination/'plan.json').open('x') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    return report


def audit_partition(cache_entry,phases,destination):
    """Reconstruct from original cached PTX; candidate claims cannot bless edits."""
    destination=Path(destination);actual=json.loads((destination/'plan.json').read_bytes())
    raw,key=load_saved_ptx(cache_entry,phases)
    expected,units=partition_candidate(raw,actual['focus'])
    artifacts=[dict(path=name,bytes=len(data),sha256=sha(data)) for name,data in units.items()]
    expected.update(cache_key=key,receipt_match=True,artifacts=artifacts,passed=True)
    if actual!=json.loads(json.dumps(expected)):raise ValueError('Partition plan differs from original cached PTX reconstruction')
    for name,data in units.items():
        if (destination/name).read_bytes()!=data:raise ValueError('Partition artifact differs from original cached PTX reconstruction')
    return dict(passed=True,cpu_audit_verified=True,input_sha256=sha(raw),cache_key=key,definitions=expected['definitions'],focus=expected['focus'],
                partition_legal_verified=False,compiler_verified=False,calculation_verified=False,nvrtc_calls=0,ptxas_calls=0,link_calls=0,driver_calls=0,gpu_calls=0)
