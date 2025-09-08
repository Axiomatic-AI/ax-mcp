# verify_eq9_Ta.py
# Production-quality SymPy verification for Eq. (9): T_a(t)
#
# This module constructs the recurrence for the transmission T(t) under
# loss modulation only, derives the formal Neumann-series solution, builds the
# paper's Eq. (9) expression, and verifies their equivalence via symbolic
# comparison of finite truncations. A pytest suite is provided.

from __future__ import annotations

import sympy as sp

# -----------------------------------------------------------------------------
# 1) Symbols and functions (explicitly defined to avoid NameError)
# -----------------------------------------------------------------------------
# Time and system parameters
# All are declared symbolically; no numeric values are required for the proof.
t, tau, phi = sp.symbols("t tau phi", complex=True)

# Transmission-related constants
sigma = sp.symbols("sigma", complex=True)  # external coupling/transmission coeff
kappa = sp.symbols("kappa", complex=True)  # (declared for completeness; unused here)

# Discrete indices
n = sp.symbols("n", integer=True, nonnegative=True)
m = sp.symbols("m", integer=True)

# Field/loss functions
T = sp.Function("T")  # transmission coefficient function of time
a = sp.Function("a")  # round-trip amplitude loss factor function of time

# Useful constants
I = sp.I

# -----------------------------------------------------------------------------
# 2) Define recurrence for loss modulation (only a(t) varies)
# -----------------------------------------------------------------------------
# Strategy:
# - Encode T(t) = sigma - a(t) * exp(-i*phi) + sigma * a(t) * exp(-i*phi) * T(t - tau)
# - Recognize this as T(t) = f(t) + g(t) * T(t - tau) with f, g as below.

# 2.1 Define f(t) and g(t) as callables for convenient time shifts
f = lambda arg: sigma - a(arg) * sp.exp(-I * phi)
g = lambda arg: sigma * a(arg) * sp.exp(-I * phi)

# The recurrence (for reference as a SymPy expression)
recurrence = sp.Eq(T(t), f(t) + g(t) * T(t - tau))

# -----------------------------------------------------------------------------
# 3) Construct the formal Neumann series solution
# -----------------------------------------------------------------------------
# Strategy:
# - T_series(t) = Sum_{n=0..oo} [ Prod_{m=0..n-1} g(t - m*tau) ] * f(t - n*tau)
# - Use the convention that an empty product (n=0) equals 1.

# Infinite-series form (formal)
G_prod = lambda n_sym: sp.Product(g(t - m * tau), (m, 0, n_sym - 1))
T_series_inf = sp.summation(G_prod(n) * f(t - n * tau), (n, 0, sp.oo))

# -----------------------------------------------------------------------------
# 4) Construct the paper's Eq. (9) expression
# -----------------------------------------------------------------------------
# Strategy:
# - T_paper(t) = [n=0 term] + Sum_{n=1..oo} sigma**n * exp(-i*n*phi)
#                 * [sigma - a(t - n*tau) * exp(-i*phi)] * Prod_{m=0..n-1} a(t - m*tau)
# - We build the infinite series (formal) and also a helper for finite truncations.

# Infinite-series form (formal)
A_prod = lambda n_sym: sp.Product(a(t - m * tau), (m, 0, n_sym - 1))
T_paper_inf = f(t) + sp.summation(
    (sigma**n) * sp.exp(-I * n * phi) * (sigma - a(t - n * tau) * sp.exp(-I * phi)) * A_prod(n),
    (n, 1, sp.oo),
)

# -----------------------------------------------------------------------------
# 5) Finite truncations for robust equality checks
# -----------------------------------------------------------------------------
# Strategy:
# - Implement pure-Python truncated sums to avoid unevaluated sympy Sum objects.
# - Compare partial sums for several N to ensure structural identity.


def partial_series(t_arg: sp.Symbol, N: int) -> sp.Expr:
    """Return the N-truncated Neumann series T_N(t).

    T_N(t) = sum_{n=0..N} [ Prod_{m=0..n-1} g(t - m*tau) ] * f(t - n*tau)

    Uses empty product = 1 for n=0.
    """
    terms = []
    for k in range(0, N + 1):
        if k == 0:
            prod_term = sp.Integer(1)
        else:
            prod_term = sp.Product(g(t_arg - m * tau), (m, 0, k - 1))
        terms.append(prod_term * f(t_arg - k * tau))
    return sp.simplify(sp.Add(*terms))


def partial_paper(t_arg: sp.Symbol, N: int) -> sp.Expr:
    """Return the N-truncated series written in the paper's Eq. (9) style.

    T_N^paper(t) = [n=0 term] + sum_{n=1..N} sigma**n * exp(-i*n*phi)
                   * [sigma - a(t - n*tau) * exp(-i*phi)] * Prod_{m=0..n-1} a(t - m*tau)
    """
    # n = 0 term
    terms = [f(t_arg)]
    for k in range(1, N + 1):
        prod_a = sp.Product(a(t_arg - m * tau), (m, 0, k - 1))
        terms.append((sigma**k) * sp.exp(-I * k * phi) * (sigma - a(t_arg - k * tau) * sp.exp(-I * phi)) * prod_a)
    return sp.simplify(sp.Add(*terms))


# -----------------------------------------------------------------------------
# 6) Verification helper and result
# -----------------------------------------------------------------------------
# Strategy:
# - For N in {0,1,2,3}, check partial_series == partial_paper by simplify.
# - Check recurrence holds for partial sums: T_N(t) = f(t) + g(t) * T_{N-1}(t - tau) for N>=1.
# - Aggregate results into a single boolean 'correct'.


def verify_symbolically() -> bool:
    Ns = [0, 1, 2, 3]
    all_ok = True
    for Nval in Ns:
        lhs = partial_series(t, Nval)
        rhs = partial_paper(t, Nval)
        if sp.simplify(lhs - rhs) != 0:
            all_ok = False
            break
    # Recurrence check for partial sums (for N>=1)
    if all_ok:
        for Nval in [1, 2, 3]:
            T_N = partial_series(t, Nval)
            T_Nm1_shift = partial_series(t - tau, Nval - 1)
            rec_diff = sp.simplify(T_N - (f(t) + g(t) * T_Nm1_shift))
            if rec_diff != 0:
                all_ok = False
                break
    return bool(all_ok)


# The requested VERIFY result: boolean variable 'correct'
correct = verify_symbolically()

# -----------------------------------------------------------------------------
# 7) Pytest test suite
# -----------------------------------------------------------------------------
# These tests assert the equivalences and recurrence identities for small N.


def test_partial_series_matches_paper_N0():
    assert sp.simplify(partial_series(t, 0) - partial_paper(t, 0)) == 0


def test_partial_series_matches_paper_N1():
    assert sp.simplify(partial_series(t, 1) - partial_paper(t, 1)) == 0


def test_partial_series_matches_paper_N2():
    assert sp.simplify(partial_series(t, 2) - partial_paper(t, 2)) == 0


def test_partial_series_matches_paper_N3():
    assert sp.simplify(partial_series(t, 3) - partial_paper(t, 3)) == 0


def test_partial_series_satisfies_recurrence_N1():
    T1 = partial_series(t, 1)
    T0_shift = partial_series(t - tau, 0)
    assert sp.simplify(T1 - (f(t) + g(t) * T0_shift)) == 0


def test_partial_series_satisfies_recurrence_N2():
    T2 = partial_series(t, 2)
    T1_shift = partial_series(t - tau, 1)
    assert sp.simplify(T2 - (f(t) + g(t) * T1_shift)) == 0


def test_partial_series_satisfies_recurrence_N3():
    T3 = partial_series(t, 3)
    T2_shift = partial_series(t - tau, 2)
    assert sp.simplify(T3 - (f(t) + g(t) * T2_shift)) == 0


if __name__ == "__main__":
    # Simple runtime report to confirm execution and correctness when run directly.
    print("Recurrence:", recurrence)
    print("Symbolic verification of Eq. (9) form (N=0..3):", verify_symbolically())
