"""Check the private weapon-frame source transplant; not a GPU equivalence proof."""
import hashlib,json,re
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


def verify(root,*,phase_source=None,wrapper_source=None):
    root=Path(root);macro_contract=verify_land_macros(root);fixture=json.loads((root/'tests/fixtures/portable-weapon-frame-transplant.json').read_text())
    before=fixture['body'];assert hashlib.sha256(before.encode()).hexdigest()==fixture['body_sha256']
    source=phase_source if phase_source is not None else (root/'gpu/weapon_frame_phases.slang').read_text()
    from portable_physical_interrupt_contract import baseline_phase
    try:
        from portable_native_query_source_contract import baseline_source as baseline_native
        source,_=baseline_native(root,'gpu/weapon_frame_phases.slang',source)
        source=baseline_phase(root,source)
    except AssertionError as error:raise AssertionError('Weapon phase statements/signature changed: '+str(error)) from error
    wrapper=wrapper_source if wrapper_source is not None else (root/'gpu/combat_runtime.slang').read_text()
    parts=[]
    for i,name in enumerate(NAMES):
        signatures=re.findall(r'\bvoid\s+'+name+r'\s*\(([^{};]*)\)\s*\{',_NON_CODE.sub('',source))
        assert len(signatures)==1 and tokens(signatures[0])==tokens(SIGNATURES[i]),'Weapon phase signature/argument contract changed'
        part=body(source,name)
        if i<3:
            # New helper returns leave ready=false. Only the old fallthrough
            # reaches ready=true; the caller must stop on every early return.
            assert tokens(part)[:4]==['ready','=','false',';']
            assert tokens(part)[-4:]==['ready','=','true',';']
            part=re.sub(r'^\s*ready=false;','',part,count=1)
            part=re.sub(r'\s*ready=true;\s*$','\n',part,count=1)
        parts.append(part)
    parts[0]=parts[0].replace('target = aimedTarget','uint target = aimedTarget').replace('s.target = target; selectWeapon','s.target = target; Weapon w;selectWeapon')
    parts[2]=parts[2].replace('scheduleAutoReload =','bool scheduleAutoReload =').replace('shotInterval =','uint64_t shotInterval =').replace('last =','bool last =').replace('completedShots =','uint completedShots =')
    initialization='landedAmount=0;landedCount=0;landedTarget=0;'
    snapshot='uint epoch = s.modeEpoch[who], modeShots = s.modeShots[who]; int mode = s.modeIndex[who];'
    reconstructed=initialization+parts[0]+snapshot+''.join(parts[1:])
    assert tokens(reconstructed)==tokens(before),'Weapon phase statements changed or were reordered'
    expected=initialization+'''
    uint target;Weapon w;bool ready;
    prepareWeaponFrame(s,who,when,output,target,w,ready);if(!ready) return;
    '''+snapshot+'''
    advanceWeaponCharge(s,w,who,when,output,epoch,mode,ready);if(!ready) return;
    uint completedShots;bool scheduleAutoReload,last;uint64_t shotInterval;
    captureWeaponShot(s,w,who,when,output,target,modeShots,mode,epoch,landedAmount,landedCount,landedTarget,completedShots,scheduleAutoReload,shotInterval,last,ready);if(!ready) return;
    landWeaponPellets(s,w,who,when,output,target,landedAmount,landedCount,completedShots);
    finishWeaponShot(s,w,who,when,output,landedCount,epoch,mode,scheduleAutoReload,shotInterval,last);
    '''
    assert tokens(body(wrapper,'weaponFrameBody'))==tokens(expected),'Weapon phase call/argument/snapshot/exit contract changed'
    return dict(verified=True,gpu_calls=0,baseline_commit=fixture['baseline_commit'],phases=list(NAMES),
        token_count=len(tokens(before)),token_sha256=hashlib.sha256(json.dumps(tokens(before),separators=(',',':')).encode()).hexdigest(),
        land_macro_contract=macro_contract,helper_signature_contract_verified=True,wrapper_exit_contract_verified=True,reviewed_physical_interrupt_hook=True,reviewed_mode_capacity_hook=True,scope='Reconstructed original statements outside the exact physical interrupt and mode-capacity zero-ammo hooks and explicit call/argument/ready ordering. Not runtime/compiler resource proof')
