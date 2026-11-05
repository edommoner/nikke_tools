#define PORTABLE_RESIDENT_RUNTIME
#define portableEvents portableBattleUnused
#include "world_projectile_entry.slang"
#undef portableEvents

[noinline]
void residentProbe(inout Runtime s,uint input,uint output)
{
    initializeRuntime(s);
    results[output]=s.alive[511];
    results[output+1]=s.pendingRow[0];
    results[output+2]=uint(s.hpSnapshot[511]);
    results[output+8]=uint(s.hpSnapshot[511]>>32);
    s.alive[511]=commands[input];
    s.pendingRow[0]=commands[input+1];
    s.hpSnapshot[511]=uint64_t(commands[input+2])|(uint64_t(commands[input+3])<<32);
    results[output+3]=s.alive[511];
    results[output+4]=s.pendingRow[0];
    storeNumber(output+5,s.hpSnapshot[511]);
}
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x!=0) return;
    for(uint lane=0;lane<commands[0];lane++)
    {
        runtimeStates[lane].alive[511]=0xdeadbeef;
        runtimeStates[lane].pendingRow[0]=0xffffffff;
        runtimeStates[lane].hpSnapshot[511]=0xffffffffffffffffUL;
        residentProbe(runtimeStates[lane],1+lane*P_INPUT_WORDS,lane*P_OUTPUT_WORDS);
    }
    for(uint lane=0;lane<commands[0];lane++) results[lane*P_OUTPUT_WORDS+7]=runtimeStates[lane].alive[511];
}
