StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
#include "binary64.slang"
#include "coordinate_arc_sets.slang"
#include "coordinate_arc_arena_view.slang"
#include "coordinate_arc_arena_ops.slang"
static const uint ARENA_PREFIX=4100U;
static const uint ARENA_OUTPUT=ARENA_PREFIX+ARC_ARENA_WORDS;
uint64_t arenaRead(uint at){return uint64_t(commands[at])|(uint64_t(commands[at+1])<<32);}
bool arenaLoad(uint base,uint count,inout ArcArenaView value)
{
    arena_coordinateArcClear(value);if(count>512)return false;
    uint64_t tau=uint64_t(0x401921fbU)<<32|uint64_t(0x54442d18U);
    for(uint i=0;i<512;i++)
    {
        uint64_t s=arenaRead(base+i*4),e=arenaRead(base+i*4+2);
        if(i>=count){if(s!=0||e!=0)return false;continue;}
        if(!f64Finite(s)||!f64Finite(e)||f64Less(s,0)||!f64Less(s,e)||f64Less(tau,e))return false;
        if(i!=0&&!f64Less(value.end[i-1],s))return false;
        arena_coordinateArcAppend(value,s,e);
    }
    return true;
}
bool arenaAlgebra(uint input,uint output)
{
    ArcArenaView a=arcArenaView(output,ARENA_PREFIX,0),b=arcArenaView(output,ARENA_PREFIX,1),value=arcArenaView(output,ARENA_PREFIX,2);
    bool valid=commands[input]==0x43415243U&&commands[input+1]==1&&commands[input+2]>=1&&commands[input+2]<=3;
    for(uint i=5;i<8;i++)if(commands[input+i]!=0)valid=false;
    if(!valid||!arenaLoad(input+8,commands[input+3],a)||!arenaLoad(input+2056,commands[input+4],b))return false;
    uint op=commands[input+2];
    if(op==1)arena_coordinateArcUnion(a,b,value);
    else if(op==2)arena_coordinateArcIntersect(a,b,value);
    else arena_coordinateArcSubtract(a,b,value);
    if(value.overflow||results[output+ARENA_PREFIX]!=0)return false;
    results[output+1]=0x43415243U;results[output+2]=value.count;
    for(uint i=0;i<value.count;i++)
    {results[output+4+i*4]=uint(value.start[i]);results[output+5+i*4]=uint(value.start[i]>>32);results[output+6+i*4]=uint(value.end[i]);results[output+7+i*4]=uint(value.end[i]>>32);}
    return true;
}
// Storage safety diagnostics are separate from interval/geometry calculations.
bool arenaDiagnostic(uint input,uint output)
{
    uint mode=commands[input+2];if(commands[input+1]!=1||mode<1||mode>5)return false;
    for(uint i=3;i<4104;i++)if(commands[input+i]!=0)return false;
    ArcArenaView a=arcArenaView(output,ARENA_PREFIX,0),b=arcArenaView(output,ARENA_PREFIX,1);
    arena_coordinateArcClear(a);arena_coordinateArcClear(b);
    a.count=1;a.end[0]=uint64_t(0x01234567U)<<32|uint64_t(0x89abcdefU);
    uint64_t observed=0;
    if(mode==1){a.start[1023]=uint64_t(0xfedcba98U)<<32|uint64_t(0x76543210U);observed=a.start[1023];}
    else if(mode==2)a.start[1024]=0;
    else if(mode==3){ArcArenaView invalid=arcArenaView(output,ARENA_PREFIX,8);}
    else if(mode==4)arena_coordinateArcUnion(a,b,a);
    else observed=a.start[1024];
    results[output+1]=0x41525631U;results[output+2]=mode;results[output+3]=results[output+ARENA_PREFIX];
    results[output+4]=uint(a.end[0]);results[output+5]=uint(a.end[0]>>32);
    results[output+6]=uint(observed);results[output+7]=uint(observed>>32);results[output+8]=a.count;
    return true;
}
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*4104,output=id.x*ARENA_OUTPUT;
    for(uint i=0;i<ARENA_OUTPUT;i++)results[output+i]=0;
    bool diagnostic=commands[input]==0x41525631U;
    bool valid=diagnostic?arenaDiagnostic(input,output):arenaAlgebra(input,output);
    if(!valid){for(uint i=0;i<ARENA_OUTPUT;i++)results[output+i]=0;results[output]=64;}
    else for(uint i=ARENA_PREFIX;i<ARENA_OUTPUT;i++)results[output+i]=0;
}
