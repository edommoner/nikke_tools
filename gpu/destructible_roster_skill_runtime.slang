// Reuse actor selection, factor sampling, rounded quantities and the typed DFS
// Frame. These functions own neither a clock nor a second skill formula.
bool rosterShieldSkillsEnabled(inout Runtime s)
{ return commands[s.inputBase+110080]==0x48534934U&&commands[s.inputBase+110085]==1; }
bool rosterShieldSkillDefinition(inout Runtime s,Definition d)
{
    uint allowed=H_NAMED_SKILL|524288U|H_BURST|H_AOE_BURST|H_SINGLE_BURST;
    if((d.damageFlags&(H_AOE_BURST|H_SINGLE_BURST))!=0&&(d.damageFlags&H_BURST)==0) return false;
    if((d.damageFlags&(H_AOE_BURST|H_SINGLE_BURST))==(H_AOE_BURST|H_SINGLE_BURST)) return false;
    return actorPoolCount(s)==1&&d.kind==3&&d.stat==0&&d.enemyBuff==0&&d.alliedFlags==0&&d.periodicFlags==0&&f64Zero(d.interval)&&d.damageRoute>=1&&d.damageRoute<=9&&d.damageCount>=1&&d.damageCount<=128&&d.damageHits==1&&d.damagePending==0&&d.damageNormal==0&&(d.damageFlags&~allowed)==0&&d.healthScaling==0&&d.quantityFlags==0&&dtQuantity(d.value);
}
bool rosterShieldSkillBody(inout Runtime s,Definition d,Frame f)
{
    uint index=0;while(index<P_WORLD_ACTOR_SETS&&results[actorPoolSet(s,index)+5]!=0) index++;
    if(index==P_WORLD_ACTOR_SETS) { s.error=64;return false; }
    actorSetCapture(s,33,index,d.damageRoute,d.damageCount,f.target,d.owner NAMED_ENEMY_ARGUMENT(d._wireRow));
    if(s.error!=0) return false;
    uint at=actorPoolSet(s,index),body=actorPoolAt(s,0);
    bool resolved=results[at]==1&&results[at+8]==0&&results[at+9]==results[body]&&results[body+1]!=0;
    for(uint i=0;i<P_WORLD_ACTOR_SET_WORDS;i++) results[at+i]=0;
    results[actorPoolHead(s)+7]--;return resolved;
}
uint64_t rosterShieldSkillDamage(inout Runtime s,uint who,uint64_t coefficient,uint64_t when,bool normal,uint64_t coreBonus,uint flags,uint64_t charge,bool optimal,bool physical,uint row)
{
    if(row>=s.count||normal||optimal||physical||!f64Equal(coreBonus,s.coreBonus)||!f64Equal(charge,ONE)||!DF_ROW_ENABLED(s,row)||!rosterShieldSkillDefinition(s,readDefinition(s.inputBase,row))) { s.error=64;return 0; }
    uint count=commands[DF_EXTRA(s)+2320],base=DF_BASE(s.resourceOutput),kind=0;bool found=false;
    for(uint slot=0;slot<count;slot++)
    { uint at=dtAt(base,slot);if(DF_MATCH(s,row,at,0)) { kind=results[at]==4?0:3;found=true;break; } }
    if(!found) { s.error=64;return 0; }
    uint64_t factors[9],intercept,explosion,pierce;uint sampled;
    sampleDamageFactorsForReach(s,who,coefficient,when,factors,intercept,explosion,pierce,sampled,false,normal,coreBonus,flags,charge,optimal,physical,row);
    uint64_t shield=destructibleModifierQuantity(s,s.inputBase+109568,who,3,when);
    if(kind==3) factors[4]=f64Add(factors[4],f64Div(shield,HUNDRED));
    return s.error==0?damageFromFactors(s,factors,false):uint64_t(0);
}
