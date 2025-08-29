import Mathlib

theorem unitary_idempotent_implies_identity 
  {n : Type*} [DecidableEq n] [Fintype n] {α : Type*} [CommRing α] [StarRing α]
  (U : Matrix.unitaryGroup n α) (h : (U : Matrix n n α) * (U : Matrix n n α) = U) : 
  U = 1 := by
  sorry