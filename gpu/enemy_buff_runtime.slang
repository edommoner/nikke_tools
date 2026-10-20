#ifdef PORTABLE_WORLD_OVERLAYS
#define WORLD_ENEMY_EMPTY(s) false
#define WORLD_ENEMY_SETUP uint worldVisited=0;
#define WORLD_ENEMY_BEFORE(s,row,target,values) if(target==0) worldEnemyUntil(s,s.entryOrder[row],worldVisited,values[2]);
#define WORLD_ENEMY_FINISH(s,target,values) if(target==0) worldEnemyUntil(s,0xffffffffU,worldVisited,values[2]);
#else
#define WORLD_ENEMY_EMPTY(s) s.enemyBuffCount == 0
#define WORLD_ENEMY_SETUP
#define WORLD_ENEMY_BEFORE(s,row,target,values)
#define WORLD_ENEMY_FINISH(s,target,values)
#endif
// Initializers can create a shared enemy carrier. Its generation vector uses
// the bullet-only words (enemy finite bullet clocks are not admitted).
uint enemyCarrierGeneration(inout Runtime s,uint slot,uint target)
{ return s.bulletInitialized[slot]!=2 ? s.enemyCaptureGeneration[slot] : target<5 ? s.recipientBullets[slot*5+target] : s.recipientStacks[slot*5+target-5]; }
// Each enemy receiver owns a resident lifetime/order and captured generation.
// Parent activation snapshots order and generations before synchronous children.
[noinline]
bool enemyCarrierSameLife(inout Runtime s, uint slot, uint recipients,uint incomingGeneration)
{
    WORLD_FIELDS_SAME(s,slot,recipients,incomingGeneration) for (uint target = 0; target < s.targetCount; target++)
        if ((recipients & (1U << (target+5))) != 0 && incomingGeneration != enemyCarrierGeneration(s,slot,target)) return false;
    return true;
}
[noinline]
void collectEnemyModifiers(inout Runtime s, uint who, uint target, uint64_t when, out uint64_t values[3])
{
    values[0] = 0; values[1] = 0; values[2] = 0; WORLD_ENEMY_SETUP
    if (WORLD_ENEMY_EMPTY(s) || s.combat == 0 || WORLD_FIELDS_QUERY_DEAD(s,target,target >= s.targetCount || s.targetAlive[target] == 0)) return;
#ifdef PORTABLE_ENEMY_BUFF_SCAN_REFERENCE
    uint count = s.orderedCount;
#else
    uint count = s.enemyBuffCount;
#endif
    for (uint i = 0; i < count; i++)
    {
#ifdef PORTABLE_ENEMY_BUFF_SCAN_REFERENCE
        uint row = s.orderedRows[i];
#else
        uint row = s.enemyBuffRows[i];
#endif
        WORLD_ENEMY_BEFORE(s,row,target,values) Definition d = residentDefinition(s,row);
        if (d.enemyBuff == 0 || d.kind!=0 || s.alive[row] == 0 || !f64Less(when,s.end[row]) ||
            WORLD_FIELDS_MEMBER_INVALID(s,row,target,(s.activeRecipients[row] & (1U << (target+5))) == 0 || s.targetGeneration[target] != enemyCarrierGeneration(s,row,target)) ||
            excludedDamageBuff(s,row,who) || !WORLD_FIELDS_CONDITION(s,row,target,when,basicConditions(s,row,when,true,target+5))) continue;
        if(d.stat==S_taunt) continue;
        uint64_t value = scalarValue(s,row,who); uint key = d.stat == S_enemy_def_down_pct ? 0 : d.stat == S_def_caster_based_pct ? 1 : 2;
        if (key == 1) value = f64Mul(s.baseDefense[d.owner],f64Div(value,HUNDRED));
        values[key] = f64Add(values[key],value);
        if (!f64Finite(value) || !f64Finite(values[key])) { s.error = 16; return; }
    } WORLD_ENEMY_FINISH(s,target,values)
}

#undef WORLD_ENEMY_EMPTY
#undef WORLD_ENEMY_SETUP
#undef WORLD_ENEMY_BEFORE
#undef WORLD_ENEMY_FINISH
