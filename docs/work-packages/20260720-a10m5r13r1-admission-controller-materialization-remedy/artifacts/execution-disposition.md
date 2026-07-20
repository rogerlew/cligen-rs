# Execution disposition

Date: 2026-07-20
Terminal: `HOLD-A10M5R13-NO-TEMPORALLY-ELIGIBLE-CANDIDATE`

R13R1 fixed the admission-controller lineage failure and executed the exact
R13 science matrix. The control and both candidates passed all submission,
calendar, environment, science, physical-support, stream-matrix, protected-
role, and job-local-cleanup gates. The two candidate jobs ran concurrently
after the serialized setup boundary. All 51 allowlisted evidence members were
collected and sanitized under projection v5.

The R13R1 replay command then failed closed before selector execution because
it compared the raw semantic plan to the deliberately reduced toolkit plan
receipt. R13R2 repaired only that authentication boundary: it reconstructed
the toolkit semantic plan from the frozen raw plan, authenticated its digest
against plan ID
`2dfc598e9767f4492afb99449fd3de1c2d320624de4213d3fcf993881f0ee91b`,
and replayed the unchanged selector twice. The 17,234-byte passes and final
result were byte-identical at SHA-256
`2213ce79ef3cf9bf2a91562983824307c7fbd7cc26f85159b24cbbf176079cbb`.
Solar and confirmation remained sealed.

Neither continuous architecture was temporally eligible against the inherited
1.25 bootstrap-upper and 1.5 maximum regime-ratio limits:

| Candidate | Bootstrap upper | Maximum ratio | Eligible |
| --- | ---: | ---: | --- |
| Flexible continuous hierarchy | 2.48191 | 3.60959 | no |
| Shared slow climate state | 2.48858 | 3.63631 | no |

The flexible hierarchy was lower-error with bootstrap probability 0.865, but
its median relative advantage was only 0.175%. Constraining the slow process
to one shared climate scalar therefore did not buy meaningful accuracy. The
continuous state design itself remains sound: daily OU states cross month and
year boundaries without resets, while calendar periods are only masked
aggregation domains for the loss and selector. This result does not identify
monthly quantization as the failure mechanism.

The authenticated cleanup receipt proves the remote root and job-local state
absent. The toolkit run closed normally. R13R1 consumed 185 GPU-minutes, the
unused five-minute recovery reservation was released, and no retry occurred.

The selector-aligned annual objective did what it targeted: relative to R12,
the flexible hierarchy reduced actual-series annual cross-field error from
4.831 to 1.391 (71.2%). Its eligibility ratios improved by only about 0.6%,
however, because 168 of the 188 selector metrics are monthly. Monthly
temperature means plus precipitation location/quantiles contribute 74.4% of
the remaining composite error. The centered residual cannot correct ensemble
climatological means, and its continuous state reaches location heads only,
not the precipitation or temperature scale heads.

The smallest scientific continuation is therefore a matched 2x2 portfolio
that preserves the flexible continuous hierarchy and crosses (a) a small,
smooth, uncentered day-of-year/geography climatology correction with (b)
centered continuous OU modulation of the distribution scale heads. This
separates mean calibration, stochastic dispersion, and their interaction
without adding month/year state cells. The shared rank-one restriction should
not advance, and solar remains sealed.
