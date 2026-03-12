WORKFLOW_PROMPT = """# Model Fitting Workflow

## Step-by-Step Process:

### 1️⃣ **Define Your Mathematical Model**
Write your model as a JAX function:
```python
def output_variable_name(input_var, param1, param2, ...):
    # Analytical functions - use jnp.* operations
    return param1 * jnp.exp(-param2 * input_var) + param3
```

### 2️⃣ **Choose a Template**
Call `get_fitting_examples` to see available templates:
- **Analytical functions** (exponential, polynomial, trigonometric)
- **ODE systems** (population dynamics, chemical kinetics)

Pick the template closest to your model structure as context for the optimization.

### 3️⃣ **Adapt the Template**
- Replace the function with your model
- Update parameter names and initial guesses
- *Set realistic bounds for ALL PARAMETERS, ALL INPUTS, AND ALL OUTPUTS variables*
- Use proper pint units ('dimensionless', 'nanometer', 'volt', 'second', etc.)

### 4️⃣ **Prepare Your Data File and Mapping**
Create a CSV/Excel file with your data, then map columns to variables:
```python
data_file = "/path/to/your/data.csv"
input_data = [{"column": "time_col", "name": "time", "unit": "second"}]
output_data = {"columns": ["concentration_col"], "name": "concentration", "unit": "molar"}
```

### 5️⃣ **Run Optimization**
Use `fit_model` with your adapted template.

## Template Selection Guide:
1. **Simple analytical?** → Use polynomial/exponential templates
2. **Complex analytical?** → Use complex helper function example
2. **Time-dependent dynamics?** → Use ODE templates
3. **Custom physics?** → Adapt the closest template structure

## Key Requirements:
- ALL functions must use JAX operations or JAX libraries (jnp.exp, jnp.sin, etc.)
- Every parameter needs bounds (reasonable ranges)
- Input AND output variables need bounds too

Ready to optimize? Get templates with `get_fitting_examples`!"""