// Reuse the complete enemy magazine/ADD input and append literal cover bases.
// Existing ammo and cover output banks are disjoint and contiguous.
#define PORTABLE_PRODUCT_COVER_AMMO
#define PORTABLE_COVER_DEFENSE_INPUT_BASE EAM_INPUT_WORDS
#include "product_cover_battle_entry.slang"
