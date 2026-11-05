[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*WGT_INPUT,output=id.x*WGT_OUTPUT;
    WORLD_TEAM_INPUT(input,output)
    for(uint i=786432U;i<WGT_OUTPUT;i++)results[output+i]=0;
    for(uint i=104400U;i<WGT_BASE;i++)if(commands[input+i]!=0){results[output]=64;return;}
    initializeRuntime(runtimeStates[id.x]);bool ready;
    initializePortableProgram(runtimeStates[id.x],input,output,ready);if(!ready)return;
    if(!initializeWeightedIncoming(runtimeStates[id.x])){results[output]=64;return;}
    uint queries;executePortableCommands(runtimeStates[id.x],input,output,queries);
    writePortableProgram(runtimeStates[id.x],input,output,queries);
}
