// Full skill history shares the existing weapon-only runtime and wire.
#include "skill_history_layout.slang"
#ifdef PORTABLE_PRODUCT_TYPED_LOGICAL
// Product initialization has validated each exact BODY/ADD owner. Both policies
// share this existing skill-history bank; private BODY-only admission stays1.
#undef WORLD_SKILL_HISTORY_ADMIT
#define WORLD_SKILL_HISTORY_ADMIT(s) (commands[(s).inputBase+109968U+13U]==1U && commands[(s).inputBase+109968U+14U]==1U && commands[(s).inputBase+109968U+15U]==2U && (commands[(s).inputBase+109968U+12U]==1U || commands[(s).inputBase+109968U+12U]==3U))
#endif
#include "world_coordinate_typed_owner_entry.slang"
