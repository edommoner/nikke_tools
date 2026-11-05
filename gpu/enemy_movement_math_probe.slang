#include "binary64.slang"
#include "enemy_movement_math.slang"
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
uint64_t motionRead(uint p){return uint64_t(commands[p])|(uint64_t(commands[p+1])<<32);}
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint p=1+id.x*24,o=id.x*16;
    for(uint i=0;i<16;i++)results[o+i]=0;
    bool valid=commands[p]==0x454d4d31U&&commands[p+1]==1&&commands[p+2]<=3&&commands[p+3]<=1;
    for(uint i=4;i<18;i+=2)if(!f64Finite(motionRead(p+i)))valid=false;
    for(uint i=18;i<24;i++)if(commands[p+i]!=0)valid=false;
    uint64_t dt=motionRead(p+16);if(f64Less(dt,0))valid=false;
    if(!valid){results[o]=64;return;}
    uint64_t x,y;
    if(!enemyMovementStep(motionRead(p+4),motionRead(p+6),motionRead(p+8),motionRead(p+10),
        motionRead(p+12),motionRead(p+14),dt,(commands[p+2]&1)!=0,(commands[p+2]&2)!=0,commands[p+3],x,y))
    {results[o]=16;return;}
    results[o+1]=0x454d4d31U;results[o+2]=commands[p+2];results[o+3]=commands[p+3];
    results[o+4]=uint(x);results[o+5]=uint(x>>32);results[o+6]=uint(y);results[o+7]=uint(y>>32);
}
