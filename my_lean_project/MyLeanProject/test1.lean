import Mathlib

theorem unitary_idempotent_implies_identity 
  {n : Type*} [DecidableEq n] [Fintype n] {α : Type*} [CommRing α] [StarRing α]
  (U : Matrix.unitaryGroup n α) (h : U * U = U) : 
  U = 1 := by
  -- Use the fact that in a group, idempotent elements are the identity
  rw [← IsIdempotentElem.iff_eq_one]
  exact h