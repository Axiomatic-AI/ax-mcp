# Production-quality SymPy code to derive E in terms of p for a free, non-relativistic particle
#
# This module encodes the standard derivation from the free-particle Schrödinger equation:
#   E = (ħ^2 k^2) / (2 m) and p = ħ k  =>  E(p) = p^2 / (2 m)
# It provides a pure function that performs the symbolic steps using SymPy's substitution,
# exposes the composed result in `composed_equation`, and includes pytest tests verifying
# the derivation.

from __future__ import annotations
from typing import Dict, Any

import sympy as sp

__all__ = [
    "derive_energy_in_terms_of_momentum",
    "composed_equation",
    "E_of_p_equation",
]

# -----------------------------------------------------------------------------
# 1) Symbols and basic setup
# -----------------------------------------------------------------------------
m = sp.symbols("m", positive=True, real=True)
hbar = sp.symbols("hbar", positive=True, real=True)
p, k, E = sp.symbols("p k E", real=True)

# Optional convenience alias for Unicode ħ
ħ = hbar  # noqa: E741


# -----------------------------------------------------------------------------
# 2) Derivation function
# -----------------------------------------------------------------------------
def derive_energy_in_terms_of_momentum() -> Dict[str, Any]:
    """
    Derive the non-relativistic free-particle energy E in terms of momentum p.

    Steps:
      1) Free-particle energy in k-space: E = (ħ^2 k^2) / (2 m)
      2) Momentum-wave number relation: p = ħ k
      3) Solve relation for k = p/ħ
      4) Substitute into E(k) and simplify → E(p) = p^2 / (2 m)

    Returns
    -------
    Dict[str, Any]
        - 'E_k'              : E expressed in terms of k.
        - 'momentum_relation': Equality p = ħ k.
        - 'k_in_terms_of_p'  : Expression for k in terms of p (p/ħ).
        - 'E_p'              : Final expression E(p) = p^2 / (2 m).
    """
    # 1) Free-particle energy in k-space
    E_k = (hbar**2 * k**2) / (2 * m)

    # 2) Momentum-wave number relation
    momentum_relation = sp.Eq(p, hbar * k)

    # 3) Solve for k
    k_in_terms_of_p = sp.solve(momentum_relation, k)[0]  # yields p / ħ

    # 4) Substitute into E(k)
    E_p = sp.simplify(E_k.subs(k, k_in_terms_of_p))

    return {
        "E_k": E_k,
        "momentum_relation": momentum_relation,
        "k_in_terms_of_p": k_in_terms_of_p,
        "E_p": E_p,
    }


# -----------------------------------------------------------------------------
# 3) Derived results available at import
# -----------------------------------------------------------------------------
_steps = derive_energy_in_terms_of_momentum()
composed_equation = _steps["E_p"]  # p^2 / (2 m)
E_of_p_equation = sp.Eq(E, composed_equation)  # Full equation form E = p^2/(2m)


# -----------------------------------------------------------------------------
# 4) Pytest tests
# -----------------------------------------------------------------------------
def test_composed_equation_matches_expected():
    expected = p**2 / (2 * m)
    assert sp.simplify(composed_equation - expected) == _
