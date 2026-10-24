"""Real expanded packet parent quantity, retaining all physical23 cases."""
import array,importlib.util,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('quantity_physical_parent',ROOT/'research/verify-coordinate-physical-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_quantity_cases import fixtures
from world_coordinate_packet_quantity_native import observe
from portable_normal_spread_specs import check_schema as check_spread
SOURCE=parent.SOURCE;INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
suite=parent.suite;cross=parent.cross;compile_case=parent.compile_case;validate_rejection=parent.validate_rejection

def prepare():
    check_spread(ROOT);entries,_=parent.prepare()
    for case in fixtures():
        words,meta,bindings,descriptors=compile_case(case);entries.append((case['name'],words,(case,meta,bindings,descriptors)))
    raw=array.array('I',[len(entries)])
    for _,words,_ in entries:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()

def native_reference(domain):
    case=domain[0]
    if not case.get('observe_coordinate_landings'):return parent.native_reference(domain)
    result=observe(case);names=parent.roster_names(case)
    for notice in result['full_charge_quantities']:
        rows=[r for r in result['physical_pellets'] if r['time']==notice['time'] and r['owner']==names[notice['owner']]]
        muzzles=case['combat']['weapons'][notice['owner']]['muzzles']
        total=sum(p['damage'] for r in rows for p in r['packets'])
        assert notice['dealt']==total/muzzles,(case['name'],'exact expanded parent quantity')
    return result

def compare(block,domain):
    case,meta,bindings,descriptors=domain
    if not case.get('observe_coordinate_landings'):return parent.compare(block,domain)
    return compare_expected(block,domain,native_reference(domain))

def compare_expected(block,domain,expected,*,verify_parent_quantity=True):
    case,meta,bindings,descriptors=domain
    parent.codec.compare_expected(block[:786432],domain[:3],dict(battle=expected['battle'],skill_trace=expected['skill_trace']))
    from portable_coordinate_physical_specs import LAYOUT
    last={notice['owner']:notice for notice in expected['full_charge_quantities']} if verify_parent_quantity else {}
    for owner,notice in last.items():
        at=LAYOUT['BANK']+owner*LAYOUT['BANK_WORDS']+14
        assert list(block[at:at+2])==list(struct.unpack('<II',struct.pack('<d',notice['dealt']))),(case['name'],'captured exact parent bits',owner)
    by_name={r['label']:r for r in descriptors['rows']};packets=[];cp=parent.CP
    for packet in expected['landed_packets']:
        target=by_name.get(packet['target']);slot=target['slot'] if target else 0;kind=target['kind'] if target else 0
        packets.append([packet['owner'],slot,kind,packet['generation'],*struct.unpack('<II',struct.pack('<d',packet['time'])),*struct.unpack('<II',struct.pack('<d',float(packet['damage']))),int(packet['extra']),0,0,0])
    assert block[cp['BASE']]==0x43534b31 and block[cp['BASE']+1]==1
    assert block[cp['BASE']+2]==len(packets),(case['name'],'physical and child packet count')
    start=cp['TRACE'];end=start+len(packets)*cp['TRACE_WORDS']
    assert list(block[start:end])==sum(packets,[]),(case['name'],'ordered physical and child packet trace')
    assert not any(block[end:start+cp['TRACE_COUNT']*cp['TRACE_WORDS']])
    return expected
