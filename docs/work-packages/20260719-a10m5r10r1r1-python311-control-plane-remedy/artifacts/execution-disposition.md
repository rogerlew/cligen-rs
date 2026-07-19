# Execution disposition

Terminal: `HOLD-A10M5R10R1R1-COMPUTE-PYTHON311-ABSENT`

Run identity: `a10m5r10r1r1-python311-control-plane-remedy-r0`

Source commit: `9bdee723deeb2185045b3fcb1e1455ac10abdedc`

Authority revision: `b3176058b91b583abf905b4b939299c0218bf1d6fcb12cad737fb8b48a6a9f7a`

Plan: `07f702afb665d4bfab92012161bf95172dc6fd84dce674dd7db4d561b74d10c1`

The full 1,440-object calendar replay was byte-identical to the frozen receipt,
all assets staged and verified, and the login-host Python 3.11 identity passed.
Control admission record `31e5d91b…` passed all 16 gates. Job `1014053` then
failed on node03 with exit `127:0` after one elapsed second because
`/usr/bin/python3.11` does not exist on the compute image. Its exact stderr
shows failures in bootstrap diagnostics and the outer failure-evidence path.

No portable runtime, wheelhouse, corpus, control reconstruction, candidate
training, or selector opened. No candidate role was admitted or submitted.
The supervisor returned `application_exit: 127` after removing the exact
job-local root. Because the compute host could not run the registered Python
failure finalizer, no gate receipt existed; toolkit observation correctly held
at `EVIDENCE_INCOMPLETE`, and `stop-matrix` could not classify a still-
unvalidated attempt.

Ten authentic files were retained privately under a logical manifest with
SHA-256 `dd9aa0a22bcd87f7175601419f2cc35a8adacf900bc09297724ef6a00d20fce4`.
The exact durable root was removed with the unmodified toolkit `clean.sh` and
independently checked absent. This is an operational HOLD only and supports no
architecture comparison.
