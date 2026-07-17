# Cleanup receipt

- Retrieved the sanitized D1 logs, matrices, compiler probes, run outputs, and
  manifests after job `1013558` completed.
- Verified every retrieved D1 result file against the remote result manifest;
  verified the prestage matrix separately.
- Verified the two scheduler output hashes before cleanup.
- Removed only the exact remote run directory `a10m2d1-3bc543f`.
- Post-cleanup checks reported `remote_run=absent` and zero queued user jobs.
- Core dumps were disabled in both scripts; no core file was retained.

The temporary local transfer directory is not part of the package evidence
and may be discarded after repository acceptance.
