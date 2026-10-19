// Component proof: real queue writers/readers and the production frame drain.
#include "event_runtime.slang"
[shader("compute")]
[numthreads(1,1,1)]
void stackNoticeProbe(uint3 thread : SV_DispatchThreadID)
{
    uint id=thread.x;if(id>=commands[0]) return;
    uint input=1+id*P_INPUT_WORDS,output=id*P_OUTPUT_WORDS;
    Runtime s;initializeRuntime(s);s.inputBase=input;s.resourceOutput=output;s.count=commands[input+1];s.carrierCount=s.count;s.generation=1;
    for(uint row=0;row<s.count;row++) s.carrierDefinition[row]=row;
    for(uint who=0;who<5;who++)
    { s.baseAttack[who]=f64FromI64(1000);s.baseHP[who]=s.hp[who]=s.baseCoverHP[who]=s.coverHP[who]=s.coverMaxHP[who]=f64FromI64(1000000);s.hpPct[who]=HUNDRED; }
    admitDefinitions(s,input);
    if(s.error!=0 || !initializeResources(s) || !validateReferences(s)) { results[output]=64;return; }
    uint mode=commands[input+P_COMMAND_BASE+5];
    if(mode<=1)
    {
        for(uint i=0;i<P_REMOVALS;i++) queueStackNotice(s,i%5,i%256,i*524287);
        if(mode==1) queueStackNotice(s,0,0,1);
    }
    else if(mode==2) queueStackNotice(s,5,0,1);
    else if(mode==3) queueStackNotice(s,0,255,0x80000000);
    else if(mode==4) queueStackNotice(s,0,0xffffffff,1);
    else if(mode==5)
    {
        for(uint i=0;i<P_REMOVALS;i++)
            if((i&1)==0) queueRemovalNotice(s,i%5,i%256);else queueStackNotice(s,i%5,i%256,0x7fffffff-i);
    }
    else if(mode==6)
    {
        uint topic=definition_eventName(input,0);
        queueStackNotice(s,0,topic,2);queueStackNotice(s,0,topic,3);queueRemovalNotice(s,0,topic);
        dispatch(s,9,0,0,0,0,output);
        results[output]=s.error;results[output+1]=s.removalCount;results[output+2]=s.alive[0];
        results[output+3]=s.stacks[2];results[output+4]=s.stacks[3];results[output+5]=s.stacks[4];
        storeNumber(output+6,readStat(s,0,S_atk_pct,0));
        return;
    }
    else if(mode==7)
    {
        queueStackNotice(s,4,255,0x7fffffff);s.removalCount=0;
        queueRemovalNotice(s,0,0);
    }
    else
    {
        uint topic=definition_eventName(input,0);queueStackNotice(s,4,topic,0x7fffffff);
        dispatch(s,9,0,0,0,0,output);
        results[output]=s.error;results[output+1]=s.removalCount;results[output+2]=s.alive[0];
        results[output+3]=s.stacks[0];results[output+4]=s.activeRecipients[0];
        storeNumber(output+6,readStat(s,4,S_atk_pct,0));return;
    }
    uint metadata=0,values=0;
    for(uint i=0;i<s.removalCount;i++) { metadata+=loadRemovalNotice(s,i);values+=loadStackNoticeValue(s,i); }
    results[output]=s.error;results[output+1]=s.removalCount;results[output+2]=metadata;results[output+3]=values;
}
