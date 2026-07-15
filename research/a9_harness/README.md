# A9 research harness

This directory is external, synthetic-only research tooling for A9b. It is not
part of the `cligen` crate, exposes no accepted generation profile or station
model, and may not read observed A9 fit, development, gate-calibration, or
confirmation targets.

The reference environment is Python 3.12 with the exact direct dependencies in
`requirements.txt`. Run from the repository root:

```text
python3 -m research.a9_harness validate ARTIFACT --schema SCHEMA --kind KIND
python3 -m research.a9_harness fit --role-manifest ROLES --role-schema ROLE_SCHEMA --fit-schema FIT_SCHEMA --candidate-plugin ID --exposures SYNTHETIC_JSON --output FIT
python3 -m research.a9_harness evaluate --role-manifest ROLES --role-schema SCHEMA --role development --input SYNTHETIC_JSON --output RESULT
python3 -m research.a9_harness optimize --role-manifest ROLES --role-schema SCHEMA --proposals SYNTHETIC_JSON --log-directory LOG
python3 -m research.a9_harness calibrate-gates --role-manifest ROLES --role-schema SCHEMA --replicates SYNTHETIC_JSON --output THRESHOLDS
python3 -m research.a9_harness confirm --sealed-freeze MANIFEST --role-schema SCHEMA --freeze-sha256 HASH --actor ACTOR --access-log-directory LOG
python3 -m research.a9_harness verify-log LOG
python3 -m research.a9_harness run-fixtures --output-directory OUTPUT
```

`fit`, `evaluate`, `optimize`, and `calibrate-gates` require an explicit
`synthetic_only: true` input and apply the path/hash/logical-record firewall.
`confirm` is the only command that can atomically change a complete synthetic
manifest from `sealed` to `consumed`. A9c must separately authorize and bind
any observed development objects.

The simulation random field is Philox4x32-10. Its input is SHA-256 of the
literal domain `cligen-rs/a9-crn/v1\0` followed, in order, by campaign, site,
burn, component, ISO Gregorian date, and variate-slot UTF-8 fields. Each field
has a four-byte unsigned big-endian length. SHA bytes 0--7 become two
little-endian key words and bytes 8--23 become four little-endian counter
words. Golden vectors are package artifacts.
