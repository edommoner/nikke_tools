// Opt-in consumer of the existing scheduler, enemy carriers and ADD health.
// Only source-open deduplication and receipts live in this bank, never HP/time.
uint ehlInput(inout Runtime s) { return s.inputBase+EHL_BASE; }
uint ehlOutput(inout Runtime s) { return s.resourceOutput+EHL_OUTPUT_BASE; }
bool initializeEnemyHealing(inout Runtime s)
{
    uint input=ehlInput(s),count=commands[input+2],nodes=commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE+1];
    if(commands[input]!=EHL_MAGIC||commands[input+1]!=EHL_VERSION||count==0||count>EHL_ROWS||commands[input+3]!=nodes||commands[input+4]!=actorPoolCount(s))return false;
    for(uint i=5;i<EHL_HEADER;i++)if(commands[input+i]!=0)return false;
    uint seen=0;
    for(uint index=0;index<EHL_ROWS;index++)
    {
        uint row=input+EHL_ROW_BASE+index*EHL_ROW_WORDS;
        if(index>=count){for(uint i=0;i<EHL_ROW_WORDS;i++)if(commands[row+i]!=0)return false;continue;}
        uint node=commands[row],n=commands[row+1];uint64_t amount=loadNumber(row+2);
        if(node>=nodes||n==0||n>EHL_TARGETS||!f64Finite(amount)||f64Less(amount,0)||(seen&(1U<<node))!=0)return false;
        seen|=1U<<node;
        uint graph=s.inputBase+P_WORLD_FRAME_INPUT_BASE+16+node*64,source=s.inputBase+P_WORLD_ACTOR_NODE_BASE+node*4;
        // An idle source has neither target pools nor authored attack packets.
        if(commands[source]!=0||commands[source+1]!=0||commands[graph+6]!=0)return false;
        ActorBits targets=actorBitsEmpty();
        for(uint i=0;i<EHL_TARGETS;i++)
        {
            uint slot=commands[row+EHL_TARGET_BASE+i];
            if(i>=n){if(slot!=0)return false;continue;}
            if(slot==0||slot>=actorPoolCount(s)||actorBitsHas(targets,slot))return false;
            actorBitsAdd(targets,slot);uint b=actorBinding(s,slot),d=actorPoolDef(s,slot);
            if(commands[b]!=5||commands[b+2]!=2||commands[d]!=2||commands[d+1]!=0||!f64Zero(loadNumber(d+4))||!f64Finite(loadNumber(d+2))||!f64Less(0,loadNumber(d+2)))return false;
        }
        for(uint i=EHL_TARGET_BASE+EHL_TARGETS;i<EHL_ROW_WORDS;i++)if(commands[row+i]!=0)return false;
    }
    uint head=ehlOutput(s);results[head]=EHL_MAGIC;return true;
}
uint64_t enemyHealingMultiplier(inout Runtime s,uint slot,uint64_t when)
{
    uint64_t total=0;uint target=ACTOR_REF|slot;
    // Same live carrier order and scalar stack/reference consumer as enemy
    // modifiers. No target selection, expiry engine or stack formula here.
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass];Definition d=residentDefinition(s,row);
        if(d.kind!=0||d.enemyBuff==0||d.stat!=S_heal_received_pct||s.alive[row]==0||!f64Less(when,s.end[row])||!actorFieldMember(s,row,target)||!actorFieldConditions(s,row,target,when))continue;
        total=f64Add(total,scalarValue(s,row,d.owner));
        if(!f64Finite(total)){s.error=16;return 0;}
    }
    return larger(0,f64Add(ONE,f64Div(total,HUNDRED)));
}
void enemyHealingFrame(inout Runtime s,uint64_t when)
{
    uint input=ehlInput(s),head=ehlOutput(s);
    if(results[head]!=EHL_MAGIC){s.error=64;return;}
    for(uint index=0;index<commands[input+2]&&s.error==0;index++)
    {
        uint row=input+EHL_ROW_BASE+index*EHL_ROW_WORDS,node=commands[row],g=s.resourceOutput+P_WORLD_FRAME_OUTPUT_BASE+16+node*24;
        uint gen=results[g+1],previous=results[head+EHL_SEEN_BASE+node];
        if(gen==previous)continue;
        if(results[g]==0||gen!=previous+1){s.error=64;return;}
        results[head+EHL_SEEN_BASE+node]=gen;results[head+2]++;
        for(uint i=0;i<commands[row+1]&&s.error==0;i++)
        {
            uint count=results[head+1];if(count>=EHL_RECEIPTS){s.error=2;return;}
            uint out=head+EHL_RECEIPT_BASE+count*EHL_RECEIPT_WORDS,slot=commands[row+EHL_TARGET_BASE+i],p=actorPoolAt(s,slot);
            results[head+1]=count+1;results[out]=node;results[out+1]=gen;results[out+2]=slot;results[out+3]=results[p];
            storeNumber(out+6,when);uint64_t amount=loadNumber(row+2);storeNumber(out+8,amount);
            if(results[p]==0){results[out+4]=1;continue;}
            if(results[p+1]==0){results[out+4]=2;continue;}
            uint64_t before=actorNumber(p+4),multiplier=enemyHealingMultiplier(s,slot,when),requested=f64Mul(amount,multiplier);
            if(s.error!=0)return;
            if(!f64Finite(requested)){s.error=16;return;}
            uint64_t applied=smaller(requested,before),after=f64Add(before,applied^F64_SIGN);
            results[out+4]=3;storeNumber(out+10,multiplier);storeNumber(out+12,requested);storeNumber(out+14,before);
            storeNumber(out+16,after);storeNumber(out+18,applied);storeNumber(out+20,f64Add(before,after^F64_SIGN));
            storeNumber(out+22,loadNumber(actorPoolDef(s,slot)+2));results[out+24]=results[p+3];
            storeNumber(p+4,after);results[out+25]=results[p+3];
            // addScoredDamage, addOverkill, hits and lifecycle are untouched.
        }
    }
}
