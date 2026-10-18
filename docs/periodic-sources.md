# Population-dependent periodic sources

An owned periodic resource has a name, a generation, separately expiring slots,
and one reserved clock. New data can use this shared instant operation:

```json
{
  "type": "instant",
  "stat": "periodic_source_refresh",
  "target": "self",
  "periodic_source": {
    "name": "example source",
    "slots": [-1, 38, 32, 26],
    "base_interval": 8,
    "population_reduction_pct": 16
  },
  "trigger": {"timing": ["battle_start"], "condition": []}
}
```

`source_tick:example source` listens to this channel. Damage stat suffixes use
the same owned resource lookup as gauges and named stacks; a present resource
with zero population stays zero. Gauge lookup retains priority on a name
collision. Names are scoped by owner. The legacy `feather_refresh` descriptor
maps to the same resource executor; its `feather_tick` audience remains separate
from scoped generic source events. There are no character-name branches.

The interval for N slots is `base * (1 - reduction / 100 * (N - 1))`.
A refresh atomically replaces all slots, increments the generation, and reserves
the first attack after the full population interval. A slot is alive only when
its expiry is strictly greater than the current time; -1 means permanent.
Losing a slot does not move an already reserved attack. On a due tick the
current population is sampled; zero stops the clock, otherwise the notification
finishes synchronously before the next reservation is committed. A child refresh
creates a new generation which the parent's commit cannot overwrite.

The next reservation is based on the previous reserved time, preserving frame
quantization without cumulative drift. Each clock emits at most once per tick.
Clock traversal preserves owner insertion order, then channel insertion order;
new channels created inside a notification join the next clock phase. Sources
are owned resources independent of active buff instances, cleared on reset.
CPU and GPU run the clock phase after damage timers and before buff expiry.

Bounds are explicit: 64 channels per squad, 32 slots per channel, finite positive
intervals for every population, and finite authored lifetimes from zero to one
day or -1. Invalid or overflowing inputs fail instead of dropping resources.
GPU schema metadata is checked before execution. No CPU timer/shot history is
used as GPU input.

The legacy feather lifetime and interval parameters in the pinned source data
are community estimates. Both CPU and GPU results display that limitation.
CPU/GPU equality establishes implementation parity for the authored model;
it does not establish those constants as measured game behavior.

After verifying the common operation, GPU lookup uses a 5-by-256 byte direct
owner/name index instead of scanning up to 64 resources. Zero means absent;
positive values encode resource positions plus one. An expired source retains
its handle and can still report population zero. The first resource allocation
clears the table once; no-source squads neither initialize nor read it. This
adds 1,280 bytes per squad and does not change traversal or refresh generations.

The same compiled inputs and outputs are compared with the archived pre-index
implementation. In the authored64-channel workload (eight autonomous squads,
two seconds, warm context), the median GPU kernel time of three runs changed
from 544.493 to 500.777 ms. The ordinary API source squad workload changed from
5.624 to 5.486 seconds for eight uncached candidates in single comparison runs.
The latter difference is small and does not establish a universal gameplay gain.
See `research/source-index-pool-performance.json` and
`research/source-index-source-api-performance.json` for the measurement scope.
