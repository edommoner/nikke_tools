StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
#include "interrupt_packet_codec.slang"
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    uint input=1+id.x*136,out=id.x*786432,at=out+8,order[128];
    for(uint i=0;i<128;i++) order[i]=commands[input+8+i];
    uint count=commands[input],birth=commands[input+1],low=commands[input+2],high=commands[input+3],reach=commands[input+4],frozen=commands[input+5],mutation=commands[input+6];
    if(commands[input+7]!=0)
    {
        uint prior[128];for(uint i=0;i<128;i++) prior[i]=127-i;
        if(!storeInterruptPacket(at,prior,128,0xffffffffU,0xdeadbeefU,0xfeedfaceU,4,true)) { results[out]=32;return; }
    }
    if(frozen>1||!storeInterruptPacket(at,order,count,birth,low,high,reach,frozen!=0)) { results[out]=64;return; }
    if(mutation==1) results[at+37]^=4;
    else if(mutation==2) results[at+2]^=1;
    else if(mutation==3) results[at+6]^=127;
    else if(mutation==4) results[at]=129;
    else if(mutation==5) results[at+36]=5;
    else if(mutation==6) results[at+33]^=0x80000000U;
    else if(mutation==7) results[at+1]=1;
    if(!validInterruptPacket(at)) { results[out]=64;return; }
    for(uint i=0;i<count;i++) results[out+64+i]=interruptPacketSlot(at,i);
}
