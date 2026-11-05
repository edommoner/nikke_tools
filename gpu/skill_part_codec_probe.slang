#define PORTABLE_WORLD_RELOAD
#include "portable_schema.slang"
StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
uint64_t sourceNumber(uint at) { return uint64_t(results[at])|(uint64_t(results[at+1])<<32); }
void storeNumber(uint at,uint64_t value) { results[at]=uint(value);results[at+1]=uint(value>>32); }
#include "skill_part_receipt.slang"
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*6,output=id.x*P_OUTPUT_WORDS,index=commands[input];
    if(index>=P_LANDINGS) { results[output]=64;return; }
    uint at=output+P_LANDING_STATE_BASE+index*P_LANDING_WORDS;
    results[at+7]=commands[input+5];
    storeSkillPartAmount(at,uint64_t(commands[input+1])|(uint64_t(commands[input+2])<<32));
    uint64_t first=loadSkillPartAmount(at);
    storeSkillPartAmount(at,uint64_t(commands[input+3])|(uint64_t(commands[input+4])<<32));
    uint64_t second=loadSkillPartAmount(at);
    results[output]=0;storeNumber(output+1,first);storeNumber(output+3,second);results[output+5]=results[at+7];
}
