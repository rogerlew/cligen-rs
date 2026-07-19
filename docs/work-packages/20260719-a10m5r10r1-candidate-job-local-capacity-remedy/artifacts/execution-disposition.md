# Execution disposition

Terminal: `HOLD-A10M5R10R1-PYTHON311-CONTROL-PLANE`

Run `a10m5r10r1-candidate-job-local-capacity-remedy-r0` used source commit
`6bde267235c9a3cddababe981cba5986e4fd8ca2`, authority revision
`227d28212a6823ba6b7ae3ecb5cccc9fa706e5d281ed78fdf7adf80db4dbffa9`,
and plan `58a51d5e89c26305b1dac1b6caeaba9a720bb4f72b1011ddc26fd0e6a1399356`.
Control job `1014042` passed all 15 submission-admission gates, then failed in
one second on node03 before setup began. Its stderr is exact and decisive:

    File ".../setup_diagnostics.py", line 4
      from __future__ import annotations
      ^
    SyntaxError: future feature annotations is not defined

The default `/usr/bin/python3` on the execution host is Python 3.6. The staged
`/usr/bin/python3.11` exists and successfully executed the same admission
checker, but the frozen wrapper and bootstrap sources invoked the unqualified
default for their pre-runtime diagnostics. No runtime archive, wheelhouse,
corpus, control reconstruction, candidate training, or selector opened.

After the single-attempt control role was exhausted, the toolkit offered no
post-submission abort or dependent-role waiver. The ten candidate roles were
therefore submitted in their frozen five pairs without admission receipts.
Jobs `1014043` through `1014052` each failed in one second before runtime
extraction, exactly as the wrapper's fail-closed gate requires. All eleven
jobs published `job_local_cleanup: true`; total charged accounting was 11
GPU-minutes.

The resulting matrix reached `MATRIX_SETTLED`, but toolkit collection stopped
at `EVIDENCE_INCOMPLETE`: the frozen evidence allowlist includes a PASS-only
`admissions/{role}.json` for every role, and correctly rejected candidate jobs
have no such records. Fabricating admissions would invalidate the evidence.
The real admission, result, Slurm, toolkit-state, and ledger records were
preserved in the package-private controller root. The exact staged root was
then removed by the toolkit's unmodified owner-marker and plan-hash validating
cleanup script and independently checked absent.

This is an operational HOLD only. It does not compare or eliminate any model
architecture. A10M5R10R1R1 must pin `/usr/bin/python3.11` for every
pre-runtime/control-plane invocation and rerun the complete coherent portfolio
under a new authority.
