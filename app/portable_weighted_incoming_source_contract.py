"""Exact historical source inverse, not generated-code normalization or a seal."""
import hashlib,json,re
from pathlib import Path
LEDGER_SHA256='93afb12ae4b67224a4cfe099ccf64bead769c52229d85ddfe0b45bfbc282f2f6'
PRODUCT_LEDGER_SHA256='9187d38559f8e40c2735afb95892f8cba4174b8a1ccf01b0d9d4bb0873894d38'
BOSS_LEDGER_SHA256='2860738ae7d6ce4a586ca92955a06808eba526cdbf8f6e00a3f399eb83280ebf'

def boss_source_preimages(root):
    """Recover exact old bytes for historical audits, never current admission."""
    root=Path(root);path=root/'tests/fixtures/portable-product-boss-debuff-source-delta.json'
    if not path.exists():return {}
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=BOSS_LEDGER_SHA256:raise ValueError('Boss product source history ledger changed')
    data=json.loads(raw)
    if data.get('schema')!='product-boss-debuff-source-history-v1' or data.get('baseline_commit')!='88cda975122d394f6409c7cec68b21efbdde12ab' or data.get('normalizer_changed') is not False or data.get('current_product_equivalence_claim') is not False:
        raise ValueError('Boss product source history scope changed')
    projected={};older=None
    for name,row in data['files'].items():
        text=(root/name).read_bytes().decode('utf-8');digest=hashlib.sha256(text.encode()).hexdigest()
        if digest==row['before_sha256']:projected[name]=text;continue
        if digest!=row['after_sha256']:
            # The existing inverse can already have restored an exact older
            # product baseline. Accept only that separately pinned ledger's
            # full-file digest, never a partially matched source or new value.
            if older is None:
                old_raw=(root/'tests/fixtures/portable-product-source-delta.json').read_bytes()
                if hashlib.sha256(old_raw).hexdigest()!=PRODUCT_LEDGER_SHA256:raise ValueError('Product source history ledger changed')
                older=json.loads(old_raw)
            old_digest=older.get('files',{}).get(name,{}).get('baseline_sha256',older.get('added_sources',{}).get(name))
            if digest==old_digest:projected[name]=text;continue
            raise ValueError('Unreviewed product source: '+name)
        boundary=len(text)
        for hunk in reversed(row['hunks']):
            start,end=hunk['start'],hunk['end']
            if not 0<=start<=end<=boundary or text[start:end]!=hunk['after']:raise ValueError('Boss product source inverse spans differ')
            text=text[:start]+hunk['before']+text[end:];boundary=start
        if hashlib.sha256(text.encode()).hexdigest()!=row['before_sha256']:raise ValueError('Boss product source preimage differs')
        projected[name]=text
    return projected

def _product_part_preimage(name,text):
    """Reviewed source history only; never current numerical equivalence."""
    digest=hashlib.sha256(text.encode()).hexdigest()
    if name=='gpu/destructible_weapon_runtime.slang' and digest=='34ef4ef4614589da699af251e0ed2d28f8f8de945ccacd2310fbcb0d1cc8fd20':
        text=text.replace('bool validDestructibleWeapons(inout Runtime s)\n{\n    if(commands[s.inputBase+110084]>1||s.landingPolicy==0) return false;\n#ifdef PORTABLE_DESTRUCTIBLE_EMPTY_BODY\n    // With no interceptable target, all post-landing work remains on the\n    // existing body path, including lifesteal and damage accumulation.\n    if(commands[DF_EXTRA(s)+2320]==0)\n    {\n        if(actorPoolCount(s)==0||commands[actorBinding(s,0)]!=0) return false;\n        for(uint slot=1;slot<actorPoolCount(s);slot++) if(commands[actorBinding(s,slot)]!=1) return false;\n        return true;\n    }\n#endif\n    if(actorPoolCount(s)!=1) return false;\n    for(uint row=0;row<s.count;row++)\n    {\n        Definition d=readDefinition(s.inputBase,row);\n#ifdef PORTABLE_DESTRUCTIBLE_BODY_ACCUM\n        bool accum=commands[s.inputBase+110080]==0x48534936U&&commands[s.inputBase+110087]==1;\n        if(d.kind==34&&!accum) return false;\n        if(d.kind==0&&((d.stat==S_lifesteal_pct&&commands[s.inputBase+110080]!=0x48534935U&&!accum)||((d.stat==81||d.stat==82)&&!accum))) return false;\n#elif defined(PORTABLE_DESTRUCTIBLE_BODY_LIFESTEAL)\n        if(d.kind==0&&((d.stat==S_lifesteal_pct&&commands[s.inputBase+110080]!=0x48534935U)||d.stat==81||d.stat==82)) return false;\n#else\n        if(d.kind==0&&(d.stat==S_lifesteal_pct||d.stat==81||d.stat==82)) return false;\n#endif\n    }\n    return true;\n}\n','bool validDestructibleWeapons(inout Runtime s)\n{\n    if(commands[s.inputBase+110084]>1||s.landingPolicy==0||actorPoolCount(s)!=1) return false;\n#ifdef PORTABLE_DESTRUCTIBLE_EMPTY_BODY\n    // With no interceptable target, all post-landing work remains on the\n    // existing body path, including lifesteal and damage accumulation.\n    if(commands[DF_EXTRA(s)+2320]==0) return true;\n#endif\n    for(uint row=0;row<s.count;row++)\n    {\n        Definition d=readDefinition(s.inputBase,row);\n#ifdef PORTABLE_DESTRUCTIBLE_BODY_ACCUM\n        bool accum=commands[s.inputBase+110080]==0x48534936U&&commands[s.inputBase+110087]==1;\n        if(d.kind==34&&!accum) return false;\n        if(d.kind==0&&((d.stat==S_lifesteal_pct&&commands[s.inputBase+110080]!=0x48534935U&&!accum)||((d.stat==81||d.stat==82)&&!accum))) return false;\n#elif defined(PORTABLE_DESTRUCTIBLE_BODY_LIFESTEAL)\n        if(d.kind==0&&((d.stat==S_lifesteal_pct&&commands[s.inputBase+110080]!=0x48534935U)||d.stat==81||d.stat==82)) return false;\n#else\n        if(d.kind==0&&(d.stat==S_lifesteal_pct||d.stat==81||d.stat==82)) return false;\n#endif\n    }\n    return true;\n}\n',1)
        if hashlib.sha256(text.encode()).hexdigest()!='e66d7817c87466244020cdf539dd8cb9ce29df39455f0dd2de8f3dd5fe60ecb4':raise ValueError('Product modifier part preimage differs')
    if name=='gpu/product_group_target_battle_entry.slang' and digest=='5a87c08576208567b6256bd99dd373f10eb11dd42a35e804dff911638908c42a':
        text=text.replace('bool validProductGroupTargetAxes(inout Runtime s)\n{\n    uint descriptor=s.inputBase+104408;\n    if(commands[descriptor]!=0x50474131U||commands[descriptor+1]!=1||commands[descriptor+2]==0||commands[descriptor+2]>256) return false;\n    for(uint i=3;i<8;i++) if(commands[descriptor+i]!=0) return false;\n    if(actorPoolCount(s)==0||commands[actorBinding(s,0)]!=0) return false;\n    for(uint slot=1;slot<actorPoolCount(s);slot++) if(commands[actorBinding(s,slot)]!=1) return false;\n    uint count=0;\n    for(uint row=0;row<256;row++)\n    {\n        uint axis=commands[descriptor+8+row];\n        if(axis==0) continue;\n        if(row>=s.count||(axis!=2&&axis!=3)) return false;\n        Definition d=readDefinition(s.inputBase,row);\n        if(d.kind!=4||d.stat!=0||d.enemyBuff!=0||d.healthScaling!=0||d.quantityFlags!=0||d.alliedFlags!=0||d.damageFlags!=0||!f64Finite(d.value)) return false;\n        count++;\n    }\n    return count==commands[descriptor+2];\n}\n\n','bool validProductGroupTargetAxes(inout Runtime s)\n{\n    uint descriptor=s.inputBase+104408;\n    if(commands[descriptor]!=0x50474131U||commands[descriptor+1]!=1||commands[descriptor+2]==0||commands[descriptor+2]>256) return false;\n    for(uint i=3;i<8;i++) if(commands[descriptor+i]!=0) return false;\n    if(actorPoolCount(s)!=1||commands[actorBinding(s,0)]!=0) return false;\n    uint count=0;\n    for(uint row=0;row<256;row++)\n    {\n        uint axis=commands[descriptor+8+row];\n        if(axis==0) continue;\n        if(row>=s.count||(axis!=2&&axis!=3)) return false;\n        Definition d=readDefinition(s.inputBase,row);\n        if(d.kind!=4||d.stat!=0||d.enemyBuff!=0||d.healthScaling!=0||d.quantityFlags!=0||d.alliedFlags!=0||d.damageFlags!=0||!f64Finite(d.value)) return false;\n        count++;\n    }\n    return count==commands[descriptor+2];\n}\n\n',1)
        text=text.replace('// Product BODY/PART specialization:','// Product plain-body specialization:',1)
        if hashlib.sha256(text.encode()).hexdigest()!='979c91067a4ea0110f5f5f1d66a0d8fa40431c931a9bd5d9ac6212a666adef1d':raise ValueError('Product modifier part preimage differs')
    if name=='gpu/destructible_battle_runtime.slang' and digest=='766691cba6bdf15af1ed8670eb48c3efbf5873c6916c0457e8c95aaa678288fc':
        text=text.replace('        if(!weaponOnly||actorPoolCount(s)==0||commands[actorBinding(s,0)]!=0) return false;\n        for(uint slot=1;slot<actorPoolCount(s);slot++) if(commands[actorBinding(s,slot)]!=1) return false;','        if(!weaponOnly||actorPoolCount(s)!=1) return false;',1)
        if hashlib.sha256(text.encode()).hexdigest()!='00df3307cf0d29c50321c35e53e31a449ec3577c065ca1ebbcc01984c568f459':raise ValueError('Product modifier part preimage differs')
    return text

def product_sources(root,*,_preimages=None):
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
    projected={};preimages=boss_source_preimages(root) if _preimages is None else _preimages
    for name,digest in data['added_sources'].items():
        raw=(root/name).read_bytes();text=_product_part_preimage(name,preimages.get(name,raw.decode()))
        if hashlib.sha256(text.encode()).hexdigest()!=digest:raise ValueError('Unreviewed product dependency: '+name)
        if text.encode()!=raw or name=='gpu/product_group_target_battle_entry.slang':projected[name]=text
    for name,row in data['files'].items():
        text=_product_part_preimage(name,preimages.get(name,(root/name).read_text()));digest=hashlib.sha256(text.encode()).hexdigest()
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
    projected=boss_source_preimages(root)
    projected.update(product_sources(root,_preimages=projected))
    parts=root/'gpu/counter_landing_runtime.slang'
    if parts.exists():
        text=parts.read_text();digest=hashlib.sha256(text.encode()).hexdigest()
        if digest=='0ce6bbcfc8a63c38c82a990b7d9ba8a4006cf16286c146471e80863ec22a37fd':
            text=text.replace('#ifdef PORTABLE_PRODUCT_OUTLINED_HELPERS\n// Keep the nested part/interrupt packet loops outside each product shot caller.\n[noinline]\n#endif\nvoid deliverCounterParts(', 'void deliverCounterParts(',1)
            if hashlib.sha256(text.encode()).hexdigest()!='d84aeea5965ffd318c409f38b5a1562293ac445ad11d3ee113f539726ba733e5':raise ValueError('Product part boundary preimage differs')
        elif digest!='d84aeea5965ffd318c409f38b5a1562293ac445ad11d3ee113f539726ba733e5':raise ValueError('Unreviewed product source: gpu/counter_landing_runtime.slang')
        projected['gpu/counter_landing_runtime.slang']=text
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
