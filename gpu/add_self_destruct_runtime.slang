uint asdHead(inout Runtime s){return s.resourceOutput+ASD_OUTPUT_BASE;}
bool validAddSelfDestructRow(inout Runtime s,uint row)
{
    uint64_t delay=loadNumber(row+5);
    return commands[row+4]<=1&&commands[row+7]==0&&f64Finite(delay)&&!f64Less(delay,0)&&
           (commands[row+4]==0||commands[row+1]!=0);
}
bool initializeAddSelfDestruct(inout Runtime s)
{
    for(uint i=0;i<ASD_HEADER+ASD_ROWS*ASD_ROW_WORDS;i++)results[asdHead(s)+i]=0;
    results[asdHead(s)]=ASD_MAGIC;return true;
}
void retireAddAfterFinalShot(inout Runtime s,uint node,uint slot,uint cursor,uint64_t when)
{
    uint row=adbRow(s,node),p=actorPoolAt(s,slot);
    if(commands[row+4]==0||results[p+1]==0||results[cursor+1]!=commands[row+1])return;
    uint head=asdHead(s),index=results[head+1];if(index>=ASD_ROWS){s.error=2;return;}
    uint record=results[s.resourceOutput+WF_OUTPUT+2];
    WorldSchedule w=frameSchedule(s);wsLog(w,5,node,slot,when);s.error=w.error;if(s.error!=0)return;
    uint at=head+ASD_HEADER+index*ASD_ROW_WORDS;results[head+1]=index+1;
    results[at]=node;results[at+1]=slot;results[at+2]=results[p];results[at+3]=results[cursor+1];
    storeNumber(at+4,when);results[at+6]=record;
    uint pool=actorPoolHead(s);if(results[pool+14]==0x7fffffff){s.error=2;return;}
    results[p+1]=0;results[p+2]=3;results[pool+14]++;WORLD_STATE_GONE(s,slot)
    s.enemySnapshot=actorPoolsEnemyCount(s);
}
void deliverAddSelfDestructNotices(inout Runtime s,uint64_t when,uint output)
{
    uint head=asdHead(s),end=results[head+1],cursor=results[head+2];
    while(cursor<end&&s.error==0)
    {
        uint at=head+ASD_HEADER+cursor*ASD_ROW_WORDS;
        // Native adds these events after all graph opening/closing events.
        // They are not deferred HP-kill notices in the actor-pool queue.
        worldFrameNotice(s,4,when,output);
        if(s.error!=0)return;
        results[at+7]=1;results[head+2]=++cursor;
    }
}
