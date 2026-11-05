// A disjoint tagged MODE payload, preserving canonical kind4/stat0 identity.
bool namedSkillInterval(inout Runtime s,uint row)
{ return (definition_quantityFlags(s.inputBase,row)&P_SKILL_INTERVAL_FLAG)!=0; }
uint skillIntervalMeta(inout Runtime s,uint row)
{ return s.inputBase+P_MODE_BASE+row*P_MODE_WORDS+P_SKILL_INTERVAL_OFFSET; }
[noinline]
bool validSkillIntervals(inout Runtime s)
{
    for(uint row=0;row<s.count;row++) if(namedSkillInterval(s,row))
    {
#ifndef PORTABLE_WORLD_ROSTER
        return false;
#else
        Definition d=readDefinition(s.inputBase,row);uint meta=skillIntervalMeta(s,row);
        if(s.combat==0 || d.kind!=4 || d.stat!=0 || d.quantityFlags!=P_SKILL_INTERVAL_FLAG || d.enemyBuff!=0 ||
           d.alliedFlags!=0 || d.healthScaling!=0 || d.damageFlags!=0 || !f64Finite(d.value) ||
           commands[meta]!=P_SKILL_INTERVAL_MAGIC || commands[meta+1]<1 || commands[meta+1]>2 ||
           commands[meta+2]>=P_DEFINITIONS || commands[meta+3]>1) return false;
        for(uint field=P_SKILL_INTERVAL_END;field<P_MODE_WORDS;field++)
            if(commands[s.inputBase+P_MODE_BASE+row*P_MODE_WORDS+field]!=0) return false;
        s.quantityMask|=4096;
#endif
    }
    return true;
}
