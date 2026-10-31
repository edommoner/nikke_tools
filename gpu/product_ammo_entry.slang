[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*EAM_INPUT_WORDS,output=id.x*EAM_OUTPUT_WORDS;
    WORLD_TEAM_INPUT(input,output)
    for(uint i=786432U;i<EAM_OUTPUT_WORDS;i++)results[output+i]=0;
    for(uint i=104400U;i<ADB_BASE;i++)if(commands[input+i]!=0){results[output]=64;return;}
    initializeRuntime(runtimeStates[id.x]);bool ready;
    initializePortableProgram(runtimeStates[id.x],input,output,ready);if(!ready)return;
    if(!initializeAddAttackBattle(runtimeStates[id.x])||!initializeEnemyAmmo(runtimeStates[id.x])){results[output]=64;return;}
    uint queries;executePortableCommands(runtimeStates[id.x],input,output,queries);
    writePortableProgram(runtimeStates[id.x],input,output,queries);
}
