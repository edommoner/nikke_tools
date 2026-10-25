"""Strict retained coordinate-shot identities; full damage uses packet history."""
import array,struct
from portable_projectile_specs import HEAD,TRACE,TRACE_COUNT
def legacy_view(block,shots,mechanics):
    count=min(len(shots),TRACE_COUNT);omitted=max(0,len(shots)-TRACE_COUNT)
    assert block[HEAD]==0x57505231,'Coordinate projectile history magic'
    assert block[HEAD+1]==count,'Coordinate retained projectile history count'
    assert block[HEAD+2]==omitted,'Coordinate omitted projectile history count'
    assert block[HEAD+3]<=1 and not any(block[HEAD+4:HEAD+16]),'Coordinate projectile reserved fields'
    for i,shot in enumerate(shots[:count]):
        assert shot['kind'] in ('_fire','_charge_fire'),'Actual native shot method required'
        mode=1 if shot['kind']=='_charge_fire' else 2 if mechanics[shot['weapon_type']]['type']=='auto_warmup' else 0
        when=list(struct.unpack('<II',struct.pack('<d',shot['time'])))
        expected=[shot['owner'],mode,*when,shot['pellets'],shot['muzzles'],0,0,0,0,0,0,0,0,0,0]
        assert list(block[TRACE+i*16:TRACE+(i+1)*16])==expected,'Every retained native coordinate shot identity'
    assert not any(block[TRACE+count*16:TRACE+TRACE_COUNT*16]),'Unused coordinate projectile history'
    if not omitted:return block
    copy=array.array('I',block);copy[HEAD+2]=0;return copy
