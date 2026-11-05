"""All typed physical packets, state and whole-stream hash against real native."""
import array,hashlib,struct,importlib.util
from pathlib import Path
from portable_coordinate_typed_specs import COORDINATE_OUTPUT_WORDS,OUTPUT_WORDS,regions
BASE=COORDINATE_OUTPUT_WORDS;HEAD=BASE+170976;KEEP=2048;WORDS=24

def double(value):return list(struct.unpack('<II',struct.pack('<d',value)))
def rows(native):
    result=[]
    for a in native['attacks']:
        r=a['receipts'][0];kind,identity,generation=r['handle'];tag=a['hit_tag']
        pellet=int(tag.rsplit(':',1)[1]) if 'pellet:' in tag else 0
        result.append([a['attack_id'],a['owner'],kind,identity,generation,r['slot'],
            *double(a['time']),*double(a['coefficient']),*double(a['damage']),*double(r['took']),
            int(r['delivered']),int(r['broken']),a['family'],int(a['extra']),int(a['critical']),
            int(a['weapon_mode_skill']),a['shot_identity'],pellet,0,0])
    return result

def compare(block,case,native):
    assert len(block)==OUTPUT_WORDS and block[0]==0
    s=importlib.util.spec_from_file_location('ctw_typed_state_decoder',Path(__file__).with_name('verify-destructible-battle-short.py'));decoder=importlib.util.module_from_spec(s);s.loader.exec_module(decoder)
    view=[0]*786432+list(block[BASE:]);actual=decoder.decode(view,(case,{},()))
    assert actual==native['typed'],('typed physical state',case['name'],actual,native['typed'])
    expected=rows(native);words=sum(expected,[]);raw=array.array('I',words)
    if __import__('sys').byteorder!='little':raw.byteswap()
    digest=list(struct.unpack('>8I',hashlib.sha256(raw.tobytes()).digest()))
    count=len(expected);pending=(count*WORDS)%16;header=[0]*64
    header[:8]=[0x43545731,1,count,min(count,KEEP),KEEP,WORDS,len(native['shots']),pending]
    header[8:16]=digest;header[32:40]=digest;header[40]=1
    def swap(v):return int.from_bytes(v.to_bytes(4,'little'),'big')
    tail=[swap(v) for v in words[-pending:]] if pending else []
    tail.append(0x80000000);tail.extend([0]*(14-len(tail)));bits=count*WORDS*32;tail.extend([bits>>32,bits&0xffffffff]);header[16:32]=tail
    assert list(block[HEAD:HEAD+64])==header,('typed physical stream header',case['name'])
    end=HEAD+64+min(count,KEEP)*WORDS
    assert list(block[HEAD+64:end])==sum(expected[:KEEP],[]),'Complete retained typed physical receipts'
    assert not any(block[end:]),'Unused typed physical history and overflow scratch'
    # Weapon-only routes own DFS scratch, but cannot write prior skill receipt
    # banks or any clear-only owner. No unused skill route is certified here.
    for region in regions()[0]:
        if region.domain=='output' and ('reserved' in region.name or region.name.endswith('attack-receipts')):
            assert not any(block[region.base:region.end]),region.name
    from portable_specs import LIMITS
    at=LIMITS['COUNTER_CONTEXT_BASE'];assert not any(block[at:at+1096]),'Typed counter context leaked'
    return dict(typed_packets=count,retained=min(count,KEEP),all_packets_sha256=hashlib.sha256(raw.tobytes()).hexdigest())
