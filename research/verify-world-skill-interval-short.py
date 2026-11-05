"""Full native battle/trace plus directly observed periodic skill clocks."""
import array
import importlib.util
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('interval_base',ROOT/'research/verify-world-projectile-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross


def prepare():
    from portable_skill_interval_cases import fixtures,negative_inputs
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case)
        entries.append((case['name'],words,(case,metadata,bindings)))
    entries+=negative_inputs(suite.compile_case)
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def clock_state(block,metadata):
    from portable_specs import LIMITS as L
    def number(at):return struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    rows=[]
    for row in range(len(metadata['effects'])):
        at=L['PERIOD_STATE_BASE']+row*4
        # Only initialized clocks have a positive previous interval. The input
        # definition need not be copied into the native expected value.
        interval=number(at+2)
        if interval!=0:rows.append(dict(row=row,due=number(at),interval=interval))
    return rows


def compare(block,domain):
    case,metadata,bindings=domain;native,trace=suite.inspect_native(case)
    actual=suite.decoded(block,metadata,case,bindings);actual['skill_clocks']=clock_state(block,metadata)
    changed=[k for k in native if k!='scope' and actual[k]!=native[k]]
    if block[0]!=0 or changed:raise ValueError(str(dict(status=block[0],changed=changed,clocks=actual['skill_clocks'],expected=native['skill_clocks'])))
    if suite.reload.charge.team.skill_trace(block,metadata)!=trace:raise ValueError('Periodic skill trace differs')
    return dict(battle=native,skill_trace=trace)
