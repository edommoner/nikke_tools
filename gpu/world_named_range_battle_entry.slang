// Original radial skill: same cast/queue, ActorPool, landing and events.
#define PORTABLE_NAMED_RANGE_BATTLE
#define PORTABLE_EFFECT_TARGET_COUNT
#define PORTABLE_NAMED_ENEMY
#include "named_range_battle_layout.slang"
#include "coordinate_area_hooks.slang"
#undef captureCoordinateCast
#define captureCoordinateCast captureNamedRangeBattleCast
#undef deliverCoordinateParts
#define deliverCoordinateParts deliverNamedRangeBattleParts
#define WORLD_PACKET_CAPTURE(s,r,index,fallback) if(!captureNamedRangeBattlePacket(s,r,index)) { fallback }
#include "world_coordinate_logical_actor_entry.slang"
#include "named_range_battle_runtime.slang"
