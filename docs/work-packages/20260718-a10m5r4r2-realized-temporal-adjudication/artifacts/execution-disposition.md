# A10M5R4R2 execution disposition

Terminal: `HOLD-A10-MODEL-RECONSTRUCTION-IDENTITY`

Only the prospectively first role was submitted. Slurm job 1013989 ran on
node03 for 00:02:43 and settled `FAILED`, exit `1:0`. No retry or second role
was submitted.

Training reproduced the accepted P1 seed-147031 state exactly:

| Identity | Accepted | Reconstructed | Result |
|---|---:|---:|---|
| checkpoint payload bytes | 1,074,300 | 1,074,300 | exact |
| checkpoint payload SHA-256 | `fd54c491180c58dc21e25b8f2324604239acb5a4e3e439995fbb2e92a0d92752` | same | exact |
| model-record SHA-256 | `0fcacf2c65db1a409a1d9a349b0880a8315bbf79b0b27942e8cbefa41fed2229` | same | exact |
| validation primary NLL | 2.666571855545044 | 2.666571855545044 | exact |
| TorchScript archive bytes | 364,196 | 364,196 | exact |
| TorchScript archive SHA-256 | `549f71b504add381db842c05cd4c172caa559b8f292417dfab5d2d06271c56ef` | `996ac7a5feddc9f05cca570a3b0c4f2a8165aa7175eccf6a844d07886f0955d2` | mismatch |

The generated-stream program stopped on the frozen archive-hash gate. That is
a valid R2 scientific hold: the model reconstruction succeeded, while the
chosen identity of its newly serialized container did not.

The original source-commit wrapper also serialized a literal newline into a
Python string while attempting to create a failure receipt, causing a second,
operational syntax error. Toolkit `observe` therefore returned
`EVIDENCE_INCOMPLETE` and did not mutate the attempt from `SUBMITTED`. This
does not change the scientific failure above. It does require a fresh package
identity, because R2 had already accessed generated output and cannot amend its
frozen contract retrospectively.

The canonical supervisor wrote `{"application_exit":1}` and returned exit 1.
Its contract returns 75 if marker validation or exact job-local removal fails,
so the observed exit proves job-local cleanup. After private read-only
retrieval, the committed marker-bound durable cleaner authenticated plan
`5076f3f6e838621488c04a919218638f1badf3860d694670ccc3be3b237e5b61`
and source commit `f704820d8e6f798b5fed4dff21e3030918c558b2`, returned
`REMOTE_ABSENT`, and a separate exact-path probe returned
`R2_REMOTE_ABSENT`.

Resource use: 163 elapsed GPU-seconds; 3 rounded GPU-minutes charged against
the 185-minute authority ceiling. Confirmation and development-selection
roles remained sealed.
