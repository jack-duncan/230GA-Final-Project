I ran your script on the real data and through your checks. It ran the first time, with only file paths and `fac` supplied, and reaches the same verdict as my own implementation (FAIL, 1 of 4). The numbers differ, and one of your stop rules fires.

1. `make_synthetic_inputs`. GS10 is a random walk clipped at 0.5 that sits on the floor (76% of 1995-2009 months for seed 0, every month for seed 16). BOND is then constant, I x BOND acts as an I main effect, and your positive control fails check (b)10: 4% of the planted 3% effect reaches alpha (t 0.98), while I x BOND has t -10.8. Seed 16 crashes the null-seed loop (rank-deficient design).

2. `attention_signal`. Requiring 60 full calendar months before the first z is a silent reading you hard-coded. I treat pre-1985 months as unavailable, not zero, so the 48-nonzero minimum is the burn-in. Your reading moves the first threshold from 1994-01 to 1994-12, adds a 2002-12 crossing and starts the window at 1995-02, not 1994-03: pi 0.809 vs. 0.729, shuffle p 0.536 vs. 0.478.

3. `leg_pipeline`. You hedge with the Mkt-RF, SMB and HML in `fac`, the FF5 file. The team hedge uses its FF3 file, which my prompt never said (my gap). SMB differs by up to 3.5 pp a month, b_t moves by up to 0.09, and your check (b)2 stops at 2.3e-3 a month (6e-17 with FF3).

4. `pass_fail_table`. (iv) passes a negative alpha whose five drop-one alphas are also negative.

With readings 2 and 3 switched to mine, your code matches my implementation to 1e-13, all 5,000 shuffle draws included.

Two smaller gaps. `check_no_lookahead` compares end-of-T states only, so it missed both return-side bugs I injected (month-t return hedged with b_t; a position earning its own month). Seen mode ends at 2022-12; its five holdout months flip the seen alpha from -0.16%/yr (t -0.24) to +0.26%/yr (t 0.37).

Please send corrected versions of these functions only, each with a unit test:
- `make_synthetic_inputs`: BOND varies in every window for seeds 0-20, and the positive control puts at least 80% of the planted shift in alpha with t > 2.
- `attention_signal`: a `z_burn_in` parameter with both readings; on a zero-free series from 1985-01, the first z falls in month 48 under mine and month 60 under yours.
- `leg_pipeline`: a separate `hedge_fac` input; changing its SMB moves b_t but not the attribution regressors.
- `pass_fail_table`: a negative alpha fails (iv).
- `check_no_lookahead`: a return-side comparison that flags both injected bugs.
- `__main__`: seen mode ends at 2022-07, with `cut_to` on its look-ahead call.

These fixes are for reproducibility; the frozen rule stays.
