// Receiver routing only:status arithmetic,caps,scratch order,and retirement
// remain in the one common status_runtime loop used by CUDA and Metal.
bool actorStatusEnabled(inout Runtime s)
{ return WORLD_STACK_POLICY(s,actorFieldsEnabled(s)&&commands[s.inputBase+P_WORLD_ACTOR_POOL_INPUT_BASE+4]==0x57493031); }
bool actorStatusFieldInvalid(inout Runtime s,Definition d)
{
    bool accumStat=false;
#ifdef PORTABLE_DAMAGE_ACCUM
    accumStat=d.stat>=81U && d.stat<=83U;
#endif
#ifdef PORTABLE_ENEMY_HEALING
    accumStat=accumStat || d.stat==S_heal_received_pct;
#endif
    return d.kind!=0&&d.kind!=4 || d.kind==4&&d.stat!=0 || d.kind==0&&WORLD_ENEMY_ATTACK_INVALID(s,d,d.stat!=S_enemy_def_down_pct&&d.stat!=S_def_caster_based_pct&&d.stat!=S_received_dmg_pct && !namedMagnitudeStat(d.stat) && !accumStat && !projectileCarrierStat(d.stat) && d.stat!=S_taunt && d.stat!=S_stun);
}
bool actorStatusScopeValid(inout Runtime s,Definition d)
{
    if(d.target!=2||d.damageRoute!=3) return true;
    for(uint slot=1;slot<actorPoolCount(s);slot++) if(commands[actorBinding(s,slot)]==5&&commands[actorPoolDef(s,slot)]==3) return false;
    return true;
}
uint actorStatusUsed(inout Runtime s,uint who,uint name)
{
    if(actorStatusEnabled(s)&&who>=5)
    { if(who-5>=actorPoolCount(s)||name>=P_DEFINITIONS) { s.error=64;return s.resourceOutput+P_WORLD_ACTOR_WIDE_IMMUNITY_BASE; }return s.resourceOutput+P_WORLD_ACTOR_WIDE_IMMUNITY_BASE+((who-5)*P_DEFINITIONS+name)*2; }
    return s.resourceOutput+P_IMMUNITY_USED_BASE+(who*P_DEFINITIONS+name)*2;
}
bool actorStatusMemberInvalid(inout Runtime s,uint row,uint who)
{
    if(actorStatusEnabled(s)&&who>=5) return !actorRecipientMember(s,row,who==5?0:ACTOR_REF|(who-5));
    return (s.activeRecipients[row]&(1U<<who))==0;
}
// Native count pools inspect target_chars,including a stale generation during
// synchronous spawn notifications. Deferred target drop owns membership removal.
bool actorStatusCountMemberInvalid(inout Runtime s,uint row,uint who)
{
    if(actorStatusEnabled(s)&&who>=5) return !actorRecipientHas(s,row,who-5);
    return (s.activeRecipients[row]&(1U<<who))==0;
}
bool actorStatusVisible(inout Runtime s,uint row,uint who)
{
    if(actorStatusEnabled(s)&&who>=5) return who-5<actorPoolCount(s)&&results[actorPoolAt(s,who-5)+1]!=0&&actorRecipientMember(s,row,who==5?0:ACTOR_REF|(who-5));
    return who<5 || (s.targetAlive[who-5]!=0&&s.targetGeneration[who-5]==enemyCarrierGeneration(s,row,who-5));
}
uint actorStatusScope(inout Runtime s,uint row,out ActorBits bits)
{
    return actorFieldScope(s,row,bits);
}
uint actorStatusCleanseMembers(inout Runtime s,uint row,uint who,uint bit)
{
    if(actorStatusEnabled(s)&&who>=5)
    {
        uint slot=who-5,at=actorRecipientAt(s,row);results[at+2+slot/32]&=~(1U<<(slot%32));
        return actorRecipientAny(s,row)?s.activeRecipients[row]:s.activeRecipients[row]&~32U;
    }
    else return s.activeRecipients[row]&~bit;
}
