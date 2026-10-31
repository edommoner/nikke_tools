// The product prefix owns battle calculation. Reuse the existing ADD cursor,
// queue ordering, source map and final-shot retirement without a second clock.
#include "world_add_attack_cursor.slang"
#include "world_add_attack_battle_runtime.slang"
#include "add_self_destruct_runtime.slang"

[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*ADB_INPUT_WORDS,output=id.x*ADB_OUTPUT_WORDS;
    WORLD_TEAM_INPUT(input,output)
    for(uint i=786432U;i<ADB_OUTPUT_WORDS;i++)results[output+i]=0;
    for(uint i=PRODUCT_ADD_PREFIX;i<ADB_BASE;i++)if(commands[input+i]!=0){results[output]=64;return;}
    initializeRuntime(runtimeStates[id.x]);bool ready;
    initializePortableProgram(runtimeStates[id.x],input,output,ready);if(!ready)return;
#ifdef PORTABLE_DESTRUCTIBLE_BATTLE
    if(!initializeDestructibleBattle(runtimeStates[id.x])||!validBattleModifierAxes(runtimeStates[id.x])||!validShieldBattleRoutes(runtimeStates[id.x])){results[output]=64;return;}
#elif defined(PORTABLE_PRODUCT_ADD_GROUP_TARGET)
    if(!validProductGroupTargetAxes(runtimeStates[id.x])){results[output]=64;return;}
#endif
    if(!initializeAddAttackBattle(runtimeStates[id.x])){results[output]=64;return;}
    uint queries;executePortableCommands(runtimeStates[id.x],input,output,queries);
    writePortableProgram(runtimeStates[id.x],input,output,queries);
}
