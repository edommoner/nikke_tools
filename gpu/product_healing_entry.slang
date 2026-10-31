// No second clock or effect executor: only the literal bank's admission and
// initial source boundary supplement the existing three program phases.
#ifndef PORTABLE_PRODUCT_EXTERNAL_EXECUTOR
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*EHL_INPUT_WORDS,output=id.x*EHL_OUTPUT_WORDS;
    WORLD_TEAM_INPUT(input,output)
    for(uint i=786432U;i<EHL_OUTPUT_WORDS;i++)results[output+i]=0;
    for(uint i=104400U;i<EHL_BASE;i++)if(commands[input+i]!=0){results[output]=64;return;}
    initializeRuntime(runtimeStates[id.x]);bool ready;
    initializePortableProgram(runtimeStates[id.x],input,output,ready);if(!ready)return;
    if(!initializeEnemyHealing(runtimeStates[id.x])){results[output]=64;return;}
    enemyHealingFrame(runtimeStates[id.x],0);
    if(runtimeStates[id.x].error!=0){results[output]=runtimeStates[id.x].error;return;}
    uint queries;executePortableCommands(runtimeStates[id.x],input,output,queries);
    writePortableProgram(runtimeStates[id.x],input,output,queries);
}
#endif
