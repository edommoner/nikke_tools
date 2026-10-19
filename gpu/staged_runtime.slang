// Shared staged application schedule; each record occupies six output words.
uint stagedAddress(inout Runtime s, uint row) { return s.resourceOutput+P_STAGED_STATE_BASE+row*6; }
uint stagedDefinition(inout Runtime s, uint row) { return s.inputBase+P_STAGED_DEFINITION_BASE+row*8; }
bool isStaged(inout Runtime s, uint row) { return commands[stagedDefinition(s,row)]!=0; }
uint stagedGeneration(inout Runtime s, uint row) { return results[stagedAddress(s,row)]; }
uint64_t stagedNext(inout Runtime s, uint row)
{
    uint at=stagedAddress(s,row);
    return f64Add(sourceNumber(at+4),f64Mul(f64FromI64(results[at+3]+1),loadNumber(stagedDefinition(s,row)+2)));
}
[noinline]
uint stagedCount(inout Runtime s, uint row)
{
    uint code=commands[stagedDefinition(s,row)+1]; uint64_t value;
    if (code<=64) return code;
    uint key=code-256; bool present;
    value=referenceCount(s,definition_owner(s.inputBase,row),key,commands[s.inputBase+P_RESOURCE_NAME_BASE+key],false,present);
    if (!present) return 1;
    if (f64Less(value,0) || f64Less(f64FromI64(64),value)) { s.error=2; return 0; }
    uint status; uint64_t count=f64ToI64(value,1,status);
    if (status!=0) { s.error=2; return 0; }
    return uint(count);
}
[noinline]
void prepareStaged(inout Runtime s, uint row, uint count, uint64_t when, bool previousCarrier)
{
    uint at=stagedAddress(s,row), global=s.resourceOutput+P_STAGED_HEADER_BASE;
    uint generation=previousCarrier ? results[at] : 0;
    if (generation==0x7fffffff || results[global]==0x7fffffff) { s.error=2; return; }
    results[at]=generation+1;results[at+1]=++results[global];results[at+2]=count;results[at+3]=0;storeNumber(at+4,when);
    uint64_t last=f64Add(when,f64Mul(f64FromI64(count),loadNumber(stagedDefinition(s,row)+2)));
    s.stacks[row]=0;s.end[row]=f64Less(definition_duration(s.inputBase,row),0) ? FOREVER : f64Add(last,definition_duration(s.inputBase,row));
    s.expiry[row]=s.end[row];s.due[row]=f64Add(last,loadNumber(stagedDefinition(s,row)+4));
}
[noinline]
bool initializeStaged(inout Runtime s)
{
    for (uint i=0;i<8;i++) results[s.resourceOutput+P_STAGED_HEADER_BASE+i]=0;
    for (uint i=0;i<P_DEFINITIONS*6;i++) results[s.resourceOutput+P_STAGED_STATE_BASE+i]=0;
    uint index=s.inputBase+P_STAGED_INDEX_BASE,total=commands[index],found=0;
    if(total>s.count) return false;
    for (uint row=0;row<s.count;row++)
    {
        uint at=stagedDefinition(s,row), flag=commands[at];
        if (flag==0) { for (uint i=1;i<8;i++) if(commands[at+i]!=0) return false;continue; }
        Definition d=readDefinition(s.inputBase,row);uint code=commands[at+1],parent=commands[at+7];uint64_t gap=loadNumber(at+2),post=loadNumber(at+4);
        if(flag!=1 || d.kind!=3 || d.damageFlags!=H_DOT || (d.periodicFlags&3)!=3 || !f64Finite(d.interval) || !f64Less(0,d.interval) || referenceScaleMode(s,row)!=0 || parent==0 || parent>s.count || parent==row+1 || commands[at+6]>65) return false;
        Definition p=readDefinition(s.inputBase,parent-1);
        if(p.kind!=3 || !f64Zero(p.interval) || p.owner!=d.owner || (p.damageFlags & ~(H_BURST|H_ARMOR|H_SEQUENTIAL|H_SPLIT|H_AOE_BURST|H_SINGLE_BURST))!=0) return false;
        if(code>64 && (code<256 || code-256>=s.resourceCount)) return false;
        if(!f64Finite(gap) || f64Less(gap,uint64_t(0x3eb0c6f7)<<32|0xa0b5ed8d) || f64Less(f64FromI64(60),gap) || !f64Finite(post) || f64Less(post,0) || f64Less(f64FromI64(3600),post)) return false;
        if(!f64Finite(d.duration) || (d.maxStack!=0xffffffff && (d.maxStack==0 || d.maxStack>64)) || !(f64Equal(d.duration,ONE|F64_SIGN) || f64Less(0,d.duration) && !f64Less(f64FromI64(86400),d.duration))) return false;
        if(found>=total || commands[index+1+found]!=row) return false;
        found++;
    }
    if(found!=total) return false;
    for(uint i=total;i<P_DEFINITIONS;i++) if(commands[index+1+i]!=0) return false;
    s.stagedEnabled=total;
    return true;
}
