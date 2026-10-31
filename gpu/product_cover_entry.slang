[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*CDF_INPUT_WORDS,output=id.x*CDF_OUTPUT_WORDS;
    WORLD_TEAM_INPUT(input,output)
    for(uint i=786432U;i<CDF_OUTPUT_WORDS;i++)results[output+i]=0;
#ifdef PORTABLE_PRODUCT_COVER_GROUP
    for(uint i=104408U;i<CDF_BASE;i++)if(commands[input+i]!=0){results[output]=64;return;}
#else
    for(uint i=104400U;i<CDF_BASE;i++)if(commands[input+i]!=0){results[output]=64;return;}
#endif
    initializeRuntime(runtimeStates[id.x]);bool ready;
    initializePortableProgram(runtimeStates[id.x],input,output,ready);if(!ready)return;
    initializeManualControls(runtimeStates[id.x]);if(runtimeStates[id.x].error!=0){results[output]=64;return;}
    if(!initializeCoverDefense(runtimeStates[id.x])){results[output]=64;return;}
    uint queries;executePortableCommands(runtimeStates[id.x],input,output,queries);
    writePortableProgram(runtimeStates[id.x],input,output,queries);
    // Same completed-frame cleanup as the existing cover battle entry.
    for(uint i=0;i<CDF_DEPTH*CDF_SNAPSHOT_WORDS;i++)results[output+CDF_OUTPUT_BASE+CDF_SNAPSHOT_BASE+i]=0;
}
