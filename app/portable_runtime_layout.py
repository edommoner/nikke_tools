"""Generate compact zeroing loops from the shared Runtime declaration.
Immutable definitions are read directly from the static input wire; runtime
initialization covers mutable state only.
"""
import re
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def runtime_initializer():
    from portable_lazy_bank_specs import BANKED_FIELDS,DECLARATIONS
    source=(ROOT/'gpu/event_runtime.slang').read_text()
    body=source.split('struct Runtime\n{',1)[1].split('};',1)[0]
    body=re.sub(r'//[^\n]*','',body)
    # Optional wire variants initialize their own scoped state. Keep the common
    # initializer identical; never silently skip an unknown declaration/guard.
    private = '#ifdef PORTABLE_WORLD_TEAM\n    uint teamEvent;\n#endif'
    if body.count(private) != 1:
        raise ValueError('Unknown private Runtime declaration')
    body=body.replace(private,'')
    bank_guard=re.compile(r'#ifndef PORTABLE_WORLD_PROJECTILE\n(.*?)\n#endif',re.S)
    guarded=bank_guard.findall(body)
    normalize=lambda text:re.sub(r'\s+','',text)
    if sorted(map(normalize,guarded))!=sorted(map(normalize,DECLARATIONS)):
        raise ValueError('Unknown private Runtime bank declarations')
    body=bank_guard.sub(lambda m:m[1],body)
    if '#' in body:raise ValueError('Unknown Runtime preprocessor directive')
    scalars=[];arrays=defaultdict(list)
    for declaration in body.split(';'):
        if not declaration.strip():continue
        match=re.fullmatch(r'\s*(uint64_t|uint|int|Definition)\s+(.+?)\s*',declaration,re.S)
        if not match:raise ValueError('Unknown Runtime declaration: '+declaration)
        for item in match[2].split(','):
            field=re.fullmatch(r'\s*(\w+)(?:\[([^\]]+)\])?\s*',item)
            if not field:raise ValueError('Unknown Runtime field: '+item)
            name,size=field.groups()
            if match[1]=='Definition':
                if (name,size)!=('defs','P_DEFINITIONS'):raise ValueError('Unknown compound Runtime member')
                continue
            if size:arrays[size].append(name)
            else:scalars.append(name)
    lines=['// Generated from Runtime in event_runtime.slang by portable_runtime_layout.py.',
           '// Immutable definitions remain in the GPU input buffer.',
           '[noinline]','void initializeRuntime(inout Runtime s)','{']
    lines += [f'    s.{name} = 0;' for name in scalars]
    for size,names in arrays.items():
        banked=all(name in BANKED_FIELDS for name in names)
        if any(name in BANKED_FIELDS for name in names) and not banked:raise ValueError('Mixed Runtime bank array group')
        if banked:lines+=['#ifndef PORTABLE_WORLD_PROJECTILE']
        lines += [f'    [loop] for (uint index = 0; index < {size}; index++)','    {']
        lines += [f'        s.{name}[index] = 0;' for name in names]
        lines += ['    }']
        if banked:lines+=['#endif']
    return '\n'.join(lines+['}',''])
