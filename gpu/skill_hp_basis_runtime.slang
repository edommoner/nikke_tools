// Tagged union in damage-kind mode words 20..23. Weapon rows keep their own ABI.
static const uint SKILL_HP_BASIS_MAGIC=0x48504231;
uint skillHPBasisAddress(inout Runtime s,uint row)
{ return s.inputBase+P_MODE_BASE+row*P_MODE_WORDS+20; }
uint skillHPBasisMode(inout Runtime s,uint row)
{
    if(row>=s.count || definition_kind(s.inputBase,row)!=3) return 0;
    uint at=skillHPBasisAddress(s,row);
    return commands[at]==SKILL_HP_BASIS_MAGIC ? commands[at+1] : 0;
}
bool validSkillHPBasis(inout Runtime s)
{
    for(uint row=0;row<s.count;row++)
    {
        if(definition_kind(s.inputBase,row)==2) continue;
        uint at=skillHPBasisAddress(s,row);
        if((commands[at]|commands[at+1]|commands[at+2]|commands[at+3])==0) continue;
#ifndef PORTABLE_WORLD_SKILLS
        return false;
#else
        uint64_t pct=loadNumber(at+2);Definition d=readDefinition(s.inputBase,row);
        if(commands[at]!=SKILL_HP_BASIS_MAGIC || commands[at+1]<1 || commands[at+1]>2 || d.kind!=3 || s.combat==0 || !worldSkillsEnabled(s) || d.damagePending!=0 || !f64Finite(pct) || f64Less(pct,0) || f64Less(f64FromI64(1000000),pct)) return false;
#endif
    }
    return true;
}
uint64_t skillAttackBasis(inout Runtime s,uint who,uint row,uint64_t when,uint64_t percent,uint64_t flat)
{
    uint64_t base=s.baseAttack[who];uint mode=skillHPBasisMode(s,row);
    if(mode!=0)
    {
        uint64_t pct=loadNumber(skillHPBasisAddress(s,row)+2);
        // Preserve native multiply-then-divide and addition into flat before ATK.
        uint64_t hp=f64Div(f64Mul(nativeAttackMaxHP(s,who,when),pct),HUNDRED);
        if(mode==1) flat=f64Add(flat,hp);
        else { base=hp;percent=0;flat=0; }
    }
    return f64Add(f64Mul(base,f64Add(ONE,f64Div(percent,HUNDRED))),flat);
}
