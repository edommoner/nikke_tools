// Named removal snapshots scope once and retires all matches before callbacks.
bool actorMutationEnabled(inout Runtime s)
{ return actorFieldsEnabled(s)&&commands[s.inputBase+P_WORLD_ACTOR_POOL_INPUT_BASE+4]==0x574D3031; }
[noinline]
void actorMutationRemoveNamed(inout Runtime s,uint row,uint target,uint64_t when)
{
    Definition d=readDefinition(s.inputBase,row);uint scope=0xffffffff,index=P_WORLD_ACTOR_SETS;ActorBits enemies=actorBitsEmpty();
    if(d.target==1) { uint64_t order;scope=selectRecipients(s,row,when,order); }
    else if(d.target==2)
    {
        index=0;while(index<P_WORLD_ACTOR_SETS&&results[actorPoolSet(s,index)+5]!=0) index++;
        if(index==P_WORLD_ACTOR_SETS) { s.error=64;return; }
        actorSetCapture(s,33,index,d.damageRoute,d.damageCount,target,d.owner);if(s.error!=0) return;
        for(uint i=0;i<4;i++) enemies.words[i]=results[actorPoolSet(s,index)+1+i];
    }
    for(uint pass=0;pass<s.orderedCount&&s.error==0;pass++)
    {
        uint slot=s.orderedRows[pass],definition=s.carrierDefinition[slot];
        if(s.alive[slot]==0||definition_name(s.inputBase,definition)!=uint(d.targetName)) continue;
        uint bound=results[actorFieldKey(s,slot)];
        if(d.target==2)
        {
            // Scope matches labels in native target_chars, even before a gone
            // binding is physically dropped. Generation filtering is a query rule.
            if(bound==0||(s.activeRecipients[slot]&32)==0||!actorBitsHas(enemies,bound-1)) continue;
            s.activeRecipients[slot]&=~32U;
        }
        else if(d.target==1)
        {
            if(bound!=0) continue;
            uint prior=removalMembers(s,slot),stripped=prior&scope;if(stripped==0) continue;
            uint remaining=prior&~stripped;s.activeRecipients[slot]=remaining;
            storeCarrierOrder(s,slot,filterRemovalOrder(carrierOrder(s,slot),remaining&31,3,21));
            if(remaining!=0) continue;
        }
        queueCarrierEnd(s,slot,1);
    }
    if(index<P_WORLD_ACTOR_SETS) { results[actorPoolSet(s,index)+5]=0;results[actorPoolHead(s)+7]--; }
}
