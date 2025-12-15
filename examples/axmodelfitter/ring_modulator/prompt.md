
# Demo: Ring modulator
Consider the following model for the power transmission a ring modulator as function of wavelength $\lambda$ and bias voltage $V$:
```math
    T(\lambda, V) = \left \lvert \frac{t-a e^{2\pi j n(V) L/\lambda}}{1-t a e^{2\pi j n(V) L/\lambda}} \right\rvert^2.
```
Transmission is determined by the factor $t = \sqrt{1-\kappa}$ governed by the power coupling coefficient $\kappa \in [0.1, 0.5]$. Power losses are accounted for by the decay factor $a= 10^{-\alpha L/20}$ with parameter $\alpha \in [0,0.6]$ $\frac{1}{\mu{\rm m}}$. $L$ denotes the ring length which is known to be quite tightly clustered around 5.0 $\mu{\rm m}$, i.e., $L \in [4.5, 5.5]$ $\mu {\rm m}$.

We assume the effective refractive index depends linearly on the bias voltage $V$, i.e., $n(V) = n_0 + g_n V$, with parameters $n_0 \in [2.2, 2.4]$ and $g_n \in [-0.05, 0.05]$ $\frac{1}{{\rm V}}$.

Using the AxModelFitter MCP, fit the parameters $(n_0, g_n, L, \alpha, \kappa)$ to the data provided in `data.csv` and compute the $R^2$-value. After fitting, compute the parameter covariance matrix to quantify uncertainty in the fitted parameters. Finally, create a visualization of the fitting results, judge if the fit is good, if the parameter values are physically sensible and prepare a summary of your results, including visualizations and parameter uncertainties, in a response.md file.
