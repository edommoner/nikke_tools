"""Existing world comparator plus actual GPU/native carrier copy witnesses."""
import array,importlib.util,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('copy_base',ROOT/'research/verify-world-projectile-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross


def prepare():
    from portable_base_copy_cases import fixtures,negative_inputs
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case)
        entries.append((case['name'],words,(case,metadata,bindings,words)))
    entries+=negative_inputs(suite.compile_case)
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def copy_state(block,metadata,words):
    from portable_runtime import decode
    from portable_specs import LIMITS as L,FIELDS as F
    from portable_base_copy_specs import STATE_BASE
    number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    rows=[]
    for c in decode(block,metadata)['carriers']:
        d=L['DEFINITION_BASE']+c['definition']*L['DEFINITION_WORDS'];stat=words[d+F['STAT']]
        if not c['active'] or stat not in (85,86):continue
        at=STATE_BASE+c['slot']*6
        if block[at+5]!=c['order']:raise ValueError('Stale copy carrier generation')
        rows.append(dict(name=c['effect'],stat='atk_copy' if stat==85 else 'hp_copy',owner=words[d+F['OWNER']],
            recipients=[who for who in range(5) if c['recipients']&(1<<who)],stacks=c['stacks'],basis=number(at),
            source=None if block[at+4]==0 else block[at+4]-1,gift=number(at+2)))
    return sorted(rows,key=lambda r:(r['owner'],r['name'],r['stat'],r['recipients']))


def compare(block,domain):
    case,metadata,bindings,words=domain;native,trace=suite.inspect_native(case)
    actual=suite.decoded(block,metadata,case,bindings);actual['base_copies']=copy_state(block,metadata,words)
    changed=[k for k in native if k!='scope' and actual[k]!=native[k]]
    if block[0]!=0 or changed:raise ValueError(str(dict(status=block[0],changed=changed,copies=actual['base_copies'],expected=native['base_copies'])))
    if suite.reload.charge.team.skill_trace(block,metadata)!=trace:raise ValueError('Base-copy skill trace differs')
    return dict(battle=native,skill_trace=trace)
