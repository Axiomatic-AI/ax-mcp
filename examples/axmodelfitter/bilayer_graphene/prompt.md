# Demo: Bilayer graphene 
Using the *AxModelFitter MCP*, fit the following physics-informed transport model to the experimental bilayer graphene data in `data.csv`. Compute the $R^2$ value of the fitted model and prepare a visualization of the model fit quality. To that end, group the data by back gate voltage and show a resistance trace for each measured value as function of top gate voltage on the same axes. Write a summary report that *includes visualizations* of the into `response.md`.

## Model Overview

The model is derived from the fundamental bilayer graphene Hamiltonian and incorporates displacement field electrostatics, gap opening, mobility modulation, and residual conductivity effects. The model predicts resistance as a function of dual gate voltages ($V_{TG}$, $V_{BG}$) using displacement field physics:

$$R(V_{TG}, V_{BG}) = \frac{1}{\sigma_{total}} + R_c,$$

where the total conductivity combines Drude and residual contributions controlled by the displacement fields.

### 1. Electrostatic Model

**Displacement Fields:**
$$D_T = V_{TG} - V_{TG0} \quad \text{(top displacement field)}$$
$$D_B = V_{BG} - V_{BG0} \quad \text{(bottom displacement field)}$$

**Derived Quantities:**
$$\bar{D} = \frac{D_T + D_B}{2} \quad \text{(average displacement field)}$$
$$\Delta D = D_B - D_T \quad \text{(displacement difference)}$$

### 2. Physical Effects

**Gap Opening:**
$$\Delta = \beta |\bar{D}| \quad \text{(tunable bandgap)}$$

**Carrier Density:**
$$n \propto \Delta D \quad \text{(induced by asymmetric gating)}$$

**Mobility Modulation:**
$$\mu(\bar{D}) = \frac{\mu_0}{1 + \alpha |\bar{D}|^p} \quad \text{(disorder scattering)}$$

**Residual Conductivity:**
$$\sigma_{min}(\Delta) = \frac{\sigma_{00}}{1 + \left|\frac{\Delta}{\Delta_0}\right|^q} \quad \text{(quantum/thermal transport)}$$

### 3. Total Transport

**Carrier Density from Displacement Field:**
$$n = \frac{\varepsilon |\Delta D|}{e \times d} \quad \text{(induced carriers)}[m^{-2}]$$

**Drude Conductivity:**
$$\sigma_{drude} = g_s \cdot g_v \cdot e \cdot n \cdot \mu(\bar{D}) \quad \text{(main transport channel [S])}$$

**Combined Conductivity:**
$$\sigma_{total} = \sigma_{drude} + \sigma_{min}(\Delta)$$

**Final Resistance:**
$$R = \frac{1}{\sigma_{total}} \times 10^{-3} + R_c \quad \text{(convert Ω to kΩ)}$$

**Physical Constants:**
- $e = 1.602 \times 10^{-19}$ C (elementary charge)
- $g_s = 2$ (spin degeneracy)
- $g_v = 2$ (valley degeneracy)
- $\epsilon = 8.854 \times 10^{-12} \times 3.9$ F/m (effective permittivity)
- $d = 0.35 \times 10^{-9}$ m (bilayer separation)


## Parameter Classification

### **Fit Parameters** (Optimized during fitting)

| Parameter   | Symbol        | Units         | Physical Meaning                   | Typical Range | Initial guess |
| ----------- | ------------- | ------------- | ---------------------------------- | ------------- | ------------- |
| **mu0**     | $\mu_0$       | m²/(V·s)      | Base mobility at zero displacement | 0.1 - 2.0     | 1.0           |
| **alpha**   | α             | V$^{-p}$      | Mobility degradation strength      | 0.5 - 5.0     | 1.0           |
| **p**       | p             | dimensionless | Mobility degradation exponent      | 1.0 - 3.0     | 1.5           |
| **sigma00** | $\sigma_{00}$ | S             | Base residual conductivity         | 1e-5 - 5e-4   | 5e-5          |
| **Delta0**  | $\Delta_0$    | eV            | Gap scale parameter                | 0.02 - 0.15   | 0.08          |
| **q**       | q             | dimensionless | Gap dependence exponent            | 1.0 - 4.0     | 1.5           |
| **beta**    | β             | eV/V          | Gate-to-gap coupling efficiency    | 0.005 - 0.05  | 0.02          |
| **VTG0**    | $V_{TG0}$     | V             | Top gate charge neutrality point   | -0.3 to 0.3   | 0.0           |
| **VBG0**    | $V_{BG0}$     | V             | Back gate charge neutrality point  | -0.3 to 0.3   | 0.0           |
| **Rc**      | $R_c$         | kΩ            | Contact resistance                 | 0.05 - 0.5    | 0.15          |

### **Input Variables** (Experimental controls)

| Variable | Symbol   | Units | Physical Meaning  | Range    |
| -------- | -------- | ----- | ----------------- | -------- |
| **V_TG** | $V_{TG}$ | V     | Top gate voltage  | -2 to +2 |
| **V_BG** | $V_{BG}$ | V     | Back gate voltage | -2 to +2 |

### **Output Variable** (Measured quantity)

| Variable | Symbol | Units | Physical Meaning | Range      |
| -------- | ------ | ----- | ---------------- | ---------- |
| **R**    | R      | kΩ    | Sheet resistance | 0.01 - 100 |

### **Physical Constants** (Fixed values)

| Constant                   | Symbol     | Value             | Units         | Physical Meaning     |
| -------------------------- | ---------- | ----------------- | ------------- | -------------------- |
| **Elementary charge**      | e          | 1.602×10⁻¹⁹       | C             | Fundamental charge   |
| **Spin degeneracy**        | $g_s$      | 2                 | dimensionless | Electron spin states |
| **Valley degeneracy**      | $g_v$      | 2                 | dimensionless | K and K' valleys     |
| **Effective permittivity** | $\epsilon$ | 8.854×10⁻¹² × 3.9 | F/m           | Dielectric response  |
| **Bilayer separation**     | $d$        | 0.35×10⁻⁹         | m             | Interlayer distance  |

