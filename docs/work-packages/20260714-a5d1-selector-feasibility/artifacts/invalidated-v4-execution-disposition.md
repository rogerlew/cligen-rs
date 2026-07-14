# A5d1 v4 Execution Disposition

Status: `INVALIDATED-BEFORE-TERMINAL-CLOSURE`

The independent accuracy review found that v4 reset predecessor state at each
complete-year block. Within-year transitions were attributed to the
destination month, but January 1 cross-block transitions were absent from the
fitted monthly replay. The accepted quality implementation treats the daily
series continuously and attributes those pairs to January.

A diagnostic replay left the observed full path count at 0/306, but that does
not rescue the experiment: the registered optimizers had not minimized the
complete path constraint vector. The v4 decision, aggregate results, report,
certificates, paths, physical audit, and detailed archive are retained under
`invalidated-v4-*` names and are excluded from terminal evidence.

V5 prospectively assigns within-block transition constraints to unordered
stationary weights and requires each realized finite path to add its actual
January 1 predecessor pairs to the fitted January transition replay. The
separate directional boundary/spell vector remains in force.
