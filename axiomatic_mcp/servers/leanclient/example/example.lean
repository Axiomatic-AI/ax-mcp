import Mathlib.Algebra.Group.Basic
import Mathlib.GroupTheory.OrderOfElement
import Mathlib.Data.Complex.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Data.Real.Sqrt
import Mathlib.Data.Set.Basic
import Mathlib.Data.PNat.Basic
import Mathlib.Data.ZMod.Basic

-- Universe
variable {G : Type*} [Group G] (x y g : G) (n : ℕ) (m a b : ℤ)

/-- Define the set G = {a ∈ ℂ | a ^ 1 ∈ ℂ} -/
def RootsOfUnity : Set ℂ := {z | ∃ n : ℕ+, z^(n : ℕ) = 1}

/-- Define the set G = {a + b√2 | a, b ∈ ℚ} -/
def QSqrt2 : Set ℝ := {x | ∃ a b : ℚ, x = ↑a + ↑b * Real.sqrt 2}

/-- Problem 12c: Find the order of 6 in the additive group $\mathbb{Z}/36\mathbb{Z}$. -/
theorem order_of_6_zmod36 :
  addOrderOf (6 : ZMod 36) = 6 := by
  -- Initial sketch of the proof:
  -- The order of 6 in ℤ/36ℤ is the smallest positive integer k such that k * 6 ≡ 0 (mod 36)
  -- This means we need the smallest k such that 36 divides k * 6
  -- Since gcd(6, 36) = 6, we have 36 | k * 6 iff 36/6 | k, i.e., 6 | k
  -- So the smallest such k is 6
  
  -- Step 1: Show that 6 * 6 = 0 in ZMod 36
  have h1 : (6 : ℕ) • (6 : ZMod 36) = 0 := by
    norm_num
    rfl
  
  -- Step 2: Show that for any k < 6, k * 6 ≠ 0 in ZMod 36
  have h2 : ∀ k : ℕ, 0 < k → k < 6 → k • (6 : ZMod 36) ≠ 0 := by
    intro k hk_pos hk_lt6
    -- k • 6 = k * 6 in ZMod 36
    -- We need to show k * 6 ≠ 0 (mod 36)
    -- Since 0 < k < 6, we have 0 < k * 6 < 36
    -- So k * 6 mod 36 = k * 6 ≠ 0
    rw [nsmul_eq_mul]
    norm_cast
    have h_bound : k * 6 < 36 := by
      calc k * 6 < 6 * 6 := by
            apply Nat.mul_lt_mul_of_pos_right hk_lt6
            norm_num
          _ = 36 := by norm_num
    have h_pos : 0 < k * 6 := by
      apply Nat.mul_pos hk_pos
      norm_num
    rw [ZMod.natCast_eq_zero_iff]
    intro hdvd
    have : k * 6 = 0 := Nat.eq_zero_of_dvd_of_lt hdvd h_bound
    linarith [h_pos]
  
  -- Step 3: Conclude that addOrderOf 6 = 6
  rw [addOrderOf_eq_iff]
  constructor
  · exact h1
  · intro m hm_lt6 hm_pos
    exact h2 m hm_pos hm_lt6
  · norm_num
