# A10M5R1 memory attribution

## Finding

The A10M5 CPU-export memory failure was a `ru_maxrss` lineage artifact. It did
not measure the fresh export address space.

A10M5 trained in a large Python process and then called `subprocess.run` to
exec a CPU worker. On Lemhi, the child's `getrusage(RUSAGE_SELF).ru_maxrss`
retains the fork parent's historical high-water mark across exec. The child
therefore printed the trainer's roughly 3.1 GiB peak even though exec had
replaced its address space.

The direct login-node control allocated and touched 512 MiB in a parent, then
exec'd the system Python through `subprocess`. Results:

- parent `ru_maxrss`: 535,080 KiB;
- child `ru_maxrss`: 530,000 KiB;
- child `/proc/self/status` `VmHWM`: 8,876 KiB;
- child `/proc/self/status` `VmRSS`: 8,876 KiB.

That 59.7x disagreement proves the counter is unsuitable for a fresh-child
memory gate when the launcher already held substantial memory.

## Fresh-process attribution

R1 launched every variant directly from a small shell under
`/usr/bin/time -v`. Its smallest-A10M5 architecture used 34,351 parameters,
36,525 deterministic synthetic days, 365-day chunks, exact hidden-state carry,
one CPU, and one framework/BLAS thread.

| Phase or variant | Resident memory |
|---|---:|
| Python start | 19--20 MB |
| PyTorch import | 498--505 MB |
| TorchScript load | 507--510 MB |
| First/steady inference | 521--525 MB |
| Eager `/usr/bin/time -v` maximum | 630,792,192 bytes |
| TorchScript `/usr/bin/time -v` maximum | 634,572,800 bytes |
| Lowest tested TorchScript maximum | 628,273,152 bytes |

At steady TorchScript inference, categorized RSS was approximately 156 MB
anonymous, 133 MB NVIDIA/CUDA libraries, 110 MB heap, 94 MB Torch mappings,
29 MB other file mappings, 5.5 MB NumPy, and 80 KiB stack. Live input/model
tensors plus retained output were about 4.2 MB. Importing the CUDA-enabled
PyTorch closure dominates; the model and recurrent workspace do not.

Eager, default TorchScript, unoptimized TorchScript, MKLDNN-off TorchScript,
and frozen TorchScript all produced the exact reference output. Backend
toggles changed peak memory by less than 7 MB and are not remedies worth
canonizing.

## Candidate-fit acceptance

R4 regenerated `N0-l32-w128-d2-lognormal` at seed 147031. Every one of its
twelve candidate stream hashes exactly matched A10M5. The export was 152,204
bytes, cold load was 1.206 seconds, and all paired runtime ratios passed with
a maximum of 3.8199. Benchmark dispersion passed.

The acceptance child reapplied deterministic algorithms but still printed
3,321,282,560 bytes through `ru_maxrss`, confirming that framework settings do
not repair inherited accounting. That value is the contaminated control, not
the deployment RSS.

## Canonical recipe

1. Finish training and persist the immutable export and its identity.
2. Exit the high-RSS training process.
3. From a small shell/supervisor process, directly exec the one-core CPU
   worker with GPU hidden and all thread pools fixed to one.
4. Measure the worker's own `VmHWM` from `/proc/self/status` and corroborate it
   with external `/usr/bin/time -v` whose launcher did not hold training data.
5. Retain exact output hashes, cold load, export bytes, and runtime evidence.

Do not use `resource.getrusage(RUSAGE_SELF).ru_maxrss` inside an exec'd child
of a high-RSS parent as a deployment-memory gate.
