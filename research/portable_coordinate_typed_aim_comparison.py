"""Every frame's frozen candidates plus the actual 9-bit focus snapshot."""
import struct
from portable_specs import LIMITS as L
BASE=1769856;HEAD=BASE+220224;END=HEAD+544

def words(native,slots):
    frames=[]
    for f in native['coordinate_typed_aim']:
        rows=[[slots[c['label']],c['handle'][2],c['key'][2],c['handle'][1]] for c in f['candidates']]
        frames.append((f,rows,[*struct.unpack('<II',struct.pack('<d',f['time'])),len(rows),int(f['canonical_has_adds']),*sum(rows,[])]))
    return frames

def compare(block,domain,native):
    slots=domain[3]['typed_aim_slots'];frames=words(native,slots);assert frames
    a=0xcbf29ce484222325;b=0x84222325cbf29ce4;mask=(1<<64)-1
    for _,_,values in frames:
        for word in values:a=((a^word)*0x100000001b3)&mask;b=(((b<<7)|(b>>57))^(word*0x9e3779b185ebca87))&mask
    f,rows,_=frames[-1];header=[0]*32
    header[:12]=[0x43544131,1,len(frames),slots[f['candidate']] if f['candidate'] else 0,*struct.unpack('<II',struct.pack('<d',f['time'])),len(rows),int(f['canonical_has_adds']),a&0xffffffff,a>>32,b&0xffffffff,b>>32]
    assert list(block[HEAD:HEAD+32])==header,'Frozen typed aim frame stream'
    assert list(block[HEAD+32:END])==sum(rows,[])+[0]*(512-len(rows)*4),'Frozen final typed aim generations'
    assert not any(block[END:]),'Unused typed aim tail'
    aims=native['coordinate_aim']['frames'][-1];at=L['FOCUS_STATE_BASE']
    mapping={r['label']:r['slot'] for r in domain[3]['rows']};mapping.update({'':0,'core':128,'__enemy__:*':0});mapping.update(slots);mapping['__enemy__:*']=domain[3]['typed_aim_add_slot']
    packed=sum(mapping[aim['target']]<<(9*who) for who,aim in enumerate(aims['aims']))
    assert list(block[at:at+7])==[packed&0xffffffff,packed>>32,aims['camera_mask'],int(aims['full_burst']),len(frames),sum(1<<who for who in range(5) if aims['camera_mask']&(1<<who) or aims['full_burst']),0x46414331],'Nine-bit typed aim focus IDs'
    return dict(frames=len(frames),last_focus_ids=[mapping[a['target']] for a in aims['aims']])
