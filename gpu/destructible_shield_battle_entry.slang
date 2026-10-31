#include "destructible_shield_frame_hooks.slang"
#define portableEvents unusedNormalBattleEntry
#include "world_projectile_chain_entry.slang"
#undef portableEvents
#include "destructible_shield_frame_impl.slang"
#ifndef PORTABLE_PRODUCT_ADD_EXECUTOR
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0]) return;
    uint input=1+id.x*110112,output=id.x*1048576; WORLD_TEAM_INPUT(input,output)
    for(uint i=786432;i<1048576;i++) results[output+i]=0;
    initializeRuntime(runtimeStates[id.x]);bool ready;
    initializePortableProgram(runtimeStates[id.x],input,output,ready);if(!ready) return;
    if(!initializeDestructibleBattle(runtimeStates[id.x])||!validBattleModifierAxes(runtimeStates[id.x])||!validShieldBattleRoutes(runtimeStates[id.x])) { results[output]=64;return; }
    uint queries;executePortableCommands(runtimeStates[id.x],input,output,queries);
    writePortableProgram(runtimeStates[id.x],input,output,queries);
}

#endif
