# Lotka-Volterra Population Dynamics Model Fitting Results

## Summary

I successfully fitted the standard Lotka-Volterra predator-prey model to the provided non-dimensionalized timeseries data using the AxModelFitter optimization framework. The model achieved an excellent fit with an R² value of **0.974**, explaining 97.4% of the variance in the data.

## Mathematical Model

The Lotka-Volterra system of differential equations was implemented as:

```
dx/dt = ax - bxy,  x(0) = x₀
dy/dt = cxy - dy,  y(0) = y₀
```

where:
- x(t): prey population
- y(t): predator population
- a: prey growth rate
- b: predation efficiency
- c: predator efficiency  
- d: predator death rate

## Optimization Results

### Fitted Parameters

| Parameter | Value | Description |
|-----------|--------|-------------|
| x₀ | 0.558 | Initial prey population |
| y₀ | 1.198 | Initial predator population |
| a | 0.698 | Prey growth rate |
| b | 1.354 | Predation efficiency |
| c | 0.887 | Predator efficiency |
| d | 0.926 | Predator death rate |

### Model Performance

- **R² = 0.974** (Excellent fit - explains 97.4% of variance)
- **MSE = 0.0100** (Very low mean squared error)
- **Execution Time**: 9.2 seconds
- **Function Evaluations**: 49
- **Optimizer**: NLopt with gradient-based optimization

All fitted parameters fall within the specified bounds:
- Rate parameters (a,b,c,d) are within their expected ranges
- Initial conditions are consistent with the data

## Visualization

The results are visualized in `lotka_volterra_fit.png` showing:

1. **Time Series Plot**: Comparison of model predictions vs. data points for both prey and predator populations
2. **Phase Portrait**: The characteristic closed-loop trajectory in phase space
3. **Residuals Plot**: Small, randomly distributed residuals indicating good model fit

## Conclusion

The Lotka-Volterra model provides an excellent description of the population dynamics data. The high R² value and low residuals confirm that the classic predator-prey model accurately captures the oscillatory behavior observed in the timeseries. The fitted parameters are physically reasonable and fall within the expected bounds, validating both the model structure and the optimization approach.

The optimization successfully identified the underlying dynamical parameters, demonstrating the effectiveness of the JAX-based differential equation solver combined with gradient-based optimization for parameter estimation in dynamical systems.