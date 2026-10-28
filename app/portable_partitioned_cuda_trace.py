"""Explicit sequence protocol; the legacy one-launch auditor is unchanged.

CPU-only boundary validation. It does not authorize a Windows execution, prove
calculation, or infer launch dimensions which the legacy observer did not log.
"""
import re


def verify(rows,layout,transports,*,pid):
    try:return _verify(rows,layout,transports,pid)
    except (ValueError,KeyError,TypeError,IndexError,OverflowError):return False


def _verify(rows,layout,transports,pid):
    from portable_backend import READBACK_CHUNK_BYTES
    from portable_phase_audit import valid_cache_hit,valid_linked_artifact
    if type(pid) is not int or pid<=0 or not rows:return False
    if any(not isinstance(r,dict) or not isinstance(r.get('stage'),str) or type(r.get('pid')) is not int or r['pid']!=pid or r.get('state') not in ('entered','returned','verified') for r in rows):return False
    if any(type(r['monotonic_ns']) is not int for r in rows) or any(a['monotonic_ns']>b['monotonic_ns'] for a,b in zip(rows,rows[1:])):return False
    batches=layout['batches']
    if not batches or len(batches)!=len(transports):return False
    if any(r['stage'].startswith('nvrtc') or r['stage']=='nvrtcCompileProgram' for r in rows):return False
    hits=[(i,r) for i,r in enumerate(rows) if valid_cache_hit(r) or valid_linked_artifact(r)]
    if len(hits)!=1:return False
    receipt=hits[0][1]['receipt']
    if receipt['identity']['artifact']!='cubin':return False
    # Every driver boundary is accounted for. Unknown/extra calls and failed or
    # unmatched returns cannot be hidden by the successful calls around them.
    native=[(i,r) for i,r in enumerate(rows) if re.fullmatch(r'cu[A-Z].*',r['stage'])]
    calls=[]
    if len(native)%2:return False
    for n in range(0,len(native),2):
        (a,x),(b,y)=native[n:n+2]
        if x['stage']!=y['stage'] or x['state']!='entered' or y['state']!='returned' or type(y.get('return_code')) is not int or y['return_code']!=0:return False
        calls.append((x['stage'],a,b,x))
    expected=['cuInit','cuDeviceGet','cuDeviceComputeCapability','cuDeviceGetName','cuCtxCreate_v2',
              'cuModuleLoadData','cuModuleGetFunction','cuModuleGetGlobal_v2',*(['cuMemAlloc_v2']*3)]
    for batch in batches:
        size=batch['output_bytes']
        if type(size) is not int or size<=0:return False
        expected+=['cuMemcpyHtoD_v2','cuMemsetD8_v2','cuMemcpyHtoD_v2','cuLaunchKernel','cuCtxSynchronize']
        expected+=['cuMemcpyDtoH_v2']*((size+READBACK_CHUNK_BYTES-1)//READBACK_CHUNK_BYTES)
    expected+=['cuCtxDestroy_v2']
    if [c[0] for c in calls]!=expected or hits[0][0]>=calls[0][1]:return False
    markers=[(i,r) for i,r in enumerate(rows) if r['stage']=='cuda_readback_file']
    if len(markers)!=2*len(batches):return False
    cursor=11;total=0;address=None
    for index,(batch,transport) in enumerate(zip(batches,transports,strict=True)):
        if (batch['first_case']!=total or type(batch['cases']) is not int or not 1<=batch['cases']<=layout['batch_size']
            or batch['output_bytes']!=batch['cases']*layout['output_words']*4
            or transport.get('backend')!='cuda' or transport.get('command_status')!='completed'
            or transport.get('compile_artifact')!=receipt
            or any(transport.get(k)!=batch[v] for k,v in (('cases','cases'),('input_bytes','input_bytes'),('output_bytes','output_bytes')))):
            return False
        size=batch['output_bytes'];chunks=(size+READBACK_CHUNK_BYTES-1)//READBACK_CHUNK_BYTES
        (start,request),(end,returned)=markers[2*index:2*index+2]
        if request['state']!='entered' or returned['state']!='returned' or not calls[cursor+4][2]<start<end:return False
        current=request['device_address']
        if type(current) is not int or current<=0 or address is not None and current!=address:return False
        address=current
        stream=returned['receipt']
        if (request['output_bytes']!=size or request['chunk_bytes']!=READBACK_CHUNK_BYTES or stream!=transport.get('readback_stream')
            or any(type(stream[k]) is not int for k in ('output_bytes','chunk_bytes','chunks'))
            or stream['output_bytes']!=size or stream['chunk_bytes']!=READBACK_CHUNK_BYTES or stream['chunks']!=chunks
            or not isinstance(stream['output_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',stream['output_sha256'])):return False
        zero=calls[cursor+1][3]
        if zero.get('destination_device')!=address or zero.get('value')!=0 or zero.get('byte_count')!=size:return False
        position=start
        for n in range(chunks):
            _,a,b,copy=calls[cursor+5+n];offset=n*READBACK_CHUNK_BYTES
            if not position<a<b<end or copy.get('source_device')!=address+offset or copy.get('byte_count')!=min(READBACK_CHUNK_BYTES,size-offset):return False
            position=b
        cursor+=5+chunks
        if not end<calls[cursor][1]:return False
        total+=batch['cases']
    return total==layout['input_count'] and cursor==len(calls)-1
