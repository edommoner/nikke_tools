// Canonical current-damage selection stays separate from interception handles.
bool typedActorPolicyEnabled(inout Runtime s){return commands[DF_EXTRA(s)+15]==1;}
bool validTypedActorPolicy(inout Runtime s)
{
    if(!typedActorPolicyEnabled(s))return true;
    for(uint row=0;row<s.count;row++)
        if(definition_kind(s.inputBase,row)!=3&&definition_enemyBuff(s.inputBase,row)!=0&&definition_damageRoute(s.inputBase,row)==0)return false;
    return true;
}
uint typedActorCurrentDamageFirst(inout Runtime s,uint row,uint route,uint legacy)
{
    if(typedActorPolicyEnabled(s)&&row<s.count&&definition_kind(s.inputBase,row)==3&&route==0)
    {
        uint pointer=counterContextEnabled(s)?results[counterContextHead(s)+1]:0;
        if(pointer!=0)
        {
            uint kind=results[pointer-1+5];
            // A typed hit/death notification still owns its physical identity.
            // Ordinary current damage uses the caster's canonical aim enemy.
            if(kind==2||kind==3||kind==4)return legacy;
        }
    }
    return COUNTER_FIELDS_FIRST(s,route,legacy);
}
