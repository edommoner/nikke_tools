// Typed configured identities;birth generation and presence come from the
// existing shared world scheduler. This registry does not decide enemy counts.
bool worldActorsEnabled(inout Runtime s) { return commands[s.inputBase+P_WORLD_ACTOR_INPUT_BASE]!=0; }
uint actorBinding(inout Runtime s,uint slot) { return s.inputBase+P_WORLD_ACTOR_BINDING_BASE+slot*8; }
uint actorState(inout Runtime s,uint slot) { return s.resourceOutput+P_WORLD_ACTOR_STATE_BASE+8+slot*8; }
[noinline]
bool initializeWorldActors(inout Runtime s)
{
    uint base=s.inputBase+P_WORLD_ACTOR_INPUT_BASE;
    for(uint i=0;i<P_WORLD_ACTOR_STATE_WORDS;i++) results[s.resourceOutput+P_WORLD_ACTOR_STATE_BASE+i]=0;
    if(commands[base]==0)
    { for(uint i=0;i<P_WORLD_ACTOR_INPUT_WORDS-P_WORLD_ACTOR_INPUT_BASE;i++) if(commands[base+i]!=0) return false;return true; }
    uint count=commands[base+1],nodes=commands[base+2];
    if(commands[base]!=0x57413031 || count==0 || count>P_WORLD_ACTORS || !worldFrameEnabled(s) || nodes!=commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE+1]) return false;
    for(uint i=3;i<8;i++) if(commands[base+i]!=0) return false;
    uint seen[32];for(uint n=0;n<32;n++) seen[n]=0;
    for(uint n=0;n<32;n++)
    {
        uint d=s.inputBase+P_WORLD_ACTOR_NODE_BASE+n*4,k=commands[d],c=commands[d+1];
        if(k>3 || c>=P_WORLD_ACTORS || (k==0)!=(c==0) || commands[d+2]!=0 || commands[d+3]!=0 || n>=nodes && k!=0) return false;
#ifndef PORTABLE_WORLD_ACTOR_POOLS
        if(k==3) return false;
#endif
    }
    uint parts=0,adds=0,interrupts=0,previousKind=0,previousNode=0;
    for(uint slot=0;slot<P_WORLD_ACTORS;slot++)
    {
        uint b=actorBinding(s,slot),kind=commands[b],id=commands[b+1],source=commands[b+2],node=commands[b+3],index=commands[b+4];
        if(slot>=count) { for(uint i=0;i<8;i++) if(commands[b+i]!=0) return false;continue; }
        if(commands[b+7]!=0) return false;
        if(slot==0)
        { if(kind!=0 || id!=0 || source!=0 || node!=0xffffffffU || index!=0 || commands[b+5]!=0xffffffffU || commands[b+6]!=0xffffffffU) return false;continue; }
        if(kind!=1 && kind!=5 && kind!=6 || kind<previousKind || node>=nodes || kind==previousKind && node<previousNode) return false;
        uint d=s.inputBase+P_WORLD_ACTOR_NODE_BASE+node*4;
        if(source!=(kind==1?1U:kind==6?3U:2U) || commands[d]!=source || index!=seen[node] || index>=commands[d+1]) return false;
        if(kind==1)
        { if(id!=parts++ || commands[b+5]!=0 || commands[b+6]!=0) return false; }
        else if(id!=(kind==6?interrupts++:adds++) || commands[b+5]!=0xffffffffU || commands[b+6]!=0xffffffffU) return false;
        seen[node]++;previousKind=kind;previousNode=node;
    }
    for(uint n=0;n<32;n++) if(seen[n]!=commands[s.inputBase+P_WORLD_ACTOR_NODE_BASE+n*4+1]) return false;
    results[s.resourceOutput+P_WORLD_ACTOR_STATE_BASE]=count;worldActorsApply(s,false);return true;
}
[noinline]
void worldActorsApply(inout Runtime s,bool pools=true)
{
    if(!worldActorsEnabled(s)) return;
    uint count=commands[s.inputBase+P_WORLD_ACTOR_INPUT_BASE+1];
    for(uint slot=0;slot<count;slot++)
    {
        uint b=actorBinding(s,slot),o=actorState(s,slot),kind=commands[b];
        results[o]=kind;results[o+1]=commands[b+1];
        if(slot==0) { results[o+2]=1;results[o+3]=1; }
        else { uint graph=s.resourceOutput+P_WORLD_FRAME_OUTPUT_BASE+16+commands[b+3]*24;results[o+2]=results[graph+1];results[o+3]=results[graph]; }
#ifdef PORTABLE_WORLD_ACTOR_POOLS
        if(pools && actorPoolsEnabled(s)) { uint p=actorPoolAt(s,slot);results[o+2]=results[p];results[o+3]=results[p+1]; }
#endif
        results[o+4]=commands[b+5];results[o+5]=commands[b+6];results[o+6]=kind==1?1U:0U;results[o+7]=commands[b+3];
    }
}
uint worldActorResolve(inout Runtime s,uint kind,uint identity,uint generation,out uint found)
{
    uint count=commands[s.inputBase+P_WORLD_ACTOR_INPUT_BASE+1];found=P_WORLD_ACTORS;
    for(uint slot=0;slot<count;slot++) { uint b=actorBinding(s,slot);if(commands[b]==kind && commands[b+1]==identity) { found=slot;break; } }
    if(found==P_WORLD_ACTORS) return 1;
    uint state=actorState(s,found);if(results[state+2]==0) return 2;if(results[state+2]!=generation) return 3;return 0;
}
[noinline]
void worldActorQuery(inout Runtime s,uint kind,uint identity,uint generation,uint root,uint query)
{
    uint out=s.resourceOutput+P_WORLD_ACTOR_QUERY_BASE+query*8,found,status=worldActorResolve(s,kind,identity,generation,found);
    for(uint i=0;i<8;i++) results[out+i]=0;results[out]=status;if(status!=0) return;
    uint state=actorState(s,found);if(root!=0 && kind==1) state=actorState(s,0);
    for(uint i=0;i<7;i++) results[out+1+i]=results[state+i];
}
