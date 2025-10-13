# Equation Verification and Functional Form Examples

This folder contains examples demonstrating potential use cases of two tools:  
- **`check_equation`** – verifies the correctness of a given equation by symbolic derivation.  
- **`find_functional_form`** – derives and returns the functional form of an equation or function requested by the user.

## Examples Structure

Each example folder contains:
- `prompt.md` - The original query/task description
- `code.py` - Generated SymPy-based script that performs the verification or derivation
- Additional context files (e.g., PDFs or supplementary markdown files)

## Available Examples

### Check Equation Examples

1. **Checking correctness of the FHS algorithm**
   - Location: `/check_FHS_algorithm/`
   - Description: Verifies and derives the Fukui-Hatsugai-Suzuki formula for calculating Chern numbers in lattice models
   - Context: Uses [this paper](https://arxiv.org/pdf/1912.12736) 

2. **Transmission with Loss Modulation Check**
   - Location: `/transmission_with_loss_modulation_check/`
   - Description: Validates transmission equations with loss modulation
   - Context: Uses Poon ring resonator paper as reference

### Find Functional Form Examples

1. **Derivation of the second order perturbation formula**
   - Location: `/derive_perturbation_result/`
   - Description: Derives the functional form of the second order perturbation approximation for the quasi-flat band width
   - Context: Based on [this paper](https://journals.aps.org/prb/pdf/10.1103/PhysRevB.102.235126) 

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
