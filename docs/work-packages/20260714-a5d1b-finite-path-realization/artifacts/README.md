# A5d1b artifacts

Status: `EXECUTED-HOLD-COUNT-SEARCH-BOUNDED`

This directory records the complete development-only A5d1b experiment. The
controlling v5 run produced one exact joint nested count witness of 17 required
stations; the all-station count gate failed, so ordered paths were not run.
No production or public interface changed and no confirmation object was
accessed.

The chronology is append-only:

- `pre-outcome-freeze-v1.json` is the root prospective freeze;
- amendments 001/002 and freezes v2/v3 repair optional solver-metadata
  serialization before count results;
- amendment 003 preserves and invalidates the flawed v3 run, then records the
  post-outcome incumbent-acceptance correction and freeze v4;
- amendment 004 preserves and invalidates all 17 v4 certificates after an
  aggregate-only missing import, then records controlling freeze v5;
- `history/v3-tools/` and `history/v4-tools/` retain the exact older tool bytes;
- `invalidated-v3-*` and `invalidated-v4-*` retain the exposed older evidence.

Controlling evidence comprises the inherited diagnostics, count result,
independent witness replay, ordered-stage skip, deterministic detailed archive,
aggregate result, machine decision, resource audit, and next-action
disposition. The report, consolidated review, gates, and closure manifest bind
the public account.
