# Execution hold

Terminal: `HOLD-A10M5R8R2-CALENDAR-END-EXCLUSION`

Job `1014024` authenticated the corrected source and passed the masked
synthetic climate-statistics test plus exact accepted-control reconstruction.
Calendar attachment then included the target-end date in `month_index`,
`year_index`, and `valid_index` while the target tensor correctly treated that
boundary as exclusive. The fail-closed length/set check rejected the resulting
2,923-versus-2,922 mismatch before treatment training.

R3 changes both label/mask slices from `end + 1` to exclusive `end` and adds a
synthetic end-boundary test. The scientific contract is unchanged.

Resource/operational record:

- Slurm job: `1014024`, node03, exit 1, 223 seconds
- actual: 223 GPU-seconds / four charged GPU-minutes
- recovery: not invoked; reserve released after authenticated cleanup
- collection: 20,480 bytes, SHA-256
  `72793a7b7e908b89b71588dc0152b26f6e15dec90c53c726fb8d7ab7e92d6c13`
- job-local cleanup: verified absent
- durable run root: verified absent
- protected roles opened: none
