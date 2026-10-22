// Compiler diagnostic only. Runtime is deliberately treated as external state.
// Never launch as a battle: no initialization/admission or final serialization.
#define portableEvents unusedFullPortableEvents
#include "world_entry_reload_resident_entry.slang"
#undef portableEvents

[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id : SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    uint input=1+id.x*P_INPUT_WORDS,output=id.x*P_OUTPUT_WORDS;
    WORLD_TEAM_INPUT(input,output)
    uint queries;
    executePortableCommands(runtimeStates[id.x],input,output,queries);
    results[output+1]=queries;
}
