// GPU-owned overlay snapshots and boss-bound enemy contributions.
// Uses the same binary64,carrier entry clock and damage collector as all backends.
static const uint WO_IN=P_WORLD_OVERLAY_INPUT_BASE, WO_NODES=P_WORLD_OVERLAY_NODE_BASE, WO_OUT=P_WORLD_OVERLAY_STATE_BASE;
bool worldOverlayEnabled(inout Runtime s) { return commands[s.inputBase+WO_IN]!=0; }
uint woState(inout Runtime s,uint node) { return s.resourceOutput+WO_OUT+32+node*8; }
uint woNode(inout Runtime s,uint node) { return s.inputBase+WO_NODES+node*16; }
uint woGraphState(inout Runtime s,uint node) { return s.resourceOutput+P_WORLD_FRAME_OUTPUT_BASE+16+node*24; }
uint64_t woRead(uint at) { return uint64_t(results[at])|uint64_t(results[at+1])<<32; }
uint64_t woCore(inout Runtime s) { return woRead(s.resourceOutput+WO_OUT+4); }
uint64_t woDistance(inout Runtime s) { return woRead(s.resourceOutput+WO_OUT+6); }
uint woRangeFlags(inout Runtime s) { return results[s.resourceOutput+WO_OUT+2]; }
uint woRangeMask(inout Runtime s) { return results[s.resourceOutput+WO_OUT+3]; }
[noinline]
bool initializeWorldOverlays(inout Runtime s)
{
    for(uint i=0;i<288;i++) results[s.resourceOutput+WO_OUT+i]=0;
    uint at=s.inputBase+WO_IN;
    if(commands[at]==0) { for(uint i=0;i<528;i++) if(commands[at+i]!=0) return false;return true; }
    if(commands[at]!=0x574f3031 || commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE]!=0x57533031 || s.targetCount!=1 || commands[s.inputBase+P_GEOMETRY_BASE]==0) return false;
    for(uint i=1;i<16;i++) if(commands[at+i]!=0) return false;
    uint count=commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE+1];
    for(uint n=0;n<32;n++)
    {
        uint p=woNode(s,n),kind=commands[p],flags=commands[p+1];
        if(n>=count || kind==0) { for(uint i=0;i<16;i++) if(commands[p+i]!=0) return false;continue; }
        // Shield/vanish and actor payloads are not silently accepted before
        // their landing/gauge providers have been connected.
        if(kind>4 || flags>1 || kind!=1 && flags!=0) return false;
        for(uint i=11;i<16;i++) if(commands[p+i]!=0) return false;
        for(uint i=2;i<10;i+=2) if(!f64Finite(loadNumber(p+i))) return false;
        if(kind==1)
        { if(f64Less(loadNumber(p+2),0) || !f64Zero(loadNumber(p+8)) || commands[p+10]!=0) return false; }
        else
        {
            for(uint i=2;i<8;i++) if(commands[p+i]!=0) return false;
            if(kind==2 || kind==3)
            { if(!f64Less(0,loadNumber(p+8)) || commands[p+10]!=0) return false; }
            if(kind==2)
            {
                uint status;uint64_t whole=f64ToI64(loadNumber(p+8),0,status);
                if(status!=0 || !f64Equal(loadNumber(p+8),f64FromI64(whole)) || f64Less(f64FromI64(100000000),loadNumber(p+8))) return false;
            }
            if(kind==4 && (!f64Zero(loadNumber(p+8)) || commands[p+10]>63)) return false;
        }
        if(kind==3 && ((commands[s.inputBase+P_GEOMETRY_BASE]&2)==0) || kind==4 && (commands[s.inputBase+P_GEOMETRY_BASE]&2)!=0) return false;
    }
    return true;
}
// Merge boss effects in the actual global insertion order, including character
// effects between openings. Summing boss effects in a separate bucket is wrong
// for cancellation and binary64 rounding. No synthetic character owner exists.
[noinline]
void worldEnemyUntil(inout Runtime s,uint cutoff,inout uint visited,inout uint64_t value)
{
    if(!worldOverlayEnabled(s)) return;
    uint count=commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE+1];
    for(uint pass=0;pass<count;pass++)
    {
        uint selected=32,sequence=cutoff;
        for(uint n=0;n<count;n++)
        { uint order=results[woState(s,n)+3];if((visited&(1U<<n))==0 && order!=0 && order<sequence) { selected=n;sequence=order; } }
        if(selected==32) break;
        visited|=1U<<selected;value=f64Add(value,loadNumber(woNode(s,selected)+6));
        if(!f64Finite(value)) { s.error=16;return; }
    }
}
[noinline]
void applyWorldOverlays(inout Runtime s,uint64_t when)
{
    if(!worldOverlayEnabled(s)) return;
    uint count=commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE+1],out=s.resourceOutput+WO_OUT;
    for(uint n=0;n<count;n++)
    {
        uint state=woState(s,n),graph=woGraphState(s,n),node=woNode(s,n),generation=results[graph+1];
        if(results[state]!=generation)
        {
            results[state]=generation;results[state+1]=0;results[state+2]=0;
            results[state+3]=0;storeNumber(state+4,0);
            if(results[graph]!=0 && commands[node]==1 && !f64Zero(loadNumber(node+6)))
            { if(s.entryClock==0x7fffffff) { s.error=2;return; } results[state+3]=++s.entryClock; }
        }
        if(results[graph]==0 || results[state+1]!=0) results[state+3]=0;
        results[state+2]=results[state+1];
    }
    uint geometry=s.inputBase+P_GEOMETRY_BASE;
    uint64_t defense=loadNumber(s.inputBase+P_TARGET_BASE+6),core=loadNumber(geometry+2),distance=loadNumber(geometry+4);
    uint flags=commands[geometry],mask=commands[geometry+1],visited=0;
    for(uint pass=0;pass<count;pass++)
    {
        uint selected=32;uint64_t earliest=0;
        for(uint n=0;n<count;n++)
        {
            if((visited&(1U<<n))!=0 || results[woGraphState(s,n)]==0) continue;
            uint64_t start=woRead(woGraphState(s,n)+2);
            if(selected==32 || f64Less(start,earliest)) { selected=n;earliest=start; }
        }
        if(selected==32) break;visited|=1U<<selected;
        uint node=woNode(s,selected),kind=commands[node];
        if(kind==1 && results[woState(s,selected)+2]==0) defense=f64Add(f64Mul(defense,loadNumber(node+2)),loadNumber(node+4));
        else if(kind==2) core=larger(core,loadNumber(node+8));
        else if(kind==3) { distance=loadNumber(node+8);flags|=2; }
        else if(kind==4) mask=commands[node+10];
    }
    if(!f64Finite(defense)) { s.error=16;return; }
    s.targetDefense[0]=defense;
    for(uint who=0;who<5;who++) s.coreDiameter[who]=core;
    results[out+2]=flags;results[out+3]=mask;storeNumber(out+4,core);storeNumber(out+6,distance);storeNumber(out+8,defense);
    results[out+10]++;
}
