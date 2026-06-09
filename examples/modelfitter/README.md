# Model Fitter Examples

Examples for the `AxModelFitterV2` MCP server.

Each folder contains:
- `prompt.md` — what to ask the agent

## Usage

Give the agent the prompt — it will call `generate_code` then `execute_code` to fit the model and return results.

## Examples

| Example | What it demonstrates |
|---------|---------------------|
| `exponential_decay_with_uq` | Basic curve fit + per-parameter standard errors via sandwich covariance |
| `lotka_volterra` | ODE fit with diffrax + uncertainty quantification using DirectAdjoint |
| `ring_resonator` | Photonic lineshape fit with Lorentzian vs Gaussian AIC model comparison |
| `model_comparison` | Polynomial candidate ranking with AIC/BIC/Akaike weights |
| `reaction_system` | Mass-action ODE fit (A+B⇌C→D) with latent species and covariance |
| `ring_modulator` | Photonic ring modulator T(λ,V) fit with sandwich covariance |
| `bilayer_graphene` | Physics-informed dual-gate transport fit, 10 parameters |
