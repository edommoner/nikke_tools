// Shared main feature chain with nonoverlapping coordinate and group arenas.
#define PORTABLE_COMPOSED_ARENA
#define PORTABLE_ATTACK_GROUPS
#define PORTABLE_WORLD_PROJECTILE_DIAGNOSTIC
#define PORTABLE_COORDINATE_LEGACY_PENDING
#define PORTABLE_COORDINATE_FULL_BURST_PENDING
#define PORTABLE_FULL_BURST_LANDING
#include "coordinate_area_hooks.slang"
#define portableEvents legacyCoordinatePoolEvents
#include "world_projectile_chain_entry.slang"
#include "world_coordinate_area_entry.slang"
