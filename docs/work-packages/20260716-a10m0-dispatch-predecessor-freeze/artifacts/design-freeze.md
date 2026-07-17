# A10 design freeze

- A10 executes as milestone-owned packages A10M0 through A10M9. Iteration
  stays inside its owning milestone unless an explicit amendment is required.
- A10M0 freezes authorities and dispatch. A10M1 freezes corpus and roles.
  A10M2 validates compute. A10M3--M9 remain governed by the reviewed study
  plan and their own future packages.
- A10M1 and A10M2 may execute independently after A10M0. Neither authorizes
  A10M3 alone; A10M3 requires both accepted handoffs.
- Development evidence cannot be relabeled confirmation evidence. The locked
  confirmation series remains unread until the plan's selection gate permits
  access.
- The overall reviewed A10 resource ceiling remains 800 GPU-hours.
- A10M2 is further bounded to five base jobs totaling 40 requested GPU-minutes,
  one exact infrastructure-transient rerun of at most 10 GPU-minutes, and a
  hard ceiling of one GPU-hour.
- A10M2 changes no production Rust behavior and makes no model-quality claim.
