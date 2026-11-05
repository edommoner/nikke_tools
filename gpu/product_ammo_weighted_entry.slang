[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*WGT_INPUT,outputWords=PRODUCT_AMMO_OUTPUT_WORDS(input),output=id.x*outputWords;
    WORLD_TEAM_INPUT(input,output)
    for(uint i=786432U;i<outputWords;i++)results[output+i]=0;
    if(commands[input+EAM_BASE+1]!=3||!validProductAmmoPadding(input)){results[output]=64;return;}
    initializeRuntime(runtimeStates[id.x]);bool ready;
    initializePortableProgram(runtimeStates[id.x],input,output,ready);if(!ready)return;
    if(!initializeProductAmmoPrefix(runtimeStates[id.x])||!initializeAddAttackBattle(runtimeStates[id.x])||!initializeEnemyAmmo(runtimeStates[id.x])||!initializeProductAmmoHealing(runtimeStates[id.x])||!initializeWeightedIncoming(runtimeStates[id.x])){results[output]=64;return;}
    uint queries;executePortableCommands(runtimeStates[id.x],input,output,queries);
    writePortableProgram(runtimeStates[id.x],input,output,queries);
}
