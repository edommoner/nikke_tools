// One ActorPool/frame/scheduler, retaining both existing consumer histories.
#define PORTABLE_PRODUCT_OUTLINED_HELPERS
#define PORTABLE_PRODUCT_MOVEMENT_RANGE
#define PORTABLE_PRODUCT_MOVEMENT
#define PORTABLE_PRODUCT_NAMED_RANGE
#define PORTABLE_ENEMY_MOVEMENT
#define PORTABLE_NAMED_RANGE_BATTLE
#define PORTABLE_EFFECT_TARGET_COUNT
#define PORTABLE_NAMED_ENEMY
#include "product_movement_range_layout.slang"
#include "coordinate_area_hooks.slang"
#undef captureCoordinateCast
#define captureCoordinateCast captureNamedRangeBattleCast
#undef deliverCoordinateParts
#define deliverCoordinateParts deliverNamedRangeBattleParts
#define WORLD_PACKET_CAPTURE(s,r,index,fallback) if(!captureNamedRangeBattlePacket(s,r,index)) { fallback }
#include "world_coordinate_logical_actor_entry.slang"
#include "enemy_movement_runtime.slang"
#include "named_range_battle_runtime.slang"
