# A9c pre-ranking implementation corrections

Status: prospective with respect to all development rankings

No candidate development score, Pareto result, or selection output existed for
any correction below. Data roles, source bytes, null thresholds, objective
registry, configuration grid, resource limits, and selection rule did not
change.

| ID | Boundary | Observation | Correction | Outcome access |
|---|---|---|---|---|
| A9C-PRE-001 | source-manifest finalization | Python `false` spelling stopped only the final manifest write after all normalized objects and ledger rows existed | reconstruct the manifest from the already written hash-valid objects and append-only ledger; no source was reacquired | no candidate fit or development score |
| A9C-PRE-002 | candidate-blind null dry run | Daymet and USCRN compound-context feature blocks had different widths | use the registered five-field context layout with unavailable-source positions represented structurally in the bootstrap vector | no threshold or candidate fit existed |
| A9C-PRE-003 | renewal fit serialization | NumPy returned a boolean scalar for an exposure diagnostic | serialize the same diagnostic as a native JSON boolean | no development score existed |
| A9C-PRE-004 | latent fit construction | hard Viterbi state/month assignment produced an empty positive-amount cell although the soft HMM emission was identified | use the same-state annual stratum/global prior for an empty seasonal cell, consistent with the frozen hierarchical seasonal law; never borrow from development | no latent fit artifact or development score existed |
