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
    for(uint i=0;i<328;i++) results[s.resourceOutput+WO_OUT+i]=0;
    uint at=s.inputBase+WO_IN;
    if(commands[at]==0) { for(uint i=0;i<528;i++) if(commands[at+i]!=0) return false;return true; }
    if(commands[at]!=0x574f3031 || commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE]!=0x57533031 || s.targetCount!=1 || commands[s.inputBase+P_LANDING_META_BASE]!=1 || commands[s.inputBase+P_GEOMETRY_BASE]==0) return false;
    if(commands[at+1]>31) return false;
    for(uint i=2;i<7;i++) if(commands[at+i]>5) return false;
    if(commands[at+7]!=0) return false;
    for(uint row=0;row<P_DEFINITIONS;row++)
    {
        uint policy=commands[s.inputBase+P_MODE_BASE+row*P_MODE_WORDS+31];
        if(policy!=0 && (policy>1 || row>=s.count || definition_kind(s.inputBase,row)!=2)) return false;
        if((commands[at+8+row/32]&(1U<<(row%32)))==0) continue;
        if(row>=s.count || definition_kind(s.inputBase,row)!=26) return false;
    }
    uint count=commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE+1];
    for(uint n=0;n<32;n++)
    {
        uint p=woNode(s,n),kind=commands[p],flags=commands[p+1];
        if(n>=count || kind==0) { for(uint i=0;i<16;i++) if(commands[p+i]!=0) return false;continue; }
        if(kind>6 || flags>1 || kind!=1 && flags!=0) return false;
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
            if(kind==5 && (commands[p+8]>commands[s.inputBase+P_WORLD_META_BASE+1] || commands[p+9]!=0 || commands[p+10]==0 || commands[p+10]>5)) return false;
            if(kind==6 && (!f64Zero(loadNumber(p+8)) || commands[p+10]!=0)) return false;
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

// Selection is from this frame's ordered active set. A blocked packet is
// charged to exactly one node;vanish has priority over every elemental shield.
uint worldGateNode(inout Runtime s,uint who,bool normal)
{
    if(!worldOverlayEnabled(s)) return 32;
    uint count=commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE+1],visited=0;
    for(uint phase=0;phase<2;phase++)
    {
        visited=0;
        for(uint pass=0;pass<count;pass++)
        {
            uint selected=32;uint64_t earliest=0;
            for(uint n=0;n<count;n++)
            {
                if((visited&(1U<<n))!=0 || results[woGraphState(s,n)]==0) continue;
                uint kind=commands[woNode(s,n)];if(phase==0 ? kind!=6 : kind!=5) continue;
                uint64_t start=woRead(woGraphState(s,n)+2);
                if(selected==32 || f64Less(start,earliest)) { selected=n;earliest=start; }
            }
            if(selected==32) break;visited|=1U<<selected;
            if(phase==0) { if(normal) return selected;continue; }
            uint p=woNode(s,selected),own=commands[s.inputBase+WO_IN+2+who],wanted=commands[p+10];
            uint superior=own==1?3U:own==2?1U:own==3?4U:own==4?5U:own==5?2U:0U;
            if(superior==wanted) continue;
            bool overrideMatch=false;uint tag=commands[p+8];
            if(tag!=0) for(uint i=0;i<s.orderedCount;i++)
            {
                uint row=s.orderedRows[i];if(s.alive[row]==0 || (s.activeRecipients[row]&(1U<<who))==0) continue;
                uint definition=s.carrierDefinition[row];
                if(definition_kind(s.inputBase,definition)==0 && definition_stat(s.inputBase,definition)==S_element_code_override && definition_damageRoute(s.inputBase,definition)==tag) { overrideMatch=true;break; }
            }
            if(!overrideMatch) return selected;
        }
    }
    return 32;
}
bool worldVanish(inout Runtime s)
{
    if(!worldOverlayEnabled(s)) return false;
    for(uint n=0;n<commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE+1];n++)
        if(results[woGraphState(s,n)]!=0 && commands[woNode(s,n)]==6) return true;
    return false;
}
bool worldOverlayLand(inout Runtime s,uint who,uint target,uint64_t amount,bool normal)
{
    if(target!=0) return true;
    uint node=worldGateNode(s,who,normal);if(node==32) return true;
    uint at=woState(s,node)+4;uint64_t blocked=f64Add(woRead(at),amount);
    if(!f64Finite(blocked)) { s.error=16;return false; }storeNumber(at,blocked);return false;
}
bool worldSkillGauge(inout Runtime s,uint who) { return worldGateNode(s,who,false)==32; }

bool worldCleanseDefinition(inout Runtime s,uint row)
{ return worldOverlayEnabled(s) && (commands[s.inputBase+WO_IN+8+row/32]&(1U<<(row%32)))!=0; }
void worldDispelLog(inout Runtime s,uint node,uint64_t when);
[noinline]
void worldDispel(inout Runtime s,uint row,uint scope,uint64_t when)
{
    // Native: int(value or 1),then max(n,0). Clamp only after preserving
    // zero's default and truncation;huge positive counts need no i64 cast.
    if((scope&32)==0) return;
    uint64_t value=definition_value(s.inputBase,row);uint limit=0;
    if(f64Zero(value)) limit=1;
    else if(f64Less(0,value))
    {
        if(!f64Less(value,f64FromI64(32))) limit=32;
        else { uint status;limit=uint(f64ToI64(value,1,status));if(status!=0) { s.error=16;return; } }
    }
    uint count=commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE+1];
    for(uint pass=0;pass<limit && s.error==0;pass++)
    {
        uint selected=32;uint64_t latest=0;
        for(uint n=0;n<count;n++)
        {
            uint node=woNode(s,n),state=woState(s,n),graph=woGraphState(s,n);
            if(results[graph]==0 || commands[node]!=1 || commands[node+1]!=0 || results[state+1]!=0) continue;
            uint64_t start=woRead(graph+2);
            if(selected==32 || f64Less(latest,start) || f64Equal(start,latest) && n>selected) { selected=n;latest=start; }
        }
        if(selected==32) break;
        uint state=woState(s,selected);if(results[state+6]==0x7fffffff) { s.error=2;return; }
        results[state+1]=1;results[state+6]++;worldDispelLog(s,selected,when);
        // Do not change the sampled defense or resident contribution here.
        // The next distinct world frame owns release/application.
    }
}

// Snapshot the physical packet category before callbacks can clear/switch modes.
bool worldPhysicalSkill(inout Runtime s,uint who)
{ return (results[s.resourceOutput+WO_OUT+288+who*8+7]&1)!=0; }
void worldSampleShotKind(inout Runtime s,uint who,int mode,uint hitCount)
{
    uint flag=mode<0 ? 0 : commands[s.inputBase+P_MODE_BASE+uint(mode)*P_MODE_WORDS+31];
    results[s.resourceOutput+WO_OUT+288+who*8+7]=flag!=0 ? 1U | (hitCount>1 ? 2U : 0U) : 0U;
}
bool worldModePolicyInvalid(inout Runtime s,uint policy)
{ return policy>1 || policy!=0 && !worldOverlayEnabled(s); }
bool worldPhysicalGauge(inout Runtime s)
{
    uint who=s.physicalGaugeOwner;
    return who>0 && who<=5 && worldPhysicalSkill(s,who-1) ? worldSkillGauge(s,who-1) : !worldVanish(s);
}

// Preserve native _is_normal: named pellet/core:pellet packets retain the
// normal landing category,independently from their skill formula and gauge.
bool worldPhysicalNormal(inout Runtime s,uint who)
{ uint flags=results[s.resourceOutput+WO_OUT+288+who*8+7];return (flags&1)==0 || (flags&2)!=0; }
