// Shared product scheduler, original explicit controls and cover landing.
#define PORTABLE_COVER_DEFENSE
#define PORTABLE_PRODUCT_UNSPECIFIED_COVER
#define PORTABLE_COORDINATE_MANUAL_ACTIONS
#define PORTABLE_PRODUCT_MANUAL_COVER_LOG
#include "cover_defense_layout.slang"
#define portableEvents unusedProductCoverBaseEntry
#ifdef PORTABLE_PRODUCT_COVER_GROUP
#include "product_group_battle_entry.slang"
#else
#include "product_battle_entry.slang"
#endif
#undef portableEvents
#include "product_cover_entry.slang"
