# Disposition

Terminal: `A10M5R15R2R1-SUCCESSOR-CONTROL-IDENTITY-READY`

Run `a10m5r15r2r1-successor-control-identity-calibration-r3` completed on
Slurm job 1060850 on node03 in 1,175 seconds, billed as 20 L40-minutes. All
six P1/P2 by seed control rows passed the frozen static identities, calendar,
corpus, setup, gradient-free validation, and candidate/protected-role sealing
gates. The run produced no R15 candidate output.

The six successor-corpus dynamic identities are recorded in
`artifacts/successor-control-identity.json`; the collected summary is
`artifacts/successor-control-summary.json`. Collection record
`c9521e4422e629d5faf0079370fdd59f097c7f4b2b101138605e1a0360c362af`
contains all 13 required files. Cleanup record
`fe6e81584ff8e3248e7bc531f7b1967ad59f7ef35004b498420d96b8b05f10f5`
authenticates both remote and job-local absence, and terminal record
`847a891e4c38c7c9e668091bcbb60445dfda52e7f7c02456951ae6ab91f20981`
closes the single-attempt run. Recovery reserve event
`3b48574d94cfbaf3b929a6e721d43d6d3971b2bd1601518dce0f440a8824068f`
released the unused five minutes.

The original R2 control mismatch is therefore resolved without weakening
exact reconstruction. A fresh execution package may pin these six identities
prospectively and must reproduce them before any candidate role is released.
The campaign has realized 38 L40-minutes to this point (8 failed R2, 9
canceled calibration, 1 corrective cleanup, and 20 successful calibration).
With the separately authorized 515-minute study still outstanding, the
bounded campaign maximum is 553, below the operator-authorized ceiling of 597.
