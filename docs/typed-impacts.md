# Typed impact boundary

`impact_specs.py` defines immutable actor handles (kind, identity, spawn generation),
attack family, outcome, damage and hit credit. Damage and credit are independent.
Zero damage is not enough to decide whether an impact counts. Attack identity zero
means unspecified; the executor must not invent grouping from ammunition use.

CPU body/part landings and GPU body/part landings enter this boundary before
lifesteal and damage accumulation, preserving their existing synchronous order.
Queued skill packets retain their family through deferred landing and queue moves.
Normal/core/pellet/charge weapon packets remain weapon-origin impacts even when a
weapon mode changes their damage formula. Periodic damage is explicitly DoT.

CPU lifecycle handlers register an `impact` callback in the sealed ordered catalog.
Event frames hold immutable target context, restore it after nested delivery and
exceptions, and clear it for resource/reload/healing events. No global last target
is used. Phase callback lists are prepared once when sealing the catalog; an event
does not scan every lifecycle family. Traces are opt-in; ordinary calculations
do not accumulate diagnostic impact summaries.

GPU ABI v53 uses the same generated enums and packet layout. Supported static body
and live parts use generation 1; the CPU bridge reads part-pattern spawn generations.
Query 126 exposes cumulative diagnostics; op 8 is
an authored transport stimulus and does not manufacture battle damage. Diagnostic
transport for projectile/shield/add identities does not establish world support.

Remaining before target counters can be accepted:

- Bind state to carrier UID/slot generation, refresh epoch and target generation.
- Define participating impact families, pellet/component credit and blocked-hit
  policy from game evidence; ammunition/non-core events are unsuitable substitutes.
- Latch completion before nested callbacks and retire only the same epoch afterward.
- Combine threshold and target death completion exactly once.
- Specify refresh reset/preserve behavior explicitly and snapshot cap-entry state
  where an overflow effect requires the resource to have already been full.

Current migration tests cover typed wire quantities and independent CPU/GPU squads,
including per-frame body/part families, shotgun pellets, deferred skill landings,
DoT, final pending landings, lifesteal and total/member/burst/health regression.
These checks establish transport behavior, not all-character or in-game accuracy.
