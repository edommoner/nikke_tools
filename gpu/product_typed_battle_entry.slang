// Ordinary product admission over the original typed owner/skill-history executor.
#define PORTABLE_COORDINATE_TYPED_MIXED
#define PORTABLE_PRODUCT_TYPED_LOGICAL
#define PORTABLE_COORDINATE_LOGICAL_ACTORS
#define PORTABLE_LOGICAL_INPUT_BASE 115680U
#define PORTABLE_PRODUCT_COORDINATE
#define PORTABLE_PRODUCT_OUTLINED_HELPERS
#define PORTABLE_PRODUCT_TYPED_NEARBY
#define PORTABLE_NAMED_RANGE_BATTLE
#define PORTABLE_EFFECT_TARGET_COUNT
#define PORTABLE_NAMED_ENEMY
#include "product_typed_nearby_layout.slang"
#include "coordinate_area_hooks.slang"
#undef captureCoordinateCast
#define captureCoordinateCast captureNamedRangeBattleCast
#undef deliverCoordinateParts
#define deliverCoordinateParts deliverNamedRangeBattleParts
#define WORLD_PACKET_CAPTURE(s,r,index,fallback) if(!captureNamedRangeBattlePacket(s,r,index)) { fallback }
#include "world_coordinate_typed_history_entry.slang"
#include "named_range_battle_runtime.slang"
