// Completion fields use the canonical recipient selector and carrier engine.
// Only current-target field selectors inherit the captured logical Actor.
// Ranked/nearest selectors and generic named callbacks retain current aiming.
bool counterFieldsEnabled(inout Runtime s)
{ return targetCountersEnabled(s)&&commands[s.inputBase+P_TARGET_COUNTER_INPUT_BASE+6]==5; }
uint counterFieldFirst(inout Runtime s,uint route,uint legacy)
{ return counterFieldsEnabled(s)&&route==0 ? counterContextTarget(s,legacy) : legacy; }
bool counterFieldDefinitionInvalid(inout Runtime s,uint row,Definition d,bool legacy)
{
    if(!counterFieldsEnabled(s)||commands[counterPolicy(s,row)]!=0) return legacy;
    // Every stat/condition/selector/period/quantity rule has already passed the
    // common Actor field/status admission. Damage packets need their own queue.
    return d.kind!=0&&d.kind!=4;
}
