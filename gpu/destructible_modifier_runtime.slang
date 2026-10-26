// Declared v1 target factor. Carrier lifecycle, recipient tests, stack values,
// seven-factor sampling and final rounding remain in the common executor.
uint64_t destructibleModifierQuantity(inout Runtime s,uint axisTable,uint who,uint kind,uint64_t when)
{
    uint64_t value=0;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass],definition=s.carrierDefinition[row];
        if(commands[axisTable+definition]!=kind || !queryRecipient(s,row,who,when)) continue;
        Definition d=residentDefinition(s,row);
        value=f64Add(value,d.queryResolve!=0 && d.alliedFlags==0 ? recipientValue(s,row,who) : scalarValue(s,row,who));
    }
    if(!f64Finite(value)) s.error=64;
    return value;
}
uint64_t destructibleModifierDamage(inout Runtime s,uint axisTable,uint who,uint kind,uint64_t coefficient,uint64_t when,out uint64_t factor5,out uint64_t projectile,out uint64_t shield,uint basisRow=P_DEFINITIONS)
{
    uint64_t factors[9];sampleDamageFactors(s,who,coefficient,when,factors,false,s.coreBonus,0,ONE,false,false,basisRow);
    projectile=destructibleModifierQuantity(s,axisTable,who,2,when);
    shield=destructibleModifierQuantity(s,axisTable,who,3,when);
    if(kind==2) factors[4]=f64Add(factors[4],f64Div(projectile,HUNDRED));
    else if(kind==3) factors[4]=f64Add(factors[4],f64Div(shield,HUNDRED));
    else if(kind!=0) s.error=64;
    factor5=factors[4];return s.error==0 ? damageFromFactors(s,factors,false) : uint64_t(0);
}
