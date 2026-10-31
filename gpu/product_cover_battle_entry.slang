// Shared product scheduler, original explicit controls and cover landing.
#define PORTABLE_COVER_DEFENSE
#define PORTABLE_PRODUCT_UNSPECIFIED_COVER
#define PORTABLE_COORDINATE_MANUAL_ACTIONS
#define PORTABLE_PRODUCT_MANUAL_COVER_LOG
#include "cover_defense_layout.slang"
#define portableEvents unusedProductCoverBaseEntry
#if defined(PORTABLE_PRODUCT_COVER_HEALING)
#define PORTABLE_PRODUCT_EXTERNAL_EXECUTOR
#include "product_healing_battle_entry.slang"
#elif defined(PORTABLE_PRODUCT_COVER_GROUP_TARGET)
#define PORTABLE_PRODUCT_EXTERNAL_EXECUTOR
#include "product_group_target_battle_entry.slang"
#elif defined(PORTABLE_PRODUCT_COVER_TARGET)
#define PORTABLE_PRODUCT_EXTERNAL_EXECUTOR
#include "product_target_battle_entry.slang"
#elif defined(PORTABLE_PRODUCT_COVER_GROUP)
#include "product_group_battle_entry.slang"
#else
#include "product_battle_entry.slang"
#endif
#undef portableEvents
#include "product_cover_entry.slang"
