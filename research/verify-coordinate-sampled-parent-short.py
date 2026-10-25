"""Sampled parent packets reuse the existing physical battle and child decoder."""
import array,importlib.util,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('sampled_parent',ROOT/'research/verify-coordinate-sampled-battle-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_sampled_parent_cases import fixtures
from world_coordinate_sampled_parent_native import observe
from world_coordinate_aim_native import capture
from portable_coordinate_sampling_bank import LAYOUT as BANK
SOURCE='gpu/world_coordinate_sampling_parent_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
suite=parent.suite;cross=parent.cross;compile_case=parent.compile_case;validate_rejection=parent.validate_rejection
def prepare():
    rows,_=parent.prepare()
    for c in fixtures():
        w,m,b,d=compile_case(c);rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
def native_reference(domain):
    if not domain[0].get('sampled_parent'):return parent.native_reference(domain)
    with capture(domain[0]) as aim:n,t=observe(domain[0])
    n['coordinate_aim']=aim;return n
def compare(block,domain):
    if not domain[0].get('sampled_parent'):return parent.compare(block,domain)
    return compare_observed(block,domain,native_reference(domain))
def compare_observed(block,domain,n,*,check_parent=True,trace_view=None,sampled_burst_totals=False,sampled_manual=False):
    c,m,b,d=domain
    from portable_roster_team_history import legacy_view
    view,battle=legacy_view(block[:786432],n['battle'],parent.parent.L['WORLD_TEAM_HEAD_BASE'])
    # Keep the legacy decoder and every battle field; replace only the explicit
    # integer total after independently checking the retained binary64 stream.
    codec=parent.parent.physical.codec
    actual=codec.suite.decoded(view,m,c,b)
    actual['healing_storage']=codec.storage.decoded_storage(view,m,c)
    from portable_sampled_damage_totals import exact_damage
    kinds={r['label']:r['kind'] for r in d['rows']}
    if c.get('sampled_delivery'):kinds.update({actor.label:int(actor.kind) for actor in b})
    actual['damage']=exact_damage(block,actual['damage'],n['landed_packets'],kinds,sampled_burst=sampled_burst_totals,sampled_manual=sampled_manual)
    changed=[key for key in battle if key!='scope' and actual[key]!=battle[key]]
    assert block[0]==0 and not changed,(c['name'],block[0],changed)
    expected_trace=n['skill_trace'] if trace_view is None else trace_view
    assert codec.suite.reload.charge.team.skill_trace(view,m)==expected_trace,(c['name'],'skill trace')
    parent.parent.parent.parent.compare_aim(block,domain,n['coordinate_aim'])
    by_name={r['label']:r for r in d['rows']};trace=[]
    if c.get('sampled_delivery'):by_name.update({actor.label:dict(slot=slot,kind=int(actor.kind)) for slot,actor in enumerate(b)})
    for p in n['landed_packets']:
        if c.get('sampled_delivery') and p['target']:assert p['target'] in by_name,'Every actual routed label must bind to one typed actor'
        target=by_name.get(p['target']);slot=target['slot'] if target else 0;kind=target['kind'] if target else 0
        trace.append([p['owner'],slot,kind,p['generation'],*parent.parent.double_words(p['time']),*parent.parent.double_words(p['damage']),int(p['extra']),0,0,0])
    cp=parent.parent.physical.CP;start=cp['TRACE'];end=start+len(trace)*12
    assert block[cp['BASE']+2]==len(trace) and list(block[start:end])==sum(trace,[]),'Actual physical and parent child delivery'
    assert not any(block[end:start+cp['TRACE_COUNT']*12]),'Unused child/physical trace'
    rng=BANK['RNG'];state=n['physical_rng'];assert block[rng]==state['index'] and list(block[rng+8:rng+632])==state['state'],'Parent fixed packets must not consume critical RNG'
    assert block[rng+1]==parent.verify(c,n)['physical_rng_words']
    if not check_parent:return n
    h=BANK['META'];who=block[h+54];when=struct.unpack('<d',struct.pack('<II',*block[h+10:h+12]))[0]
    notices=[x for x in n['full_charge_quantities'] if x['owner']==who and x['time']==when]
    assert notices,'Last shot must have a real native full-charge quantity'
    expected=notices[-1]['dealt'];assert list(block[h+14:h+16])==parent.parent.double_words(expected),'One-round parent quantity bits'
    names=parent.parent.roster_names(c);total=sum(p['damage'] for row in n['physical_pellets'] if row['owner']==names[who] and row['time']==when for p in row['packets'])
    assert sum(int(block[h+50+i])<<(32*i) for i in range(4))==total,'Exact128 packet sum before division'
    return n
