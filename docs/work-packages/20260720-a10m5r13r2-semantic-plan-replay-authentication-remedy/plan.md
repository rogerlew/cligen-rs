# Execution plan

1. Publish the R13R2 replay script, predecessor pin, and R13R1 input pin on
   `main`; require working tree bytes of all three files to equal bytes at
   current `HEAD`, require `HEAD == origin/main`, and prove the frozen R13R1
   input source commit is an ancestor of that remedy head.
2. Load the R13R1 toolkit publication plan receipt separately from its raw
   frozen semantic-plan input. Authenticate the receipt's record hash and
   exact R13R1 package, run, and source identities.
3. Reconstruct toolkit semantic plan bytes as raw plan minus optional
   `created_at`, plus the receipt's `cluster_profile_sha256` and
   `provider_stack`. Require canonical SHA-256 identity with the receipt's
   `plan_id`.
4. Require raw plan, receipt, collection, and asset manifest to match the
   committed input pin. Require the asset manifest additionally to match its
   exact entry in the authenticated semantic plan.
5. Authenticate the R13R1 collection receipt against that plan identity and
   against source commit `927c6147f879ed3a9a56ff1218ffaa3953bef93c`.
   Use only the authenticated semantic plan's evidence allowlist, and require
   unique/disjoint `present` and `absent` rosters whose union is that allowlist.
6. Recheck comparator, corpus, data-root, selector assets, every collected
   file, required candidate streams, inherited PRISM provenance, and sealed
   protected roles.
7. Execute two isolated selector passes. Require byte identity and one of the
   unchanged R13 terminals, then write the R13R2 replay identity.
8. Permit R13R1 cleanup only after the authenticated replay identity exists.

No HPC or remote allocation action is authorized or required by this package.
