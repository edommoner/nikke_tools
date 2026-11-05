// Mutable copy state belongs to the exact carrier and entry generation.
bool baseCopyStat(uint stat) { return stat==S_atk_copy || stat==S_hp_copy; }
bool baseCopyDefinition(inout Runtime s,uint row)
{ return (definition_quantityFlags(s.inputBase,row)&P_BASE_COPY_FLAG)!=0; }
uint baseCopyAddress(inout Runtime s,uint row) { return s.resourceOutput+P_BASE_COPY_STATE_BASE+row*6; }
uint64_t copyNumber(uint at) { return uint64_t(results[at])|(uint64_t(results[at+1])<<32); }
uint64_t baseCopyContribution(inout Runtime s,uint row,uint who)
{ return f64Div(f64Mul(copyNumber(baseCopyAddress(s,row)),scalarValue(s,row,who)),HUNDRED); }
[noinline]
void prepareBaseCopy(inout Runtime s,uint row,bool fresh)
{
#ifdef PORTABLE_WORLD_PROJECTILE
    Definition d=residentDefinition(s,row);if(!baseCopyStat(d.stat) || d.kind!=0) return;
    uint at=baseCopyAddress(s,row),source=5;uint64_t best=0;
    if(fresh) for(uint word=0;word<6;word++) results[at+word]=0;
    for(uint who=0;who<5;who++) if((s.downMask&(1U<<who))==0)
    {
        uint64_t value=d.stat==S_atk_copy ? s.baseAttack[who] : s.baseHP[who];
        if(source==5 || f64Less(best,value)) { source=who;best=value; }
    }
    storeNumber(at,best);results[at+4]=source==5 ? 0 : source+1;results[at+5]=s.entryOrder[row];
#endif
}
uint64_t prepareCopyGrant(inout Runtime s,uint row)
{
    uint at=baseCopyAddress(s,row);uint64_t amount=baseCopyContribution(s,row,definition_owner(s.inputBase,s.carrierDefinition[row]));
    uint64_t previous=copyNumber(at+2);storeNumber(at+2,amount);
    return larger(0,f64Add(amount,previous^F64_SIGN));
}
[noinline]
bool validBaseCopies(inout Runtime s)
{
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);bool tagged=baseCopyDefinition(s,row);
        if(baseCopyStat(d.stat)!=tagged) return false;
        if(!tagged) continue;
#ifndef PORTABLE_WORLD_PROJECTILE
        return false;
#else
        uint meta=s.inputBase+P_MODE_BASE+row*P_MODE_WORDS;
        if(s.combat==0 || d.kind!=0 || d.target>1 || d.enemyBuff!=0 || d.quantityFlags!=P_BASE_COPY_FLAG ||
           d.healthScaling!=0 || d.alliedFlags!=0 || d.bulletDuration!=0 || d.damageFlags!=0 || !f64Finite(d.value) ||
           referenceScaleMode(s,row)!=0 || commands[meta+P_BASE_COPY_OFFSET]!=P_BASE_COPY_MAGIC ||
           commands[meta+P_BASE_COPY_OFFSET+1]!=d.stat || commands[meta+P_BASE_COPY_OFFSET+2]!=(d.stat==S_atk_copy ? 1U:2U) || commands[meta+P_BASE_COPY_OFFSET+3]!=0) return false;
        for(uint field=P_BASE_COPY_END;field<P_MODE_WORDS;field++) if(commands[meta+field]!=0) return false;
        s.quantityMask|=8192;
        if(d.stat==S_hp_copy) s.healthMask|=1;
#endif
    }
    return true;
}
