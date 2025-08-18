# Equation Verification and Functional Form Examples

This folder contains examples demonstrating potential use cases of two tools:  
- **`check_equation`** – verifies the correctness of a given equation by symbolic derivation.  
- **`find_functional_form`** – derives and returns the functional form of an equation or function requested by the user.

## Examples Structure

Each example folder contains:
- `prompt.md` - The original query/task description
- `code.py` - Generated SymPy-based script that performs the verification or derivation
- `response.md` - Detailed explanation of the process and results
- Additional context files (e.g., PDFs or supplementary markdown files)

## Available Examples

### Check Equation Examples

1. **Derive H Energy States**
   - Location: `/derive_H_energy_states/`
   - Description: Verifies and derives energy states in quantum mechanics
   - Context: Uses quantum basics from supplementary markdown file

2. **Transmission with Loss Modulation Check**
   - Location: `/transmission_with_loss_modulation_check/`
   - Description: Validates transmission equations with loss modulation
   - Context: Uses Poon ring resonator paper as reference

### Find Functional Form Examples

1. **Kinetic Energy in Terms of Momentum**
   - Location: `/kinetic_energy_in_terms_of_momentum/`
   - Description: Derives the functional form of kinetic energy expressed through momentum
   - Context: Based on quantum mechanics principles

2. **Dynamical Transmission as Function of C**
   - Location: `/dynamical_transmission_as_function_of_C/`
   - Description: Derives transmission function in terms of coupling coefficient
   - Context: Based on ring resonator physics from Poon paper

## Response Format

For each example, you'll find:

1. **Generated Code (`code.py`)**
   - SymPy-based implementation
   - Thoroughly commented derivation steps
   - Validation or derivation logic
   - Python-executable format

2. **Detailed Report (`response.md`)**
   - Step-by-step explanation of the process
   - Commentary on performed tasks
   - Validation of results
   - Additional insights and observations

## Notes

- Both tools support symbolic mathematical validation and derivation automation
- Examples demonstrate real-world physics and photonics applications
- Each example is self-contained with necessary context files
- Code is generated to be executable and modifiable for similar problems
- Examples show both theoretical (quantum mechanics) and practical (photonics) applications