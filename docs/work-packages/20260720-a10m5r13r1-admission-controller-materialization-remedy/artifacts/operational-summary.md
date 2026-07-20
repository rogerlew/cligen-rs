# Operational summary

## Run identity

- source: `927c6147f879ed3a9a56ff1218ffaa3953bef93c`
- run: `a10m5r13r1-admission-controller-materialization-remedy-r0`
- plan: `2dfc598e9767f4492afb99449fd3de1c2d320624de4213d3fcf993881f0ee91b`
- authority ceiling: 515 GPU-minutes
- pre-close private-state SHA-256:
  `fdfc95d0b815171bcdf37f229ce5728a531b407cd20793337f8789b3ba3db906`
- pre-close ledger SHA-256:
  `7129f5b554864239d60da77e2c596f876091546f2ada5b1539315b32e294e941`
- final ledger SHA-256:
  `7eb3fb832e87756b96b9be678fd63b6235bc2fb413c6fab25c657d91aceab805`

## Resource reconciliation

| Role | Job | Requested | Charged | State |
| --- | ---: | ---: | ---: | --- |
| Control materialization | 1016150 | 30 | 20 | settled |
| Flexible continuous hierarchy | 1016152 | 240 | 84 | settled |
| Shared slow climate state | 1016153 | 240 | 81 | settled |
| Toolkit recovery | none | 5 | 0 | released |

Total charged usage was 185 GPU-minutes. The authority retained 330 unused
GPU-minutes; no scientific retry or recovery job was submitted.

## Evidence and replay

The promoted collection archive was 96,727,040 bytes at SHA-256
`2ad8ea3400870ff0a226d2f4137b6fe43e38b2ac79538d42d99df3f23c9ccb73`.
Its receipt authenticated 51 present, zero absent, and 51 sanitized files.
R13R2 authenticated the exact semantic plan and produced byte-identical replay
passes. Replay identity SHA-256 was
`6edcaad3196369f984589ff1c06a50e114f7b50390d3ac30d49382da6e029965`;
its embedded canonical record digest was
`1f08ab7df52ba51709e16878cf23135e85f7dbdce7a5be75558562e7b326f810`.

Cleanup receipt record digest
`d4de26d813327793ba834037d0317ca4db7359e6aae12049bfa3b8d00094949d`
proves remote and job-local state absent. Terminal receipt record digest
`886657cb32a8185d7d97fa86d3e411e17fd2f0f1ab40b98398e8d68f89abda0b`
closes the run with three attempts and zero stopped roles.
