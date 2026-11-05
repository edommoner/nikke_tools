// Explicit partial model: live snapshot delivery, unresolved death is rejected.
#define WORLD_PACKET_CAPTURE(s,r,index,fallback) if(!lockDeliveryCapture(s,r,index)) { fallback }
#include "world_lock_packet_entry.slang"
#include "live_lock_delivery_runtime.slang"
