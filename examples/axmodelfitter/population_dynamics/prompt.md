# Demo: Population dynamics

Fit the standard Lotka-Volterra predator-prey model:
```math
\begin{dcases}
\frac{{\rm d} x}{{\rm d} t} (t) = a x(t) - b x(t) y(t), & x(0) = x_0\\[1em]
\frac{{\rm d} y}{{\rm d} t}(t) = c x(t) y(t) - d y(t), & y(0) = y_0 
\end{dcases} \\[1em]
```
to the non-dimensionalized timeseries data in `data.csv`. The parameters to be identified are the rate parameters $(a,b,c,d)$ alongside the initial populations of prey and predator species $(x_0, y_0)$. 

The rate parameter values are expected to lie within the following limits: $a \in [0.5, 1.2], b \in [0.8, 1.5], c \in [0.5, 1.0], d\in [0.5,1.0]$. Reasonable bounds for the population sizes $x_0$ and $y_0$ are easily extracted from the data. 


Compute the $R^2$ of the model fit and use the parameter estimates to simulate the population dynamics on a fine timegrid and plot the trajectories against the data to visualize the goodness-of-fit. Write a summary of your results, including visualizations, into a response.md file. 
