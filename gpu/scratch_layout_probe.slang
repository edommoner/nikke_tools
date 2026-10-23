#define PORTABLE_WORLD_RELOAD
#include "portable_schema.slang"
#include "portable_scratch_layout.slang"
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
void storeNumber(uint at,uint64_t value) { results[at]=uint(value);results[at+1]=uint(value>>32); }
uint64_t sourceNumber(uint at) { return uint64_t(results[at])|(uint64_t(results[at+1])<<32); }
#include "skill_part_receipt.slang"
uint marker(uint seed,uint tag,uint index) { return seed^(tag*0x9e3779b9U+index); }
void paint(uint at,uint count,uint seed,uint tag)
{ for(uint i=0;i<count;i++) results[at+i]=marker(seed,tag,i); }
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    uint input=1+id.x*4,out=id.x*786432,mode=commands[input],seed=commands[input+1];
    if(mode>2 || commands[input+2]!=0 || commands[input+3]!=0) { results[out]=64;return; }
    paint(out+P_FOCUS_STATE_BASE,P_FOCUS_STATE_WORDS,seed,1);
    paint(out+P_NATIVE_QUERY_BASE,P_NATIVE_QUERY_HEADER_WORDS,seed,2);
    for(uint cell=0;cell<P_NATIVE_QUERY_COUNT;cell++)
        for(uint word=0;word<P_NATIVE_QUERY_CELL_WORDS;word++)
            results[nativeNumericCell(out,cell)+word]=marker(seed,3,cell*P_NATIVE_QUERY_CELL_WORDS+word);
    paint(out+P_ORDERED_HISTORY_BASE,P_ORDERED_HISTORY_WORDS,seed,4);
    for(uint slot=0;slot<2048;slot++)
    {
        uint64_t value=uint64_t(marker(seed,5,slot*2))|(uint64_t(marker(seed,5,slot*2+1))<<32);
        storeSkillPartAmount(out+P_LANDING_STATE_BASE+slot*P_LANDING_WORDS,value);
    }
    paint(out+785424,10,seed,6);
    if(mode==1) paint(out+P_NATIVE_DIAG_BASE,P_NATIVE_DIAG_WORDS,seed,7);
    if(mode==2) paint(out+771072,8+512*20,seed,8);
    results[out+1]=mode;results[out+2]=seed;results[out+3]=P_NATIVE_QUERY_COUNT;
    uint64_t first=loadSkillPartAmount(out+P_LANDING_STATE_BASE),last=loadSkillPartAmount(out+P_LANDING_STATE_BASE+2047*P_LANDING_WORDS);
    storeNumber(out+4,first);storeNumber(out+6,last);
}
