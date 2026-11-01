// A named modifier is carried unchanged; no spatial decision is inferred.
bool validProductNamedCarriers(inout Runtime s)
{
    uint found=0;
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);
        if(d.stat!=TC_STAT&&d.stat!=94U)continue;found++;
        if(d.targetName<0||d.targetName>=int(P_DEFINITIONS))return false;
        // All authored/generated definitions are in this complete static program.
        // Any consumer name requires the separately checked spatial/count path.
        for(uint other=0;other<s.count;other++)
            if(definition_name(s.inputBase,other)==uint(d.targetName))return false;
        if(d.kind!=0||d.enemyBuff!=0||d.lazyGroup!=0||d.queryResolve!=0||d.alliedFlags!=0||d.healthScaling!=0||d.quantityFlags!=0||d.damageFlags!=0||d.bulletDuration!=0||!f64Finite(d.value)||!f64Zero(d.interval))return false;
        uint plan=s.inputBase+P_RECIPIENT_BASE+row*8;
        if(commands[plan]!=0&&commands[plan]!=1&&commands[plan]!=12)return false;
        if(d.stat==94U&&f64Less(d.value,HUNDRED^F64_SIGN))return false;
    }
    return found!=0;
}
