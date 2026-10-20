// Canonical persistent recipient sets:one stack and lifetime per resident.
// Binding slots are static input identities;generations are captured on GPU.
bool actorRecipientsEnabled(inout Runtime s)
{ return actorFieldsEnabled(s)&&commands[s.inputBase+P_WORLD_ACTOR_POOL_INPUT_BASE+4]==0x57523031; }
uint actorRecipientAt(inout Runtime s,uint row)
{ return s.resourceOutput+P_WORLD_ACTOR_RECIPIENT_BASE+16+row*P_WORLD_ACTOR_RECIPIENT_WORDS; }
bool actorRecipientHas(inout Runtime s,uint row,uint slot)
{ return slot<128&&(results[actorRecipientAt(s,row)+2+slot/32]&(1U<<(slot%32)))!=0; }
bool actorRecipientAny(inout Runtime s,uint row)
{ uint at=actorRecipientAt(s,row);return (results[at+2]|results[at+3]|results[at+4]|results[at+5])!=0; }
void resetActorRecipients(inout Runtime s,uint row)
{ if(actorRecipientsEnabled(s)) { uint at=actorRecipientAt(s,row);for(uint i=0;i<P_WORLD_ACTOR_RECIPIENT_WORDS;i++) results[at+i]=0; } }
void actorRecipientAppend(inout Runtime s,uint row,uint slot,uint generation)
{
    uint at=actorRecipientAt(s,row),count=results[at+1];
    if(slot>=actorPoolCount(s)||generation==0||count>=128||actorRecipientHas(s,row,slot)) { s.error=64;return; }
    results[at+2+slot/32]|=1U<<(slot%32);results[at+8+slot]=generation;
    uint order=at+136+count/4;results[order]|=slot<<((count%4)*8);results[at+1]=count+1;
}
void bindActorRecipient(inout Runtime s,uint row,uint target,uint generation)
{
    if(!actorRecipientsEnabled(s)) return;
    resetActorRecipients(s,row);uint at=actorRecipientAt(s,row);results[at]=1;actorRecipientAppend(s,row,target&127U,generation);
}
bool actorRecipientMember(inout Runtime s,uint row,uint target)
{
    uint slot=actorFieldLogicalSlot(s,target),at=actorRecipientAt(s,row);if(slot>=actorPoolCount(s)) return false;
    return actorRecipientHas(s,row,slot)&&results[at+8+slot]==results[actorPoolAt(s,slot)];
}
bool actorRecipientSame(inout Runtime s,uint row,uint generation)
{
    uint at=actorRecipientAt(s,row),slot=s.target&127U;
    return results[at+1]==1&&actorRecipientHas(s,row,slot)&&results[at+8+slot]==generation;
}
void initializeActorRecipients(inout Runtime s)
{
    for(uint i=P_WORLD_ACTOR_RECIPIENT_BASE;i<P_OUTPUT_WORDS;i++) results[s.resourceOutput+i]=0;
    if(actorRecipientsEnabled(s)) results[s.resourceOutput+P_WORLD_ACTOR_RECIPIENT_BASE]=0x57523031;
}
void actorRecipientsDropGone(inout Runtime s)
{
    uint head=actorFieldHead(s);ActorBits gone;for(uint i=0;i<4;i++) { gone.words[i]=results[head+8+i];results[head+8+i]=0; }
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass],at=actorRecipientAt(s,row);if(results[at]==0) continue;
        for(uint i=0;i<4;i++) results[at+2+i]&=~gone.words[i];
        if(!actorRecipientAny(s,row)) s.activeRecipients[row]&=~32U;
    }
}
bool actorRecipientsStrip(inout Runtime s,uint row,ActorBits scope)
{
    uint at=actorRecipientAt(s,row);if(results[at]==0) return false;bool changed=false;
    for(uint slot=0;slot<actorPoolCount(s);slot++)
        if(actorBitsHas(scope,slot)&&actorRecipientMember(s,row,slot==0?0:ACTOR_REF|slot))
        { results[at+2+slot/32]&=~(1U<<(slot%32));changed=true; }
    return changed&&!actorRecipientAny(s,row);
}
[noinline]
void captureActorRecipients(inout Runtime s,uint row,Definition d,uint target)
{
    uint index=0;while(index<P_WORLD_ACTOR_SETS&&results[actorPoolSet(s,index)+5]!=0) index++;
    if(index==P_WORLD_ACTOR_SETS) { s.error=64;return; }
    // Native initialization uses nearest ordering for a current-target selector.
    uint route=d.damageRoute==0?6:d.damageRoute;actorSetCapture(s,33,index,route,d.damageCount,target,d.owner);if(s.error!=0) return;
    resetActorRecipients(s,row);uint at=actorRecipientAt(s,row),set=actorPoolSet(s,index);results[at]=2;
    for(uint i=0;i<results[set]&&s.error==0;i++) actorRecipientAppend(s,row,results[set+8+i*4],results[set+9+i*4]);
    results[set+5]=0;results[actorPoolHead(s)+7]--;
    uint key=actorFieldKey(s,row);results[key]=0x80000000U|row;results[key+1]=0;s.activeRecipients[row]=actorRecipientAny(s,row)?32U:0U;
    // Shared binding semantics are represented above,not in the legacy8 arrays.
    s.bulletInitialized[row]=2;s.enemyCaptureGeneration[row]=0;
}
