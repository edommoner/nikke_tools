// Native enemy attack flat query. Resident activation, expiry, ordering, stacks,
// reference values, recipient membership and conditions stay in common code.
// Native incoming damage does not consume enemy atk_pct. Native get_buffs
// nevertheless includes it in the attacking ally's outgoing numeric query.
[noinline]
uint64_t collectWorldEnemyAttackFlat(inout Runtime s,uint target,uint64_t when)
{
    if((target&ACTOR_REF)!=0&&commands[actorBinding(s,target&127U)]==6) return 0;
    uint64_t total=0;
    for(uint i=0;i<s.orderedCount;i++)
    {
        uint row=s.orderedRows[i];Definition d=residentDefinition(s,row);
        if(d.kind!=0||d.stat!=S_atk_caster_based_pct||s.alive[row]==0||!f64Less(when,s.end[row])) continue;
#ifdef PORTABLE_COORDINATE_ORIGINAL_COVER_REVIVE
        // A final diagnostic must not resolve an allied late numeric selector.
        // Actual enemy-ATK reads and explicit actor queries keep native ordering.
        if(nativeNumericDiagnostic(s)&&d.enemyBuff==0) continue;
#endif
        // Native resolves _by_stat's lazy row before testing enemy membership,
        // including allied rows. This observable resolution affects later ranks.
        if(s.lazyPending[row]!=0) ensureLazyRecipients(s,row,when);
        if(d.enemyBuff==0||!actorFieldMember(s,row,target)||!actorFieldConditions(s,row,target,when)) continue;
        uint64_t value=scalarValue(s,row,d.owner);
        value=f64Mul(s.baseAttack[d.owner],f64Div(value,HUNDRED));total=f64Add(total,value);
        if(!f64Finite(value)||!f64Finite(total)) { s.error=16;return 0; }
    }
    return total;
}

// Keep the native get_buffs target branch inside the existing ordered scalar
// accumulator. Do not apply enemy fields to ally rank/base-stat helpers.
bool worldEnemyAttackDamageMember(inout Runtime s,uint row,uint who,uint64_t when)
{
    Definition d=residentDefinition(s,row);
    return worldEnemyAttackEnabled(s)&&d.enemyBuff!=0&&d.stat==S_atk_pct&&!excludedDamageBuff(s,row,who)&&actorFieldMember(s,row,s.target)&&actorFieldConditions(s,row,s.target,when);
}
