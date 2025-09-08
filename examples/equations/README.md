# Equation Verification and Functional Form Examples

This folder contains examples demonstrating potential use cases of two tools:  
- **`check_equation`** – verifies the correctness of a given equation by symbolic derivation.  
- **`find_functional_form`** – derives and returns the functional form of an equation or function requested by the user.

---

## Example 1: Hydrogen Energy Levels Verification

- **Description**  
  This example uses the `check_equation` tool to verify the correctness of the hydrogen energy levels formula as presented in `example_document.md`.  
  The tool derives the formula starting from the hydrogen Hamiltonian and checks its validity step by step.

- **Response Format**  
  The user receives:
  1. **Report** – a detailed description of the derivation process, including commentary on the performed tasks. It is saved in the `response.md` file.
  2. **`code.py`** – a SymPy-based script that performs the correctness verification and symbolic derivation.  
     The code is thoroughly commented to explain each step of the derivation process.

---

## Example 2: Functional Form Derivation

- **Description**  
  This example demonstrates the `find_functional_form` tool. Instead of verifying a known formula, the tool derives the requested equation or function directly.

- **Response Format**  
  The output format is the same as in Example 1:
  1. **Reposne** – explaining the derivation and results. It is saved in the `response.md` file.
  2. **`code.py`** – a SymPy-based script that produces the requested functional form with explanatory comments.

---

## Notes

- Both tools are intended for symbolic mathematical validation and derivation automation, helping scientists verify the correctness of equations, generate functions from known expressions, and streamline the derivation process directly into code.

- The examples in this folder provide reproducible workflows for extending or adapting these tools to other physics and mathematics problems.
