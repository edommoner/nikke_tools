        if(kind!=0&&kind!=2&&kind!=3&&kind!=4&&kind!=6&&kind!=7&&kind!=8&&kind!=24
#ifdef PORTABLE_COORDINATE_ORIGINAL_RESOURCES
            &&kind!=9&&kind!=10 // Existing shared gauge charge/consume handlers.
#endif
#ifdef PORTABLE_COORDINATE_ORIGINAL_CLOCKS
            &&kind!=22 // Existing shared remaining skill-clock reduction.
#endif
#ifdef PORTABLE_COORDINATE_ORIGINAL_ROSTER
            &&kind!=1 // Existing named removal, recipient snapshot and callbacks.
#endif
#ifdef PORTABLE_COORDINATE_HEALING
            &&kind!=32 // Existing received-healing pool discharge, including lifecycle.
#endif
#ifdef PORTABLE_COORDINATE_BURST_CONTROLS
            &&((kind!=5&&kind!=25)||!burstControls(s)) // Existing shared cooldown/reentry handlers.
#endif
#ifdef PORTABLE_COORDINATE_SQUAD_MODE_STATE
            &&kind!=29 // Existing shared revival handler; mode flags survive on_down/on_revive.
#endif
        )return false; // Shared weapon/heal/reduce dispatch.
