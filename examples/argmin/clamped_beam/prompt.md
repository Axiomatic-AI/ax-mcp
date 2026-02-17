# Clamped Beam (Optimal Control)

Minimize control effort to deflect a clamped beam while keeping deflection within bounds.

Use a simple single-mode surrogate for the beam tip deflection:

- **States:** tip deflection `w(t)` and velocity `v(t)`
- **Control:** actuator force `u(t)`
- **Dynamics:**
  - `w_dot = v`
  - `v_dot = u`

Solve a minimum-energy deflection maneuver:

- **Time horizon:** `T = 1.0`
- **Initial state:** `w(0) = 0`, `v(0) = 0`
- **Terminal state:** `w(T) = 0.1`, `v(T) = 0`
- **State bounds:** `-0.12 <= w(t) <= 0.12`
- **Control bounds:** `-2.0 <= u(t) <= 2.0`
- **Objective:** minimize control effort `∫ u(t)^2 dt`
