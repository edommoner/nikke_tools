// Completion fields use the canonical recipient selector and carrier engine.
// Only current-target field selectors inherit the captured logical Actor.
// Ranked/nearest selectors and generic named callbacks retain current aiming.
bool counterFieldsEnabled(inout Runtime s)
{ return WORLD_SKILL_FIELDS(s,targetCountersEnabled(s)&&commands[s.inputBase+P_TARGET_COUNTER_INPUT_BASE+6]==5); }
uint counterFieldFirst(inout Runtime s,uint route,uint legacy)
{ return counterFieldsEnabled(s)&&route==0 ? counterContextTarget(s,legacy) : legacy; }
bool counterFieldDefinitionInvalid(inout Runtime s,uint row,Definition d,bool legacy)
{
    if(!counterFieldsEnabled(s)||commands[counterPolicy(s,row)]!=0) return legacy;
    // Every stat/condition/selector/period/quantity rule has already passed the
    // common Actor field/status admission. Damage packets need their own queue.
    return d.kind!=0&&d.kind!=4;
}
void initializeCounterFieldWork(inout Runtime s)
{
    if(!counterFieldsEnabled(s)) return;
    for(uint i=0;i<8;i++) results[s.resourceOutput+P_COUNTER_FIELD_WORK_BASE+i]=0;
}
void recordCounterFieldWork(inout Runtime s,uint work)
{
    if(!counterFieldsEnabled(s)) return;
    uint at=s.resourceOutput+P_COUNTER_FIELD_WORK_BASE;
    if(results[at]==0x7fffffff||results[at+2]>0x7fffffff-work) { if(s.error==0) s.error=2;return; }
    results[at]++;results[at+1]=max(results[at+1],work);results[at+2]+=work;
    if(s.error==4) results[at+3]++;
}
