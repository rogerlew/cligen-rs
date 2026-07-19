# Execution hold

Terminal: `HOLD-A10M5R8R1-CALENDAR-MISSINGNESS`

The corrected authority, plan, immutable asset stage, and exact P1 control
reconstruction passed. The canonical synthetic dispersion test also passed.
Job `1014023` then exited before treatment training with:

    eight-year eligibility incomplete: fit=0/1200 validation=0/240

The accepted Daymet documents span 1980-01-01 through 2009-12-31: 10,958
Gregorian dates, 10,950 `source_observed=true` rows, and 10,950 non-null rows
for every weather field in the inspected source document. The eight excluded
rows are the absent leap-year December 31 observations represented by the
A10M1 `daymet_official_365_v1` corpus contract.
Every exact eight-year interval therefore includes accepted missingness and no
window satisfies an all-calendar-day predicate.

The failure is an implementation assumption, not evidence against the
scientific objective. R2 keeps exact calendar years, masks unobserved core
rows, requires at least 28 observed rows in every year-month, and applies the
low-weight proper score only to precipitation/Tmax/Tmin. It does not impute or
change the climate-statistic estimand.

Resource/operational record:

- Slurm job: `1014023`, node03, exit 1, 246 seconds
- requested primary: 60 GPU-minutes; actual: 246 GPU-seconds / five charged
  GPU-minutes
- recovery: not invoked; reserve released after authenticated cleanup
- collection: 20,480 bytes, SHA-256
  `651878416be2c5b9102d368950e42fe188c399119bccd5496a2805bfc10afbd0`
- control checkpoint SHA-256:
  `fd54c491180c58dc21e25b8f2324604239acb5a4e3e439995fbb2e92a0d92752`
- job-local cleanup: verified absent
- durable run root: verified absent
- protected roles opened: none

Terminology correction (2026-07-19): an earlier revision called the eight
excluded rows "leap-day missingness." The count and hold are unchanged;
official-calendar Daymet retains February 29 and omits December 31 in leap
years.
