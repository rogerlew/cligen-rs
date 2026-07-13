# A5a Adversarial Review and Disposition

Review: delegated read-only code, schema, metric-contract, corpus, and evidence
audits plus an independent full baseline-verifier replay  
Final verdict: **ACCEPT WITH P3 OBSERVATIONS**  
Date: 2026-07-13

## Scope and result

The review covered the metrics-v3 implementation and public quality-report
DTO, the observed-target corpus and rebuild chain, the executable A5 climate
gate and bootstrap contracts, the downstream-WEPP response boundary, and the
complete 544-run baseline evidence chain. It also checked that the package
does not change a generation profile, station model/schema, faithful
generator path, or rendered `.cli` behavior.

No P1 finding was identified. Every P2 found during review was remediated and
retested before the final evidence run. No P1 or P2 remains open.

## P1/P2 disposition

| Finding | Disposition |
|---|---|
| **A5A-P2-001 — public quality-report validation did not initially enforce all v3 relationships.** Structurally valid mutable DTOs could retain inconsistent dimensions, counts, definedness, or identities. | Remediated. The public parser and serializer now run the closed combination schema and explicit relational validation. Exact monthly/matrix dimensions, counts, complete-period identities, correlations, low-frequency definedness, tails, descriptors, winter proxies, process counters, provenance, duplicate keys, unknown fields, and non-finite values have positive and mutation coverage. |
| **A5A-P2-002 — broad prose did not define an executable climate-gate denominator.** The initial registration named metric families but not every scalar cell, count requirement, target projection, exclusion, or aggregation membership. It also risked mixing signed temperature locations with scale metrics and diluting the three-cell low-frequency outcome. | Remediated prospectively before candidate output. The hash-pinned version-1 metric manifest expands 24 templates to 1,211 exact bindings, fixes the baseline-eligible common-cell set, count sufficiency, paths, projections, distances, exclusions, and equal-weight hierarchy, normalizes Group-A temperature location by matched target SD, and adds the explicit 0.90 low-frequency-family subguard. Its semantic verifier rejects 51 mutations/parser vectors. |
| **A5A-P2-003 — observed-target uncertainty was not executable.** The block unit, PRNG, bounded draw, draw order, year relabeling, target/generated crossing, invalid-cell handling, reporting levels, and decision role were under-specified. | Remediated prospectively. The reference and golden vector fix SHA-256 seed extraction, `splitmix64-v1`, rejection-sampled bounds, four circular five-year blocks, truncation to 16 complete aligned years, 2,000 replicates, nearest-rank endpoints, sequence seams, all-eight-generated-report crossing, and report-only application to Gates 1, 4, and 6. Twenty-one mutation/parser vectors and an independent cross-language reconstruction pass. |
| **A5A-P2-004 — the WEPP response surface was initially structural rather than operational.** Cross-family semantics, strict external-record intake, and independent schema/protocol/validator identity were not all enforceable. | Remediated. Each response record binds independent schema, protocol, and semantic-validator IDs and hashes. The external validator strict-parses records and enforces horizon counts, complete family/statistic membership, coherent units/source semantics, nonnegative magnitudes, summary ordering, unique output identities, and cross-array output references. Four positive and 28 structural/semantic/parser negatives pass. A5a still correctly holds WEPP execution for a pinned A5b/A5c campaign. |
| **A5A-P2-005 — baseline evidence identity was initially vulnerable to mutable inputs and incomplete build/run binding.** The binary, station files, evaluation contracts, Cargo configuration/environment, and effective runspec semantics were not one closed reproducibility chain. | Remediated. The runner uses immutable binary and station snapshots, pre/post static-identity checks, an 85-file implementation closure, exact evaluation-contract hashes, a pinned evidence target, safe Cargo/Rust environment policy, complete Cargo-config search closure, tool-proxy/Cargo-home linkage, canonical archive construction, and exact report/provenance/runspec verification. |
| **A5A-P2-006 — Python “strict JSON” loaders rejected `NaN`/`Infinity` tokens but initially admitted a finite JSON lexeme such as `1e400` as binary64 infinity.** | Remediated across the normative metric, bootstrap, WEPP, runner, and evidence-verifier loaders with a finite `parse_float` hook and positive/negative overflow vectors. Duplicate keys and non-standard non-finite constants remain rejected. |
| **A5A-P2-007 — the first development baseline used the lower center order statistic for eight burns.** That was inconsistent with the subsequently fixed conventional-median definition. | Rejected and prospectively amended on 2026-07-12. The preregistration declares that development baseline stale and prohibits reuse of any report, summary, cell set, or pass claim. The final 544-run matrix was regenerated under the conventional median and the complete revision-2 contract. |
| **A5A-P2-008 — the first replacement attempt exposed an incomplete verifier expectation for `effective_runspec.output.command_echo`.** The generated off-QC provenance correctly included ` --qc-filter off`, while the verifier omitted it. | The independent verifier rejected the attempt before publication/cleanup. Its expectation and compact-JSON golden were corrected, its changed hash became a static evidence input, the rejected evidence was discarded, and a full empty-target regeneration was required. |
| **A5A-P2-009 — the next replacement attempt exposed a second incomplete command-echo expectation.** Nonzero burns correctly include the `-r<burn>` prefix, which the verifier had omitted. | The verifier again rejected the attempt. The exact four-way burn-zero/nonzero and faithful/off normalization was checked against the rejected archive, the compact-JSON golden was updated, and no prior report was reused. A third full empty-target regeneration bound the final verifier and passed both the runner-owned and independent full verifier replays. |

The last two findings were defects in the independent verifier's expected
normalization, not silent defects in generated provenance. Their rejection is
evidence that the publication gate failed closed. Because the verifier hash is
part of the static evidence identity, correction required full regeneration;
the final archive does not inherit reports from either rejected attempt.

## P3 disposition

| Observation | Disposition |
|---|---|
| **A5A-P3-001 — the bootstrap golden's crossed toy estimand is a mean and therefore order-invariant.** The sampled-index/vector hashes and normative prose pin draw order and relabeling, but that one estimand would not itself expose an analyzer that sorted sampled years before recomputing lag, periodogram, rolling, or spell metrics. | Accepted as nonblocking conformance-test hardening. A5b should add an order-sensitive toy statistic before its analyzer reads candidate output. The version-1 order is already unambiguous and every current golden hash passes, so this does not change an A5a result. |
| **A5A-P3-002 — the held-out bootstrap bound is 16, which divides `2^64`.** For this bound, modulo and rejection sampling produce the same accepted indices, so the golden cannot behaviorally distinguish those implementations even though the reference and prose require rejection sampling. | Accepted as nonblocking general-contract hardening. A5b should add an injected-draw or non-divisor bounded-integer vector. This has no version-1 result impact for the fixed 16-year target. |

## Independent coverage

| Surface | Review evidence |
|---|---|
| Rust implementation and compatibility | The package gate owner ran format, Clippy, 181 passing tests with 10 explicit ignores, LLVM coverage, CRAP over 670 production functions with none above 30, and crate packaging. All twelve faithful golden `.cli` trajectories remained byte-identical. Review of the diff found quality instrumentation only, with no generator/profile/station behavior change. |
| Public quality schemas | Envelope-1/metrics-1 and envelope-2/metrics-2 identities remain unchanged. The envelope-2/metrics-3 public and runtime schemas are byte-identical, validate offline under Draft 2020-12, and are packaged without source-tree or network resolution. |
| Observed corpus | All 17 Daymet and 8 GHCN source objects hash to the source manifest; 102 station/source/period coverage rows are explicit. The source manifest, target schema, target corpus, coverage ledger, and final manifest rebuild byte-identically. The independent target corpus remains schema version 1 with content SHA-256 `4d0987bb172aef76f3f3a48704bf9df78a375d9d562a145f435800042b5b5660`; source notices remain public and license-safe. |
| Metric manifest | The semantic verifier passed 24 templates, 1,211 bindings, Gate counts 422/422/120/205/24/18, and 51 negative vectors. Independent expansion resolved all 789 generated paths and 14,341 available target paths with no error; dimensional consistency and the frozen common-cell set were checked adversarially. |
| Bootstrap | The reference passed 2,000 replicates, 8,000 bounded draws, and 21 negative vectors. An independent implementation reproduced the seed, start indices, sampled vectors, target rationals, crossed eight-replicate median-distance rationals, and nearest-rank endpoints. |
| WEPP boundary | The schema, protocol, and semantic validator hashes agree in SPEC-A5 and in the baseline evaluation contract. Four positive and 28 negative vectors pass, including duplicate-key and binary64-overflow intake. No mutable sibling executable was treated as evidence. |
| Baseline matrix and archive | A second full invocation of `verify-baseline-evidence.py` independently passed the strict manifest/analysis schemas, exact 544-run matrix, every report/provenance/parameter hash, report-to-provenance-to-runspec semantics, and exact analysis recomputation. A separate sequential scan verified 544 quality reports, 544 provenance documents, and 17 station files: 1,105 unique lexicographically ordered regular USTAR members with canonical gzip/header, ownership, mode, and timestamp metadata. The temporary target directory is empty. |

## Reviewed identities

| Artifact | SHA-256 |
|---|---|
| SPEC-A5-EVALUATION revision 2 | `e774496f4f4bcc3de184b03bed2ce15e774bcdfb6090d92eea9f8c24d32944da` |
| A5b preregistration | `ee2f29dfc6e1843affe4734260347abb54336d7a3ce74c652b230a2264b95021` |
| Climate metric manifest / schema / verifier | `37d2e36fe84a7fafbc2dafdea553a5702fe94677de23a6ba45ac4a4946572d95` / `f17b6a3896df1226b60a6e1f181089568cab918488d6564caa4ec12baf83be2c` / `ae1ef7f06b4afef94910af656f2077ee2029698a42e9223f3a8099a61dac1ac0` |
| Observed bootstrap reference / golden | `d154773bb8bd5265e8423360b69fc6acb0cec8cc64280cdee5c1ac705df8d649` / `d38a730371a847e78fb9563821ea7efffa24f364787f902f555634a32f8c2ec2` |
| WEPP response schema / protocol / verifier | `7d006023684f2079ce09e5ab1af21e1154a417eb4295ebf1a02c40d7f7a2e70d` / `9cd770d18c04dfde877c91e03304697b107d117bf2e52cc94f1f83e3d99c5800` / `05e7a085f146e264c3b34e3f7c04f498f0f4d3dd0c9b0cd17a0f8176221b683b` |
| Final baseline runner / verifier | `11098df165e3df880f06f4a84fb6c7b4ecf1ca2b361cd5310db38f356d8f2642` / `9a3fbdb4d35ec693db6bad916b1cb941c3c3ebec93340a05899f103f269b32f1` |
| Final release binary | `13e85f851748047e83a39173d7722941606e73127d3ff52c968cdfd3514b20d6` |
| Baseline manifest | `e6e12a08b7d552edd45481b929271af87530d2821b9b51d5cec066dc76867cbc` |
| Baseline analysis | `7892cc2d8931623154c33f854db1170e46749e741d08a3843205131329934733` |
| Baseline evidence archive (55,928,355 bytes) | `2fca565b8c3f83632e73050984dce0c619352ac4bb76deed86fb3928f8de15fe` |

## Conclusion

A5a satisfies its review exit criterion: no P1/P2 remains, the metric and
observed-target authority is executable and independently versioned, the
final baseline is bound to the reviewed implementation and evaluation
contracts, and the complete evidence archive validates independently. The two
P3 observations are explicit A5b conformance-test improvements; neither
changes the fixed A5a evidence or authorizes a candidate promotion.
