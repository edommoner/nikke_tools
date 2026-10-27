// Static wiring only. One WorldSchedule/DFS stack owns both existing executors.
#define PORTABLE_LOCK_TYPED_COMPOSITION
#define PORTABLE_PROJECTILE_CHAIN
#define PORTABLE_FULL_BURST_LANDING
#define PL_LAYOUT_OFFSET 262144U
#define PL_LAYOUT_OUTPUT 1310720U
#define PORTABLE_RESIDENT_RUNTIME
#define PORTABLE_DESTRUCTIBLE_FRAME
#define PORTABLE_DESTRUCTIBLE_BATTLE
#define DT_OUTPUT(output,offset) ((output)+786432+(offset))
#define DF_DESCRIPTOR(s) ((s).inputBase+109520)
#define DF_EXTRA(s) ((s).inputBase+104400)
#define DF_BASE(output) ((output)+787456)
#define DF_HEADER(output) ((output)+789248)
#define DF_SCHEDULE(s,w,extra,output) WorldSchedule w=frameSchedule(s);
#define DF_SCRATCH(output,depth) ((output)+940000+uint(depth)*544)
#define DF_VALID(s,d,descriptor) (commands[descriptor+3]==0x44425431U&&(d.damageFlags&~(H_NAMED_SKILL|524288U))==0)
#define DF_HAS_SAMPLE(s,row) destructibleActivationHasTargets(s,row)
#define DF_COEFF(s,scratch,output,value) dtStore(scratch+532,value);
#define DF_AMOUNT(s,scratch,output,value) dtStore(scratch+534,value);
#define DF_SELECTION(s,scratch,output,selected,f,d) destructibleBattleCapture(s,scratch,selected,f,d);
#define DF_RECEIPT(s,scratch,output,cursor) (results[scratch+530]+16+(cursor)*8)
#define DF_ATTACK_ID(s,scratch,descriptor) results[scratch+531]
#define DF_COMPLETE(s,scratch) if(results[scratch+531]!=0) results[results[scratch+530]+10]=1;
#define WORLD_PACKET_CAPTURE(s,r,index,fallback) if(compositionSuppressedReceipt(s,r,index,when)) return s.error==0; if(!lockDeliveryCapture(s,r,index)) { fallback }
#define portableEvents unusedNormalLockEntry
#include "world_lock_packet_entry.slang"
#include "live_lock_delivery_runtime.slang"
#undef portableEvents
#include "destructible_target_core.slang"
#include "destructible_world_runtime.slang"
#include "destructible_battle_runtime.slang"
#include "packet_fates_runtime.slang"
#define pushSkillHit compositionPushSkillHit
#include "destructible_frame_runtime.slang"
#undef pushSkillHit

[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*109536,output=id.x*1310720;WORLD_TEAM_INPUT(input,output)
    for(uint i=786432;i<1048576;i++)results[output+i]=0;
    initializeRuntime(runtimeStates[id.x]);bool ready;
    initializePortableProgram(runtimeStates[id.x],input,output,ready);if(!ready)return;
    if(!initializeDestructibleBattle(runtimeStates[id.x])){results[output]=64;return;}
    if(!initializePacketFates(runtimeStates[id.x])){results[output]=64;return;}
    uint queries;executePortableCommands(runtimeStates[id.x],input,output,queries);
    writePortableProgram(runtimeStates[id.x],input,output,queries);
}
