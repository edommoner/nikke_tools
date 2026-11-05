"""Full battle/trace comparator plus actual per-name critical accumulator state."""
import array
import importlib.util
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('critical_base',ROOT/'research/verify-world-projectile-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross


def prepare():
    from portable_skill_critical_cases import fixtures,negative_inputs
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case)
        entries.append((case['name'],words,(case,metadata,bindings)))
    entries+=negative_inputs(suite.compile_case)
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def critical_state(block,metadata):
    from portable_specs import LIMITS as L
    names={v:k for k,v in metadata['states'].items()};rows=[]
    for owner in range(5):
        for name in range(L['DEFINITIONS']):
            at=L['SKILL_CRITICAL_STATE_BASE']+(owner*L['DEFINITIONS']+name)*3
            if block[at]==0:continue
            if block[at]!=1:raise ValueError('Invalid critical accumulator presence')
            value=struct.unpack('<d',struct.pack('<II',*block[at+1:at+3]))[0]
            rows.append(dict(owner=owner,name=names[name],value=value))
    return sorted(rows,key=lambda r:(r['owner'],r['name']))


def compare(block,domain):
    case,metadata,bindings=domain;native,trace=suite.inspect_native(case)
    actual=suite.decoded(block,metadata,case,bindings);actual['skill_critical']=critical_state(block,metadata)
    changed=[k for k in native if k!='scope' and actual[k]!=native[k]]
    if block[0]!=0 or changed:raise ValueError(str(dict(status=block[0],changed=changed,critical=actual['skill_critical'],expected=native['skill_critical'])))
    if suite.reload.charge.team.skill_trace(block,metadata)!=trace:raise ValueError('Critical-context skill trace differs')
    return dict(battle=native,skill_trace=trace)
