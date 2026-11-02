// One shared coordinate clock and typed world for weapons and original skills.
#ifndef PORTABLE_RESIDENT_FRAME_STACK
#define PORTABLE_RESIDENT_FRAME_STACK
#endif
#define PORTABLE_PRODUCT_MANUAL_COVER_LOG
#define PORTABLE_COORDINATE_LOGICAL_OWNERS
#define PORTABLE_COORDINATE_TYPED_MIXED
#define PORTABLE_PRODUCT_TYPED_NEARBY
#define PORTABLE_NAMED_RANGE_BATTLE
#define PORTABLE_PRODUCT_TYPED_LOCK
#define PORTABLE_PRODUCT_TYPED_MOTION
#define PORTABLE_ENEMY_MOVEMENT
#define PORTABLE_COORDINATE_TYPED_TARGETS
#define PORTABLE_COORDINATE_TYPED_WEAPONS
#define PORTABLE_COORDINATE_TYPED_AIM
#define PORTABLE_COORDINATE_TYPED_ACTORS
#define PORTABLE_COORDINATE_TYPED_OWNERS
#define DT_INPUT(s,offset) ((s).inputBase+115680U+(offset))
#define CTW_SCRATCH(s) DT_OUTPUT((s).resourceOutput,220768U)
#define DF_ROW_ENABLED(s,row) ((row)==commands[DF_DESCRIPTOR(s)])
#define DF_BODY_FALLBACK(s,row) false
#define DF_MATCH(s,row,at,selected) (results[at+3]!=0&&results[at]==2)
#include "product_typed_nearby_layout.slang"
#include "product_typed_movement_layout.slang"
#include "coordinate_area_hooks.slang"
#undef captureCoordinateCast
#define captureCoordinateCast captureNamedRangeBattleCast
#undef deliverCoordinateParts
#define deliverCoordinateParts deliverNamedRangeBattleParts
#include "product_coordinate_lock_battle_entry.slang"
#include "named_range_battle_runtime.slang"
#include "enemy_movement_runtime.slang"
