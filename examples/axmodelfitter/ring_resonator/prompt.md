# Demo: Ring resonator

The file `data.csv` contains measurements of the power transmission of a ring resonator as function of detuning around its resonance frequency. The measurement noise is expected to be Gaussian with standard deviation of 0.01. Use this data alongside *AxModelFitter MCP* to complete the following sequential tasks. Write your results, including visualizations, into a response.md file.

### 1. Model selection
Using information criteria, compare the following two models and make a judgement which is better. 

1. Lorentzian dip: 
   
    $$T(f) = T_{\max} - (T_{\max}-T_{\min}) \frac{1}{1+ (f/f_{h})^2}$$

    where $T_{\max} \in [0.9, 1.0], T_{\min} \in [0.7, 0.9], f_{h} \in [0.001, 0.1]$ GHz. Extract a reasonable initial guess for the parameters by looking at teh data ($T_{\min}$ = minimal transmission, $T_{\max}$ = maximal transmission, $f_h$ = detuning at $T(f_h)= 1/2 (T_{\max}+T_{\min})$).

2. Gaussian dip:
    
    $$T(f) = T_{\max} - (T_{\max} - T_{\min}) \exp{\left(- \frac{1}{2}(f/f_h)^2\right)}$$

    with $T_{\max} \in [0.9, 1.1], T_{\min} \in [0.7, 0.9], f_h \in [0.001, 0.1]$ GHz. Extract a reasonable initial guess for the parameters by looking at teh data ($T_{\min}$ = minimal transmission, $T_{\max}$ = maximal transmission, $f_h$ = detuning at $T(f_h)=  0.7 T_{\min} + 0.3 T_{\max}$).

Plot both model predictions against the data to provide visual evidence for your choice. Label the curves with their names and Akaike weights.

### 2. Cross-validation
For the model you have identified as better, perform 5-fold cross validation to confirm the model neither over- nor underfits the data and generalizes nicely. Report mean and variance of $R^2$ values.

### 3. Model fitting
Fit the better model against all data and report the optimal parameter values. Report MSE and $R^2$ of the final fit.

