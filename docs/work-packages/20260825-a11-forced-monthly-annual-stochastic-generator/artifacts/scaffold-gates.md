# A11 scaffold gates

Evidence mode: Ran
Date: 2026-08-25
Source base: `2f65bf8` (`main`, equal to `origin/main` before scaffold edits)
Working directory: `/Users/roger/src/cligen-rs`
Tool versions: Cargo 1.97.1, rustc 1.97.1, ripgrep 15.2.0, Ruby 2.6.10p210

| Command | Result |
|---|---|
| `cargo fmt --check` | PASS |
| `cargo clippy --all-targets -- -D warnings` | PASS |
| `cargo test` | PASS |
| `git diff --check` | PASS |
| Local relative-Markdown-link validation for all changed scaffold documents | PASS |

The shell emitted the pre-existing startup warning that
`/tmp/cligen-cargo/env` was absent. The commands still ran with exit status 0.
Coverage/CRAP is not triggered by this scaffold because it adds no production
function under `crates/`. The three Cargo gates were rerun after dispositioning
the independent-review findings and remained passing. The reviewer
independently reran the authored-text and relative-link commands during closure
review; both remained passing.

The exact authored-text and relative-link checks were:

```zsh
a11_docs=(
  docs/ROADMAP.md
  docs/exec-plans/20260721-a10-external-normal-conditioning.md
  docs/exec-plans/20260825-a11-forced-stochastic-generator.md
  docs/specifications/README.md
  docs/specifications/SPEC-A11-FORCED-STOCHASTIC-GENERATOR.md
  docs/work-packages/README.md
  docs/work-packages/20260825-a11-forced-monthly-annual-stochastic-generator/package.md
  docs/work-packages/20260825-a11-forced-monthly-annual-stochastic-generator/artifacts/README.md
  docs/work-packages/20260825-a11-forced-monthly-annual-stochastic-generator/artifacts/review.md
  docs/work-packages/20260825-a11-forced-monthly-annual-stochastic-generator/artifacts/scaffold-gates.md
)
scan_status=0
rg -n '[[:blank:]]+$' "${a11_docs[@]}" || scan_status=$?
test "$scan_status" -eq 1
ruby -e 'bad = []; ARGV.each { |f| File.read(f).scan(/\[[^\]]*\]\(([^)]+)\)/).flatten.each { |raw| p = raw.split("#", 2).first; next if p.empty? || p =~ %r{\A(?:https?://|mailto:)}; target = File.expand_path(p, File.dirname(f)); bad << "#{f}: #{raw}" unless File.exist?(target) } }; abort(bad.join("\n")) unless bad.empty?' "${a11_docs[@]}"
```
