// One original coordinate runtime, with the complete original lock/typed arena.
#define PORTABLE_PRODUCT_COORDINATE_LOCK
#define PORTABLE_PRODUCT_COORDINATE
#define PORTABLE_PRODUCT_OUTLINED_HELPERS
#define PORTABLE_PRODUCT_LOCK_EMPTY
#define PORTABLE_LOCK_ENEMY_CARRIER
#define PORTABLE_EFFECT_TARGET_COUNT
#define PORTABLE_EFFECT_TARGET_COUNT_SHOTS
#define PORTABLE_GENERATION_LOCKS
#define PORTABLE_PHYSICAL_LOCKS
#define PORTABLE_PHYSICAL_LOCK_COVER
#define PORTABLE_PHYSICAL_LOCK_ARENA
#define PORTABLE_LOCK_PACKET_BINDINGS
#define PORTABLE_NAMED_ENEMY
#define PORTABLE_DESTRUCTIBLE_FRAME
#define PORTABLE_DESTRUCTIBLE_BATTLE
#define DF_DESCRIPTOR(s) ((s).inputBase+120800U)
#define DF_EXTRA(s) ((s).inputBase+115680U)
#define DT_OUTPUT(output,offset) ((output)+2032000U+(offset))
#define DF_BASE(output) DT_OUTPUT(output,1024U)
#define DF_HEADER(output) DT_OUTPUT(output,2816U)
#define DF_SCHEDULE(s,w,extra,output) WorldSchedule w=frameSchedule(s);
#define DF_SCRATCH(output,depth) DT_OUTPUT(output,153568U+uint(depth)*544U)
#define DF_VALID(s,d,descriptor) (commands[descriptor+3]==0x44425431U&&(d.damageFlags&~(H_NAMED_SKILL|524288U))==0)
#define DF_HAS_SAMPLE(s,row) destructibleActivationHasTargets(s,row)
#define DF_COEFF(s,scratch,output,value) dtStore(scratch+532,value);
#define DF_AMOUNT(s,scratch,output,value) dtStore(scratch+534,value);
#define DF_SELECTION(s,scratch,output,selected,f,d) destructibleBattleCapture(s,scratch,selected,f,d);
#define DF_RECEIPT(s,scratch,output,cursor) (results[scratch+530]+16+(cursor)*8)
#define DF_ATTACK_ID(s,scratch,descriptor) results[scratch+531]
#define DF_COMPLETE(s,scratch) if(results[scratch+531]!=0) results[results[scratch+530]+10]=1;
#define WORLD_PACKET_CAPTURE(s,r,index,fallback) if(compositionSuppressedReceipt(s,r,index,when)) return s.error==0; if(!lockDeliveryCapture(s,r,index)) { fallback }
#include "product_coordinate_lock_layout.slang"
#include "world_coordinate_logical_actor_entry.slang"
#include "live_lock_delivery_runtime.slang"
#include "destructible_target_core.slang"
#include "destructible_world_runtime.slang"
#include "destructible_battle_runtime.slang"
#include "packet_fates_runtime.slang"
#include "lock_enemy_carrier_runtime.slang"
#define pushSkillHit compositionPushSkillHit
#include "destructible_frame_runtime.slang"
#undef pushSkillHit
bool initializeCoordinateLocks(inout Runtime s)
{
    return initializePhysicalLocks(s)&&initializeLockPackets(s)&&initializeDestructibleBattle(s)&&initializePacketFates(s);
}
