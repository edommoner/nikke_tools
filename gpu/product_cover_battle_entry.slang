// Shared product scheduler, original explicit controls and cover landing.
#define PORTABLE_COVER_DEFENSE
#define PORTABLE_COORDINATE_MANUAL_ACTIONS
#define PORTABLE_PRODUCT_MANUAL_COVER_LOG
#include "cover_defense_layout.slang"
#define portableEvents unusedProductCoverBaseEntry
#include "product_battle_entry.slang"
#undef portableEvents
#include "product_cover_entry.slang"
