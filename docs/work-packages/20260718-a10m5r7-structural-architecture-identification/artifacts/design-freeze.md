# A10M5R7 prospective design freeze

The accepted P1/P2 terminal remains final for its hypothesis. This package
does not reinterpret that result. It tests the narrower structural observation
that training used previous observed normalized weather while accepted
generation supplied zero in all seven weather channels and never fed sampled
weather back into the recurrence.

Three inference modes use the same seed-147031 P1 weights:

1. `accepted_open_loop`: the accepted calendar/site-only generation path;
2. `observation_conditioned`: one-step sampled output using the preceding
   available observed day, diagnostic-only; and
3. `generated_feedback`: sampled weather is normalized and becomes the next
   day's seven endogenous inputs.

The diagnosis uses 30-year streams, eight members, the exact six temporal
sites, the existing metric scales, and five predeclared groups. Grouped
arithmetic is explanatory and cannot replace the unchanged temporal gate.

Generated feedback advances only when its family-balanced error is at least
15% below accepted open-loop, no group is more than 25% worse, and every
stream is finite and supported. If it advances, the exact three accepted P1
checkpoints generate the full 100-year, 24-stream-per-site matrix and face the
unchanged temporal score.

If generated feedback does not advance, a deterministic attribution tree
selects only the simplest supported next hypothesis: rollout-trained closure
when observation conditioning improves at least 25%; climate-normal
conditioning when monthly-climatology residual share is at least 50%; an
explicit occurrence state when occurrence/spell share is at least 30%; a slow
stochastic state when annual-dependence share is at least 30%; otherwise a
mixed hold. Amount family and capacity remain fixed throughout.

No component residual, candidate output, comparator stream, or protected role
was read to author this freeze. One 60-minute primary L40 allocation plus one
five-minute exact-node cleanup reserve is the complete package budget.
