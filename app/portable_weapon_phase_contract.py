"""Current weapon phase signatures, wrapper ordering and macro control flow."""
import re
from pathlib import Path
_NON_CODE=re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"',re.S)
NAMES=('prepareWeaponFrame','advanceWeaponCharge','captureWeaponShot','landWeaponPellets','finishWeaponShot')
SIGNATURES=(
'inout Runtime s,uint who,uint64_t when,uint output,out uint target,out Weapon w,out bool ready',
'inout Runtime s,inout Weapon w,uint who,uint64_t when,uint output,uint epoch,int mode,out bool ready',
'inout Runtime s,inout Weapon w,uint who,uint64_t when,uint output,uint target,uint modeShots,int mode,uint epoch,inout uint64_t landedAmount,inout uint landedCount,inout uint landedTarget,out uint completedShots,out bool scheduleAutoReload,out uint64_t shotInterval,out bool last,out bool ready',
'inout Runtime s,inout Weapon w,uint who,uint64_t when,uint output,uint target,uint64_t amount,uint count,uint completedShots',
'inout Runtime s,inout Weapon w,uint who,uint64_t when,uint output,uint count,uint epoch,int mode,bool scheduleAutoReload,uint64_t shotInterval,bool last')

def tokens(text):return re.findall(r'[A-Za-z_]\w*|\d+|[^\s]',_NON_CODE.sub('',text))

def body(source,name):
    masked=_NON_CODE.sub(lambda m:''.join('\n' if c=='\n' else ' ' for c in m[0]),source)
    hits=list(re.finditer(r'\bvoid\s+'+re.escape(name)+r'\s*\([^{};]*\)\s*\{',masked))
    if len(hits)!=1:raise ValueError('Missing or ambiguous phase: '+name)
    start=hits[0].end();end=start;depth=1
    while depth and end<len(masked):
        depth+=(masked[end]=='{')-(masked[end]=='}');end+=1
    if depth:raise ValueError('Unbalanced phase: '+name)
    return source[start:end-1]


def verify_land_macros(root,*,event_source=None):
    # Check every authored definition branch, including inactive wire variants.
    # Expand macro dependencies lexically; ordinary function returns stay local
    # to those functions and are not caller control-flow escapes.
    definitions={}
    for path in sorted((Path(root)/'gpu').glob('*.slang')):
        text=event_source if event_source is not None and path.name=='event_runtime.slang' else path.read_text()
        text=_NON_CODE.sub(lambda m:''.join('\n' if c=='\n' else ' ' for c in m[0]),text)
        text=text.replace('\\\n',' ')
        for name,value in re.findall(r'(?m)^\s*#define[ \t]+(\w+)(?:\([^\n)]*\))?[ \t]*([^\n]*)',text):
            definitions.setdefault(name,[]).append(value)
    roots=('WORLD_POOL_PHYSICAL_TARGET','WORLD_TEAM_PELLET','WORLD_FRACTION_AUTO')
    pending=list(roots);seen=set()
    while pending:
        name=pending.pop()
        if name in seen:continue
        seen.add(name)
        assert name in definitions,'Missing land macro: '+name
        for value in definitions[name]:
            words=tokens(value)
            assert not set(words)&{'return','break','continue'},'Land macro escape: '+name
            pending.extend(word for word in words if word in definitions and word not in seen)
    return dict(roots=list(roots),definitions_checked=sum(len(definitions[name]) for name in seen),macro_names=sorted(seen))


def verify(root, *, phase_source=None, wrapper_source=None):
    root=Path(root);macro_contract=verify_land_macros(root)
    source=phase_source if phase_source is not None else (root/'gpu/weapon_frame_phases.slang').read_text()
    wrapper=wrapper_source if wrapper_source is not None else (root/'gpu/combat_runtime.slang').read_text()
    for i,name in enumerate(NAMES):
        signatures=re.findall(r'\bvoid\s+'+name+r'\s*\(([^{};]*)\)\s*\{',_NON_CODE.sub('',source))
        signature=SIGNATURES[i]
        if i==4:signature+='\n#ifdef PORTABLE_PARENT_FIXED_DAMAGE\n,uint64_t landedAmount\n#endif\n'
        assert len(signatures)==1 and tokens(signatures[0])==tokens(signature),'Weapon phase signature/argument contract changed'
        if i<3:
            part=tokens(body(source,name))
            assert part[:4]==['ready','=','false',';'] and part[-4:]==['ready','=','true',';'],'Weapon phase readiness contract changed'
    expected='landedAmount=0;landedCount=0;landedTarget=0;'+'''
    uint target;Weapon w;bool ready;
    prepareWeaponFrame(s,who,when,output,target,w,ready);if(!ready) return;
    '''+'uint epoch = s.modeEpoch[who], modeShots = s.modeShots[who]; int mode = s.modeIndex[who];'+'''
    advanceWeaponCharge(s,w,who,when,output,epoch,mode,ready);if(!ready) return;
    uint completedShots;bool scheduleAutoReload,last;uint64_t shotInterval;
    captureWeaponShot(s,w,who,when,output,target,modeShots,mode,epoch,landedAmount,landedCount,landedTarget,completedShots,scheduleAutoReload,shotInterval,last,ready);if(!ready) return;
    landWeaponPellets(s,w,who,when,output,target,landedAmount,landedCount,completedShots);
    finishWeaponShot(s,w,who,when,output,landedCount,epoch,mode,scheduleAutoReload,shotInterval,last
#ifdef PORTABLE_PARENT_FIXED_DAMAGE
,landedAmount
#endif
);
    '''
    assert tokens(body(wrapper,'weaponFrameBody'))==tokens(expected),'Weapon phase call/argument/snapshot/exit contract changed'
    return dict(verified=True,phases=list(NAMES),land_macro_contract=macro_contract,helper_signature_contract_verified=True,wrapper_exit_contract_verified=True,gpu_calls=0)
