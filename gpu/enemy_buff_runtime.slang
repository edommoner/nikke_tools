// Each enemy receiver owns a resident lifetime/order and captured generation.
// Parent activation snapshots order and generations before synchronous children.
[noinline]
bool enemyCarrierSameLife(inout Runtime s, uint slot, uint recipients,uint incomingGeneration)
{
    for (uint target = 0; target < s.targetCount; target++)
        if ((recipients & (1U << (target+5))) != 0 && incomingGeneration != s.enemyCaptureGeneration[slot]) return false;
    return true;
}
[noinline]
void collectEnemyModifiers(inout Runtime s, uint who, uint target, uint64_t when, out uint64_t values[3])
{
    values[0] = 0; values[1] = 0; values[2] = 0;
    if (s.enemyBuffCount == 0 || s.combat == 0 || target >= s.targetCount || s.targetAlive[target] == 0) return;
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
        Definition d = residentDefinition(s,row);
        if (d.enemyBuff == 0 || s.alive[row] == 0 || !f64Less(when,s.end[row]) ||
            (s.activeRecipients[row] & (1U << (target+5))) == 0 || s.targetGeneration[target] != s.enemyCaptureGeneration[row] ||
            excludedDamageBuff(s,row,who) || !basicConditions(s,row,when,true,target+5)) continue;
        uint64_t value = scalarValue(s,row,who); uint key = d.stat == S_enemy_def_down_pct ? 0 : d.stat == S_def_caster_based_pct ? 1 : 2;
        if (key == 1) value = f64Mul(s.baseDefense[d.owner],f64Div(value,HUNDRED));
        values[key] = f64Add(values[key],value);
        if (!f64Finite(value) || !f64Finite(values[key])) { s.error = 16; return; }
    }
}
