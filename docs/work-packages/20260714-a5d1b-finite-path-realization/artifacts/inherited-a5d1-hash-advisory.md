# Inherited A5d1 report-hash advisory

Status: `DISPOSITIONED-NONCONTROLLING`

The A5d1 closure manifest correctly binds the current normalized
`feasibility-report.md` hash
`05e4e310523da3793c1c54471e79646b6025ae35dc96270a1bb90f4b62b75469`.
Its consolidated `review.md` retains the report's pre-normalization hash
`c2ec3dab82b091e41e942f937b1f3e9e7853129023aeb8a3ba5c408f19d05e03`.
The difference arose when Markdown hard-break whitespace was removed during
final staging and the closure manifest was refreshed.

A5d1b therefore treats the A5d1 machine contract, freeze, manifests, aggregate
results, machine decision, detailed evidence, and closure manifest as its
controlling inputs. The A5d1 narrative report remains contextual prose. This
advisory changes no A5d1 numerical result, terminal decision, or review verdict
and does not silently rewrite the accepted predecessor record.

