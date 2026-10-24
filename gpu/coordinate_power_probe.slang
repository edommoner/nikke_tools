#define portableEvents legacyCoordinatePowerEvents
#include "event_runtime.slang"
#undef portableEvents
#include "coordinate_power_v1.slang"
uint64_t powerRead(uint at){return uint64_t(commands[at])|(uint64_t(commands[at+1])<<32);}
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*8,output=id.x*8;for(uint i=0;i<8;i++)results[output+i]=0;
    if(commands[input]!=0x43505631U||commands[input+1]!=1||commands[input+2]!=0||commands[input+3]!=0){results[output]=64;return;}
    uint status;uint64_t value=coordinateUnitPower(powerRead(input+4),powerRead(input+6),status);
    if(status!=0){results[output]=64;return;}
    results[output+1]=0x43505631U;results[output+2]=uint(value);results[output+3]=uint(value>>32);
}
