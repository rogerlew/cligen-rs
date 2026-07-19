# Review

The revision closes the ambiguity that caused A10M5R8R1 to require all rows on
a normalized Gregorian axis to be observed. The normative vocabulary now keeps
three surfaces separate: official Daymet source observations, the normalized
Gregorian axis plus availability mask, and complete Gregorian model output.

The canonical profile independently reconstructs 10,958 fit-period calendar
rows, 10,950 observed rows, and the eight absent leap-year December 31 source
dates. Its eight-year example reconstructs 2,922 calendar rows and 2,920
observed rows with an exclusive end boundary. It also pins February 29 as an
observed official-Daymet source day.

Revision 2 does not change the A10M1 corpus schema or bytes, A10M5R8 objective
or disposition, or historical A5 `noleap_365_v1` behavior. The completed R1
evidence receives a transparent terminology correction rather than a changed
outcome. The historical A10M5R8 synthetic missing-mask test remains evidence of
generic mask handling; future Daymet transform fixtures must use the canonical
December 31 profile and pass before resource reservation.

No production or faithful generator code changed. The unrelated existing
worktree package and roadmap edits were not included in this package.
