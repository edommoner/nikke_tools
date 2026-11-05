"""One sampled-vital kind guard for Slang emission and CPU-only early rejection.

This checks definition kinds only. It never certifies schema, runtime behavior,
GPU execution or other initializeCoordinateSampling predicates.
"""
import re
from pathlib import Path
BASE=(0,2,3,4,6,7,8,24)
EXTENSIONS=(
 ('PORTABLE_COORDINATE_EXISTING_HANDLERS',(18,20,21,31,34,35,37),False,'Private existing handlers; kind acceptance is not native battle certification.'),
 ('PORTABLE_COORDINATE_ORIGINAL_COVER_REVIVE',(30,),False,'Existing shared broken-cover revival and recipient handlers.'),
 ('PORTABLE_COORDINATE_ORIGINAL_SHIELD_HEAL',(27,),False,'Existing shared protection healing and periodic instant handlers.'),
 ('PORTABLE_COORDINATE_ORIGINAL_FORCED_RELOAD',(23,),False,'Existing common reload request and lifecycle handlers.'),
 ('PORTABLE_COORDINATE_ORIGINAL_SOURCE_OPS',(15,33),False,'Existing named duration and forced skill-slot handlers.'),
 ('PORTABLE_COORDINATE_ORIGINAL_CLEANSE',(26,),False,'Existing allied cleanse and enemy overlay dispel handlers.'),
 ('PORTABLE_COORDINATE_ORIGINAL_STACKS',(16,17,19),False,'Existing own-stack and current-stack increase handlers.'),
 ('PORTABLE_COORDINATE_ORIGINAL_AMMO',(13,14),False,'Existing shared percentage and flat ammo handlers.'),
 ('PORTABLE_COORDINATE_ORIGINAL_RESOURCES',(9,10),False,'Existing shared gauge charge/consume handlers.'),
 ('PORTABLE_ENEMY_AMMO',(11,),False,'Existing ammo-observed gauge consumption; opt-in enemy magazine battles.'),
 ('PORTABLE_COORDINATE_ORIGINAL_CLOCKS',(22,),False,'Existing shared remaining skill-clock reduction.'),
 ('PORTABLE_COORDINATE_ORIGINAL_ROSTER',(1,),False,'Existing named removal, recipient snapshot and callbacks.'),
 ('PORTABLE_COORDINATE_HEALING',(32,),False,'Existing received-healing pool discharge, including lifecycle.'),
 ('PORTABLE_COORDINATE_BURST_CONTROLS',(5,25),True,'Existing shared cooldown/reentry handlers.'),
 ('PORTABLE_COORDINATE_SQUAD_MODE_STATE',(29,),False,'Existing shared revival handler; mode flags survive on_down/on_revive.'),
)
FRAGMENT='gpu/coordinate_vital_kind_admission.slang'
INCLUDE='#include "coordinate_vital_kind_admission.slang"'

def render():
    lines=['        if('+ '&&'.join('kind!='+str(k) for k in BASE)]
    for macro,kinds,controls,comment in EXTENSIONS:
        term='&&'.join('kind!='+str(k) for k in kinds)
        if controls:term='(('+term+')||!burstControls(s))'
        lines.extend(['#ifdef '+macro,'            &&'+term+' // '+comment,'#endif'])
    lines.append('        )return false; // Shared weapon/heal/reduce dispatch.')
    return '\n'.join(lines)+'\n'

def profile(root,source):
    from portable_backend import source_hashes
    root=Path(root);closure=source_hashes(source)
    macros={};known={macro for macro,*_ in EXTENSIONS}|{'PORTABLE_COORDINATE_SAMPLED_VITAL'}
    for name in closure:
        if not name.endswith('_entry.slang'):continue
        depth=0
        for line in (root/name).read_text().splitlines():
            if re.match(r'\s*#\s*(?:if|ifdef|ifndef)\b',line):depth+=1
            elif re.match(r'\s*#\s*endif\b',line):depth-=1
            match=re.match(r'\s*#\s*define\s+(\w+)\b',line)
            if match and match[1] in known:
                if depth:raise ValueError('Conditional profile kind macro is not statically attested: '+match[1])
                macros[match[1]]=name
    if 'PORTABLE_COORDINATE_SAMPLED_VITAL' not in macros:return dict(checked=False,macros=())
    if FRAGMENT not in closure or (root/FRAGMENT).read_text()!=render():raise ValueError('Shared kind guard differs from its declared policy')
    text=(root/'gpu/coordinate_sampling_runtime.slang').read_text()
    if text.count(INCLUDE)!=1 or '#ifdef PORTABLE_COORDINATE_SAMPLED_VITAL\n'+INCLUDE not in text:raise ValueError('Shared kind guard is disconnected from sampled-vital initializer')
    return dict(checked=True,macros=tuple(sorted(macros)))

class KindAdmission:
    def __init__(self,root,source):self.profile=profile(root,source)

    def inspect(self,words):
        from portable_specs import LIMITS as L,FIELDS as F
        if not self.profile['checked']:return dict(checked=False,scope='not-sampled-vital',unsupported=[])
        macros=self.profile['macros'];allowed=set(BASE)
        from portable_burst_control_specs import INPUT_BASE
        controls=len(words)>INPUT_BASE+2 and words[INPUT_BASE+2]==1
        for macro,kinds,needs_controls,_ in EXTENSIONS:
            if macro in macros and (not needs_controls or controls):allowed.update(kinds)
        if len(words)<=L['DEFINITION_BASE'] or not 0<=words[1]<=L['DEFINITIONS']:raise ValueError('Complete definition wire required for kind preflight')
        unsupported=[]
        for row in range(words[1]):
            at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['KIND']
            if at>=len(words):raise ValueError('Truncated definition wire in kind preflight')
            if words[at] not in allowed:unsupported.append(dict(row=row,kind=words[at]))
        return dict(checked=True,scope='sampled-vital-definition-kinds-only',unsupported=unsupported,profile_macros=sorted(macros),gpu_admission_verified=False)

def inspect_kinds(root,source,words):return KindAdmission(root,source).inspect(words)

def require_kinds(root,source,words):
    result=inspect_kinds(root,source,words)
    if result['unsupported']:raise ValueError('GPU definition kinds rejected before native/GPU execution: '+str(result['unsupported']))
    return result
