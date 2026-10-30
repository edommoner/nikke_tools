"""Exact historical source inverse, not generated-code normalization or a seal."""
import hashlib,json,re
from pathlib import Path
LEDGER_SHA256='93afb12ae4b67224a4cfe099ccf64bead769c52229d85ddfe0b45bfbc282f2f6'
PRODUCT_LEDGER_SHA256='9187d38559f8e40c2735afb95892f8cba4174b8a1ccf01b0d9d4bb0873894d38'

def product_sources(root):
    """Exact inverse of the reviewed product family before legacy audit layers.

    Preserve every old fixture. This proves an explicit historical preimage,
    never numerical equivalence of current product code to the legacy program.
    """
    root=Path(root);path=root/'tests/fixtures/portable-product-source-delta.json'
    if not path.exists():return {}
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PRODUCT_LEDGER_SHA256:raise ValueError('Product source history ledger changed')
    data=json.loads(raw)
    if (data['schema']!=1 or data['baseline_commit']!='168f1bbf65957a85ba48a58699e585f74aa5ad91'
            or data['normalizer_changed'] is not False or data['current_product_equivalence_claim'] is not False):
        raise ValueError('Product source history scope changed')
    for name,digest in data['added_sources'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Unreviewed product dependency: '+name)
    projected={}
    for name,row in data['files'].items():
        text=(root/name).read_text();digest=hashlib.sha256(text.encode()).hexdigest()
        # Exact reviewed charge corrections and GPU observation hooks only.
        # Recover the prior source before the unchanged historical ledger.
        if name=='gpu/world_charge_control_runtime.slang' and digest=='7ac4a981dcefff85b44293b8ba05a8058778c92972cc64a437f643b04f4bcaf8':
            text,count=re.subn(r'(?ms)^#ifdef PORTABLE_PRODUCT_OUTLINED_HELPERS\n.*?^#endif\n','',text)
            if count!=6:raise ValueError('Product charge observation spans differ')
            text=text.replace('// Product operator intervals reuse the bounded common control trace.\n// End product operator interval helpers.\n','')
            text=text.replace('    { results[a+14]=0xffffffff;storeNumber(a+6,ONE|F64_SIGN);results[a+22]=0;\n    }','    { results[a+14]=0xffffffff;storeNumber(a+6,ONE|F64_SIGN);results[a+22]=0; }')
            text=text.replace('                { results[a+14]=selected;storeNumber(a+6,uint64_t(0x7ff00000)<<32);results[a+15]=commands[row+2];\n                }','                { results[a+14]=selected;storeNumber(a+6,uint64_t(0x7ff00000)<<32);results[a+15]=commands[row+2]; }')
            text=text.replace('#if defined(PORTABLE_COORDINATE_ORIGINAL_FORCED_RELOAD) || defined(PORTABLE_PRODUCT_OUTLINED_HELPERS)','#ifdef PORTABLE_COORDINATE_ORIGINAL_FORCED_RELOAD')
            text=text.replace('return (commands[p+1]==4 || commands[p+1]==5&&commands[p+10]>0&&commands[p+10]<32) && commands[p+5]==0x46424731U','return commands[p+1]==4 && commands[p+5]==0x46424731U')
            text=text.replace('    return commands[p+1]==5?11:10;','    return 10;')
            text=text.replace('{ uint p=controlInput(s);\n#ifdef PORTABLE_PRODUCT_FIXED_BURST\n    if(commands[p+1]==5)return (commands[p+10]&(1U<<who))!=0;\n#endif\n    return (commands[p+1]==2','{ uint p=controlInput(s);return (commands[p+1]==2')
            digest=hashlib.sha256(text.encode()).hexdigest()
            if digest!='aa8df45901d9d3a7e19d6af41bbd6a0a1721594156ea56c4dd1f47cde900c33d':raise ValueError('Product charge history preimage differs')
        # Partial charge applies to the BODY and its part/interrupt snapshot.
        # This exact source inverse retains the old full-charge-only history.
        if name=='gpu/event_runtime.slang' and digest=='8f2b069a23501b3d983279748de0c4dd239f674c9d66f113c95a045ce4a47594':
            text=text.replace('w.mode==1?(PARTIAL_IS_FULL(w)?H_CHARGE:0U)|','w.mode==1?H_CHARGE|')
            text=text.replace('w.mode==1 ? (PARTIAL_IS_FULL(w)?H_CHARGE:0U)|','w.mode==1 ? H_CHARGE|')
            digest=hashlib.sha256(text.encode()).hexdigest()
            if digest!=row['current_sha256']:raise ValueError('Product part charge history preimage differs')
        if digest==row['baseline_sha256']:
            projected[name]=text;continue
        if digest!=row['current_sha256']:raise ValueError('Unreviewed product source: '+name)
        boundary=len(text)
        for hunk in reversed(row['hunks']):
            start,end=hunk['start'],hunk['end']
            if not 0<=start<=end<=boundary or text[start:end]!=hunk['current']:
                raise ValueError('Product source inverse spans differ: '+name)
            text=text[:start]+hunk['baseline']+text[end:];boundary=start
        if hashlib.sha256(text.encode()).hexdigest()!=row['baseline_sha256']:raise ValueError('Product source preimage differs: '+name)
        projected[name]=text
    return projected

def project_sources(root):
    root=Path(root);raw=(root/'tests/fixtures/portable-weighted-incoming-source-delta.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:raise ValueError('Weighted source inverse ledger changed')
    data=json.loads(raw)
    if data['schema']!=1 or data['normalizer_changed'] is not False or data['baseline_commit']!='e93182fb61ed6fce5cb7d02e13e1aa5ac59ec840':raise ValueError('Weighted source baseline changed')
    for name,digest in data['added_sources'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Unreviewed weighted dependency: '+name)
    projected=product_sources(root)
    group=root/'gpu/attack_group_runtime.slang'
    if group.exists():
        text=group.read_text();digest=hashlib.sha256(text.encode()).hexdigest()
        if digest=='30c0706d85c6144e4d2952bbfa38107abccf56fcef9d95ed36d1831f2baf5bc1':
            text=text.replace('#ifdef PORTABLE_PRODUCT_OUTLINED_HELPERS\n            // Native parts are additional packets of this BODY pellet. They\n            // never become logical enemies in the multi-hit recipient set.\n            if(results[head+9]!=0&&commands[actorBinding(s,slot)]==0&&counterLandingsEnabled(s)&&s.error==0)\n                deliverCounterParts(s,who,ACTOR_REF|slot,when,output);\n#endif\n','',1)
            text=text.replace('\n#ifdef PORTABLE_PRODUCT_OUTLINED_HELPERS\n       &&!(commands[input+1]==2&&commands[actorBinding(s,slot)]==1)\n#endif\n       ','',1)
            if hashlib.sha256(text.encode()).hexdigest()!='0ea6d9b8bd82f063553762609836bd536c025590455ae7191be3440bb4dcf070':raise ValueError('Product native part group preimage differs')
            projected['gpu/attack_group_runtime.slang']=text
        elif digest!='0ea6d9b8bd82f063553762609836bd536c025590455ae7191be3440bb4dcf070':raise ValueError('Unreviewed product source: gpu/attack_group_runtime.slang')
    for name,row in data['files'].items():
        text=projected.get(name,(root/name).read_text())
        if hashlib.sha256(text.encode()).hexdigest()!=row['after_sha256']:raise ValueError('Unreviewed weighted source: '+name)
        for hunk in reversed(row['hunks']):
            if text.count(hunk['after'])!=1:raise ValueError('Ambiguous weighted source inverse: '+name)
            text=text.replace(hunk['after'],hunk['before'],1)
        if hashlib.sha256(text.encode()).hexdigest()!=row['before_sha256']:raise ValueError('Weighted source preimage differs: '+name)
        projected[name]=text
    return projected
def projected_hashes(root,source,sources):
    root=Path(root).resolve();found={}
    def visit(path):
        name=path.relative_to(root).as_posix()
        if name in found:return
        raw=sources[name].encode() if name in sources else path.read_bytes();found[name]=hashlib.sha256(raw).hexdigest()
        for inc in re.findall(rb'^\s*#include\s+"([^"]+)"',raw,re.M):visit((path.parent/inc.decode()).resolve())
    visit(root/source);return found
def historical_hashes(root,source):return projected_hashes(root,source,project_sources(root))
