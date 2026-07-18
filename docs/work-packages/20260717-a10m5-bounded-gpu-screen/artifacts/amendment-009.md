# Operational amendment 009 — reserved-token log normalization

## Trigger

With finite scientific JSON accepted and collection restartable, the next R7
projection attempt stopped on the Slurm error logs. `screen-job.sh` had already
redacted traceback paths to `<REMOTE_RUN_ROOT>` and `<JOB_LOCAL>`. Projection
revision 3 intentionally rejects reserved angle-bracket tokens in raw evidence
before replacement, because otherwise a producer could spoof sanitizer output.

## Prospective source correction

Future job wrappers render local diagnostic redaction as `[REMOTE_RUN_ROOT]`
and `[JOB_LOCAL]`. Square-bracket labels are visibly nonliteral but do not
occupy the sanitizer's authenticated replacement namespace. No scientific
output, gate receipt, checkpoint, benchmark, or scheduler accounting changes.

## R7 legacy normalization

The first and second downloaded R7 quarantines preserve the original Slurm
logs and their archive-bound hashes in restricted private state. Before the
next independent download, only the two exact legacy strings in the twelve
allowlisted `.err` diagnostics are changed from angle to square brackets on
the durable remote root. Scientific JSON and stdout logs are untouched.

The package completion artifacts record before/after SHA-256 values for every
affected file and the exact replacement count. The toolkit's new raw-collected
record binds the normalized download, while the retained failed quarantines
preserve the original bytes. This bounded legacy bridge does not weaken the
projector's reserved-token rejection.

After successful collection, authenticated cleanup, and close, the toolkit
purged restricted private run state as designed. `log-normalization.md` retains
the original and collected hashes and exact replacement count.
