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
#define DF_SELECTION(s,scratch,output,selected,f,d) destructibleBattleCapture(s,scratch,selected,f,d); if(results[scratch+530]!=0) results[scratch+530]-=output;
#define DF_RECEIPT(s,scratch,output,cursor) ((output)+results[scratch+530]+16+(cursor)*8)
#define DF_ATTACK_ID(s,scratch,descriptor) results[scratch+531]
#define DF_COMPLETE(s,scratch) if(results[scratch+531]!=0) results[(s).resourceOutput+results[scratch+530]+10]=1;
#ifdef PORTABLE_PRODUCT_TYPED_NEARBY
#define WORLD_PACKET_CAPTURE(s,r,index,fallback) if(compositionSuppressedReceipt(s,r,index,when)) return s.error==0; if(!captureNamedRangeBattlePacket(s,r,index)&&!lockDeliveryCapture(s,r,index)) { fallback }
#else
#define WORLD_PACKET_CAPTURE(s,r,index,fallback) if(compositionSuppressedReceipt(s,r,index,when)) return s.error==0; if(!lockDeliveryCapture(s,r,index)) { fallback }
#endif
#include "product_coordinate_lock_layout.slang"
#ifdef PORTABLE_PRODUCT_TYPED_MOTION
#undef TCS_TRACE_CAPACITY
#define TCS_TRACE_CAPACITY PTQ_KEEP
#undef TCS_TRACE_AT
#define TCS_TRACE_AT(s,index) ((s).resourceOutput+((index)<PTQ_PREFIX?PTQ_PREFIX_BASE+(index)*20U:PTQ_EXTRA+((index)-PTQ_PREFIX)*20U))
#undef WT_TRACE_CAPACITY
#define WT_TRACE_CAPACITY PTT_KEEP
#undef WT_TRACE_AT
#define WT_TRACE_AT(s,index) ((s).resourceOutput+((index)<PTT_PREFIX?PTT_PREFIX_BASE+(index)*8U:PTT_EXTRA+((index)-PTT_PREFIX)*8U))
#endif
#include "world_coordinate_logical_actor_entry.slang"
#include "live_lock_delivery_runtime.slang"
#ifdef PORTABLE_PRODUCT_TYPED_LOCK
#include "coordinate_typed_geometry_runtime.slang"
#define PORTABLE_EXTERNAL_DESTRUCTIBLE_FRAME
#include "destructible_shield_frame_impl.slang"
#undef PORTABLE_EXTERNAL_DESTRUCTIBLE_FRAME
#include "coordinate_typed_weapon_runtime.slang"
#include "coordinate_typed_aim_runtime.slang"
#include "coordinate_typed_actor_runtime.slang"
#include "coordinate_typed_owner_runtime.slang"
#else
#include "destructible_target_core.slang"
#include "destructible_world_runtime.slang"
#include "destructible_battle_runtime.slang"
#endif
#include "packet_fates_runtime.slang"
#include "lock_enemy_carrier_runtime.slang"
#define pushSkillHit compositionPushSkillHit
#ifdef PORTABLE_PRODUCT_TYPED_LOCK
#define damageValue modifierFrameDamage
#endif
#include "destructible_frame_runtime.slang"
#ifdef PORTABLE_PRODUCT_TYPED_LOCK
#undef damageValue
#endif
#undef pushSkillHit
bool initializeCoordinateLocks(inout Runtime s)
{
    bool ready=initializePhysicalLocks(s)&&initializeLockPackets(s)&&initializeDestructibleBattle(s)&&initializePacketFates(s);
#ifdef PORTABLE_PRODUCT_TYPED_LOCK
    ready=ready&&validBattleModifierAxes(s)&&validShieldBattleRoutes(s);
    for(uint row=0;row<256;row++)
        if(commands[DT_INPUT(s,5424)+row]!=(row==commands[DF_DESCRIPTOR(s)]?2U:0U))ready=false;
#endif
#ifdef PORTABLE_PRODUCT_MANUAL_COVER_LOG
    // Physical-lock initialization clears its whole arena, including CMC.
    // Restore the existing posture initializer before any battle frame runs.
    if(ready){initializeManualControls(s);ready=s.error==0;}
#endif
    return ready;
}
