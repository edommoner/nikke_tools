// Native enemy attack flat query. Resident activation, expiry, ordering, stacks,
// reference values, recipient membership and conditions stay in common code.
// Enemy atk_pct is a named state; native incoming damage does not consume it.
[noinline]
uint64_t collectWorldEnemyAttackFlat(inout Runtime s,uint target,uint64_t when)
{
    uint64_t total=0;
    for(uint i=0;i<s.enemyBuffCount;i++)
    {
        uint row=s.enemyBuffRows[i];Definition d=residentDefinition(s,row);
        if(d.enemyBuff==0||d.kind!=0||d.stat!=S_atk_caster_based_pct||s.alive[row]==0||!f64Less(when,s.end[row])||!actorFieldMember(s,row,target)||!actorFieldConditions(s,row,target,when)) continue;
        uint64_t value=scalarValue(s,row,d.owner);
        value=f64Mul(s.baseAttack[d.owner],f64Div(value,HUNDRED));total=f64Add(total,value);
        if(!f64Finite(value)||!f64Finite(total)) { s.error=16;return 0; }
    }
    return total;
}
