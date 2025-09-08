# microring_T_of_C.py
# sympy-based derivation of T(t) in terms of C(t) for a microring resonator
#
# This module derives an explicit, closed-form transmission T(t)=B(t)/A in terms of the
# circulating field C(t) (and C(t-τ)) and device parameters for a lossless directional
# coupler. It follows the algebraic plan described in the analyst report.

from __future__ import annotations

import sympy as sp

# ---------- Symbols and functions ----------
# Time and delay
t, tau = sp.symbols("t tau", real=True)

# Field amplitudes as functions of time
C = sp.Function("C")  # circulating amplitude in the ring
B = sp.Function("B")  # transmitted/output port amplitude
T = sp.Function("T")  # transmission coefficient function

# Device parameters as time-dependent functions
sigma = sp.Function("sigma")  # transmission coefficient of the coupler
kappa = sp.Function("kappa")  # coupling coefficient of the coupler
alpha = sp.Function("a")  # round-trip attenuation a(t)
phi = sp.Function("phi")  # round-trip phase φ(t)

# Input amplitude (constant complex scalar, nonzero)
A = sp.symbols("A", complex=True, nonzero=True)

# Convenience shorthands for values at time t
sig_t = sigma(t)
kap_t = kappa(t)
a_t = alpha(t)
phi_t = phi(t)
C_t = C(t)
C_delay = C(t - tau)
B_t = B(t)

# ---------- Core equations (from the excerpt; Eq. 5) ----------
# 1) B(t) = sigma(t) A + i kappa(t) a(t) e^{-i phi(t)} C(t-τ)
eq1 = sp.Eq(B_t, sig_t * A + sp.I * kap_t * a_t * sp.exp(-sp.I * phi_t) * C_delay)

# 2) i kappa(t) C(t) = sigma(t) B(t) - A
eq2 = sp.Eq(sp.I * kap_t * C_t, sig_t * B_t - A)

# ---------- Lossless directional coupler constraint ----------
# sigma(t)^2 + kappa(t)^2 = 1  (amplitude coefficients, real-valued in a lossless coupler)
# We will use it algebraically as 1 - sigma^2 -> kappa^2 when simplifying.
lossless_subs = {1 - sig_t**2: kap_t**2}

# ---------- Derivation strategy ----------
# Plan (documented for clarity):
# - Solve eq2 for A and substitute into eq1 to eliminate A.
# - Solve the resulting linear equation for B(t) in terms of C(t) and C(t-τ).
# - Form T(t) = B(t)/A, eliminating A via eq2 again.
# - Use the lossless coupler identity to simplify the result to a compact closed form.

# Step 1: Solve eq2 for A
A_from_eq2 = sp.solve(eq2, A)[0]  # A = sigma*B - i*kappa*C

# Step 2: Substitute A into eq1 and solve for B(t)
eq1_sub_B = eq1.subs(A, A_from_eq2)
B_expr_general = sp.solve(eq1_sub_B, B_t)[0]
# This yields B = I*kappa*(a*e^{-i phi}*C_delay - sigma*C) / (1 - sigma^2)
B_expr = sp.simplify(B_expr_general.subs(lossless_subs))

# Step 3: Express A in terms of B and C using eq2, then form T = B/A
A_expr = A_from_eq2.subs(B_t, B_expr)
T_expr_raw = sp.simplify(sp.together(B_expr / A_expr))
T_expr = sp.simplify(T_expr_raw.subs(lossless_subs))

# Step 4: Provide the composed equation T(t) = ...
composed_equation = sp.Eq(T(t), T_expr)

# For clarity, also build an explicitly factored target form expected from hand algebra
T_expected = (a_t * sp.exp(-sp.I * phi_t) * C_delay - sig_t * C_t) / (sig_t * a_t * sp.exp(-sp.I * phi_t) * C_delay - C_t)

# ---------- Optional internal check (not asserted at import) ----------
# Ensure the derived expression matches the expected compact form (under lossless identity)
_ = sp.simplify(sp.together(T_expr - T_expected).subs(lossless_subs))  # Should simplify to 0 in tests


# ---------- Tests (pytest) ----------


def test_symbolic_equivalence_under_lossless_subs():
    """Symbolically verify that the derived T matches the compact target, using generic symbols.

    Strategy:
    - Replace all time-dependent function values at time t by independent symbols.
    - Impose the lossless identity 1 - sigma^2 = kappa^2 to simplify the difference.
    - Check that the difference simplifies to zero.
    """
    s, k = sp.symbols("s k")
    a_sym, phi_sym = sp.symbols("a_sym phi_sym")
    C0, Ctau = sp.symbols("C0 Ctau")

    subs_map = {
        sig_t: s,
        kap_t: k,
        a_t: a_sym,
        phi_t: phi_sym,
        C_t: C0,
        C_delay: Ctau,
    }

    T_rhs_sub = sp.simplify(composed_equation.rhs.subs(subs_map))
    T_expected_sub = sp.simplify(((a_sym * sp.exp(-sp.I * phi_sym) * Ctau - s * C0) / (s * a_sym * sp.exp(-sp.I * phi_sym) * Ctau - C0)))

    diff = sp.simplify(sp.together(T_rhs_sub - T_expected_sub).subs({1 - s**2: k**2}))
    assert sp.simplify(diff) == 0


def test_numeric_consistency():
    """Numerically verify equality for a concrete set of parameters that satisfy sigma^2 + kappa^2 = 1."""
    # Choose a Pythagorean pair: sigma=4/5, kappa=3/5 satisfies s^2 + k^2 = 1
    s_val = sp.Rational(4, 5)
    k_val = sp.Rational(3, 5)
    a_val = sp.Rational(9, 10)
    phi_val = sp.Rational(3, 10)  # radians
    C0_val = 1 + 2 * sp.I
    Ctau_val = sp.Rational(1, 2) - sp.I / 4

    T_numeric = sp.N(
        composed_equation.rhs.subs(
            {
                sig_t: s_val,
                kap_t: k_val,
                a_t: a_val,
                phi_t: phi_val,
                C_t: C0_val,
                C_delay: Ctau_val,
            }
        )
    )

    T_expected_numeric = sp.N(
        ((a_val * sp.exp(-sp.I * phi_val) * Ctau_val - s_val * C0_val) / (s_val * a_val * sp.exp(-sp.I * phi_val) * Ctau_val - C0_val))
    )

    assert sp.Abs(T_numeric - T_expected_numeric) < 1e-12
