# Axiomatic Equations Server

An MCP server that provides equation composition capabilities using the Axiomatic AI platform, with a focus on creating the custom equation together with the derivation recipe.


## Tools Available

### `compose_expression`

generates the desired equation from all the other equations in the source text together with a code explaining the derivation steps.

**Parameters:**

- `file_path` (Path, required): The absolute path to the PDF file to analyze
- `task` (str, required): explanation of the expression of interest

**Returns:**

- Expression object of the composed expression together with descriptions of all symbols
- Comments if necessary
- Sympy code explaining how the composition of the desired equation was done.

**Features:**

- Uses Derivation endpoint and Equation Processing endpoint
- Employs shared/documents/pdf_to_markdown.py function to preprocess the pdf to MD format
- Maintains original mathematical notation and conventions.
- Provides units 

**Example Usage:**

```
Provide the formula that expresses N as a function of momentum and temperature
```

(wait for response)

```
Use the composed epxression to visualize N in the report youre writing.
```
