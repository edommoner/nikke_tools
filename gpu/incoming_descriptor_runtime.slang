// One incoming executor with layout-specific descriptor providers.
// The world variant shares all target,damage,protection and notification math.
#ifdef PORTABLE_WORLD_FRAME
#include "world_frame_addresses.slang"
#else
[ForceInline]
uint incomingCommandAddress(inout Runtime s,uint arg) { return s.inputBase+P_COMMAND_BASE+arg*8; }
[ForceInline]
uint incomingDamageAddress(inout Runtime s,uint arg) { return s.inputBase+P_INCOMING_BASE+arg*P_INCOMING_WORDS; }
[ForceInline]
uint enemyRuleAddress(inout Runtime s,uint arg) { return s.inputBase+P_ENEMY_TARGET_COMMAND_BASE+arg*4; }
[ForceInline]
uint enemyQueryAddress(inout Runtime s,uint arg) { return s.resourceOutput+P_ENEMY_TARGET_QUERY_BASE+arg*8; }
[ForceInline]
uint incomingRecordAddress(inout Runtime s,uint arg,uint origin,uint member,bool primary,uint legacy) { return legacy; }
[ForceInline]
bool scheduledArgument(uint arg) { return false; }
[ForceInline]
bool worldFrameEnabled(inout Runtime s) { return false; }
[ForceInline]
bool initializeWorldFrame(inout Runtime s) { return true; }
[ForceInline]
void worldFrameBegin(inout Runtime s,uint64_t when) { }
[ForceInline]
void worldFrameDeliver(inout Runtime s,uint64_t when,uint output) { }
[ForceInline]
void worldFrameFinish(inout Runtime s) { }
#endif
