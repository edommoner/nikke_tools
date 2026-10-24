#define portableEvents legacyPacketIntegerEvents
#include "event_runtime.slang"
#undef portableEvents
#include "packet_integer_sum.slang"
#include "packet_integer_layout.slang"
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*PI_INPUT,output=id.x*PI_OUTPUT;
    for(uint i=0;i<PI_OUTPUT;i++)results[output+i]=0;
    uint n=commands[input+2],multiplier=commands[input+3];
    bool valid=commands[input]==PI_MAGIC&&commands[input+1]==1&&n<=PI_TERMS&&multiplier>0&&multiplier<=PI_MAX_MULTIPLIER;
    for(uint i=4;i<PI_HEADER;i++)if(commands[input+i]!=0)valid=false;
    PacketIntegerSum sum=packetIntegerZero();
    for(uint i=0;i<PI_TERMS;i++)
    {
        uint at=input+PI_HEADER+i*2;uint64_t value=uint64_t(commands[at])|(uint64_t(commands[at+1])<<32);
        if(i<n){if(valid&&!packetIntegerAddAmount(sum,value))valid=false;}
        else if(value!=0)valid=false;
    }
    if(!valid){results[output]=64;return;}
    sum=packetIntegerMultiply(sum,multiplier);uint64_t rounded=packetIntegerBinary64(sum);
    results[output+1]=PI_MAGIC;results[output+2]=uint(sum.low);results[output+3]=uint(sum.low>>32);
    results[output+4]=uint(sum.high);results[output+5]=uint(sum.high>>32);
    results[output+6]=uint(rounded);results[output+7]=uint(rounded>>32);
}
