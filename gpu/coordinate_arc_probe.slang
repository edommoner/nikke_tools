StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
#include "binary64.slang"
#include "coordinate_arc_sets.slang"
uint64_t arcRead(uint at){return uint64_t(commands[at])|(uint64_t(commands[at+1])<<32);}
bool arcLoad(uint base,uint count,out CoordinateArcSet value)
{
    coordinateArcClear(value);if(count>512)return false;
    uint64_t tau=uint64_t(0x401921fbU)<<32|uint64_t(0x54442d18U);
    for(uint i=0;i<512;i++)
    {
        uint64_t s=arcRead(base+i*4),e=arcRead(base+i*4+2);
        if(i>=count){if(s!=0||e!=0)return false;continue;}
        if(!f64Finite(s)||!f64Finite(e)||f64Less(s,0)||!f64Less(s,e)||f64Less(tau,e))return false;
        if(i!=0&&!f64Less(value.end[i-1],s))return false;
        coordinateArcAppend(value,s,e);
    }
    return true;
}
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*4104,output=id.x*4100;for(uint i=0;i<4100;i++)results[output+i]=0;
    CoordinateArcSet a,b,value;
    bool valid=commands[input]==0x43415243U&&commands[input+1]==1&&commands[input+2]>=1&&commands[input+2]<=3;
    for(uint i=5;i<8;i++)if(commands[input+i]!=0)valid=false;
    if(!valid||!arcLoad(input+8,commands[input+3],a)||!arcLoad(input+2056,commands[input+4],b)){results[output]=64;return;}
    uint op=commands[input+2];
    if(op==1)coordinateArcUnion(a,b,value);
    else if(op==2)coordinateArcIntersect(a,b,value);
    else coordinateArcSubtract(a,b,value);
    if(value.overflow){results[output]=64;return;}
    results[output+1]=0x43415243U;results[output+2]=value.count;
    for(uint i=0;i<value.count;i++)
    {results[output+4+i*4]=uint(value.start[i]);results[output+5+i*4]=uint(value.start[i]>>32);results[output+6+i*4]=uint(value.end[i]);results[output+7+i*4]=uint(value.end[i]>>32);}
}
