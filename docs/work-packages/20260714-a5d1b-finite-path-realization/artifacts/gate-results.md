# A5d1b gate results

Status: `FINAL-PASS`
Date: 2026-07-14
Source commit: `08db78cb5365b2f961599421826a600dae1c765a`
Branch: `main`

## Scientific execution gates

- Contract/schema and root/amended freeze chain: **PASS**.
- Evidence lock and 17-station input identities: **PASS**.
- Original synthetic fixtures: **12/12 PASS**.
- Corrected incumbent-acceptance fixtures: **4/4 PASS**.
- Inherited diagnostic matrix: **153/153 closed**.
- Controlling count matrix: **17/17 closed; 1 exact joint witness**.
- Independent witness replay: **PASS** for one joint and 14 separate-100
  exact witnesses; mutation self-test rejected.
- Ordered-stage barrier: **PASS**; execution skipped because the joint count
  gate was 1/17 rather than 17/17.
- Controlling detailed archive: **17/17 ordered members and hashes PASS**.
- Resource audit: **PASS**; station scheduler 17/17, total wall
  138.488182/7200 seconds, peak RSS 562,397,184/2,147,483,648 bytes, retained
  outcome evidence 67,339/1,073,741,824 bytes.
- Exposure/public surface: **PASS**; zero confirmation objects/values/WEPP
  responses, zero production changes, zero public candidate/profile changes.

## Independent review and report gates

- Accuracy lens: **ACCEPT**, open P1/P2/P3 = 0/0/0.
- Scientific-validity lens: **ACCEPT**, open P1/P2/P3 = 0/0/0.
- Consistency/public-safety lens: **ACCEPT**, open P1/P2/P3 = 0/0/0.
- Accepted report verifier: **PASS**.
- Report verifier mutation self-test: **PASS**.
- Local Markdown links and report-manifest evidence identities: **PASS**.

## Repository gates

Commands run from the repository root:

```text
cargo fmt --check                                  PASS
cargo clippy --all-targets -- -D warnings          PASS
cargo test                                         PASS
python3 docs/reports/verify-report.py <manifest>   PASS
python3 docs/reports/verify-report.py --self-test  PASS
git diff --check                                   PASS
```

Coverage/CRAP is **not applicable**: A5d1b changes no production function under
`crates/`.

## Git LFS gate

The staged index contains valid LFS pointers:

| Archive | SHA-256 OID | Bytes |
|---|---|---:|
| Controlling detailed evidence | `24ba4de1df56d35f7e3b4e2854378c2eb94be81cc09e6a44cda9f825e601dfe7` | 11,451 |
| Invalidated v3 detailed evidence | `8e9020d09b99c01d770cebe85f5761d3c432e72158de5da2704f8f385012eb16` | 6,959 |
| Invalidated v4 certificates | `a1c96742218401e7d7806f39b5cde166cc6115bd0b3f844b79ef8f51988bd289` | 11,440 |

`git lfs fsck`: **PASS**.

The package-scoped `blank-at-eof` whitespace attribute preserves prospectively
hash-frozen files whose registered bytes include a terminal blank line; all
other whitespace checks remain active and `git diff --check` passes.

## Terminal package gate

`python3 artifacts/verify-a5d1b-package.py`: **PASS**.

Terminal replay: 153/153 inherited diagnostics, 1/17 exact joint count
witnesses, 0/0 ordered cells after the conditional skip, and 5/5 mutation
self-tests rejected. The verifier was rerun after the closure record bound this
final gate file.
