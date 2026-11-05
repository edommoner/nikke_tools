// Product BODY/PART specialization: retain typed-axis carriers alongside the
// existing native shot-group executor. No typed target or damage model exists
// in this world; the GPU verifies that fact before executing any command.
#define portableEvents unusedProductGroupEntry
#include "product_group_battle_entry.slang"
#undef portableEvents

#include "product_group_target_axes.slang"

#if !defined(PORTABLE_PRODUCT_ADD_EXECUTOR) && !defined(PORTABLE_PRODUCT_EXTERNAL_EXECUTOR)
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    uint input=1+id.x*104672,output=id.x*1048576; WORLD_TEAM_INPUT(input,output)
    for(uint i=786432;i<1048576;i++) results[output+i]=0;
    initializeRuntime(runtimeStates[id.x]);bool ready;
    initializePortableProgram(runtimeStates[id.x],input,output,ready);if(!ready) return;
    if(!validProductGroupTargetAxes(runtimeStates[id.x])) { results[output]=64;return; }
    uint queries;executePortableCommands(runtimeStates[id.x],input,output,queries);
    writePortableProgram(runtimeStates[id.x],input,output,queries);
}

#endif
