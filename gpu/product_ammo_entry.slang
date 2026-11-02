#ifndef PORTABLE_PRODUCT_EXTERNAL_EXECUTOR
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*EAM_INPUT_WORDS,outputWords=PRODUCT_AMMO_OUTPUT_WORDS(1U),output=id.x*outputWords;
    WORLD_TEAM_INPUT(input,output)
    for(uint i=786432U;i<outputWords;i++)results[output+i]=0;
    if(PRODUCT_AMMO_OUTPUT_WORDS(input)!=outputWords||!validProductAmmoPadding(input)){results[output]=64;return;}
    initializeRuntime(runtimeStates[id.x]);bool ready;
    initializePortableProgram(runtimeStates[id.x],input,output,ready);if(!ready)return;
    if(!initializeProductAmmoPrefix(runtimeStates[id.x])||!initializeAddAttackBattle(runtimeStates[id.x])||!initializeEnemyAmmo(runtimeStates[id.x])||!initializeProductAmmoHealing(runtimeStates[id.x])){results[output]=64;return;}
    uint queries;executePortableCommands(runtimeStates[id.x],input,output,queries);
    writePortableProgram(runtimeStates[id.x],input,output,queries);
}
#endif
