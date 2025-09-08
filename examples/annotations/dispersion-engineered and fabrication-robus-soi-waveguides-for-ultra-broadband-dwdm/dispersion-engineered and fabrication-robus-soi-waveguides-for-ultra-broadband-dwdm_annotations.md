**Annotation 0** (Page 1):
Type: AnnotationType.EQUATION
Description: The transmission of a Mach-Zehnder Interferometer (MZI) is characterized by its interference fringes, which are used to determine the group index (ng) of the constituent waveguides. The group index is a critical parameter that governs the dispersion and overall performance of the MZI, especially in DWDM systems. This equation provides the fundamental relationship between the group index, the operating wavelength (λ), the free spectral range (FSR) of the MZI's transmission spectrum, and the physical path length difference between the two arms of the MZI (ΔL).
Equation: n_g = \frac{\lambda^2}{FSR \cdot \Delta L}
Tags: equation, MZI, group_index, FSR
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 1** (Page 1):
Type: AnnotationType.PARAMETER
Description: The group index of the waveguide, which represents the ratio of the speed of light in vacuum to the group velocity of light in the waveguide.
Parameter: n_g
Tags: parameter, group_index
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 2** (Page 1):
Type: AnnotationType.PARAMETER
Description: The wavelength of light.
Parameter: λ nm
Tags: parameter, wavelength
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 3** (Page 1):
Type: AnnotationType.PARAMETER
Description: The free spectral range of the MZI, defined as the wavelength spacing between adjacent transmission peaks or dips.
Parameter: FSR nm
Tags: parameter, FSR
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 4** (Page 1):
Type: AnnotationType.PARAMETER
Description: The difference in physical length between the two arms of the MZI.
Parameter: ΔL nm
Tags: parameter, MZI
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 5** (Page 2):
Type: AnnotationType.EQUATION
Description: This equation presents the analytical model for the group index (ng) as a function of wavelength (λ) and waveguide width (w). It is based on a previously developed effective index (neff) model. The model is formulated as the difference between the effective index and its wavelength derivative, and is expressed as a sum of polynomial terms. The coefficients pn(w) are themselves ratios of polynomials in w, ensuring that the group index approaches a constant value for large widths, characteristic of a slab waveguide. This model is fundamental for predicting and engineering the dispersion properties of the SOI waveguides.
Equation: n*g(\lambda, w) = n*{eff}(\lambda, w) - \lambda \cdot \frac{dn*{eff}(\lambda, w)}{d\lambda} = \sum*{n=0}^{3} (1-\lambda) p*n(w)^n, \text{where } p_n(w) = p*{n0} \frac{w^2 + p*{n1}w + p*{n2}}{w^2 + p*{n3}w + p*{n4}}
Tags: equation, group_index, dispersion_engineering, analytical_model
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 6** (Page 2):
Type: AnnotationType.PARAMETER
Description: The group index as a function of wavelength and waveguide width.
Parameter: n_g(λ, w)
Tags: parameter, group_index
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 7** (Page 2):
Type: AnnotationType.PARAMETER
Description: The effective index of the waveguide mode as a function of wavelength and waveguide width.
Parameter: n_eff(λ, w)
Tags: parameter, effective_index
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 8** (Page 2):
Type: AnnotationType.PARAMETER
Description: The wavelength of light.
Parameter: λ nm
Tags: parameter, wavelength
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 9** (Page 2):
Type: AnnotationType.PARAMETER
Description: The width of the waveguide.
Parameter: w nm
Tags: parameter, waveguide_width
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 10** (Page 2):
Type: AnnotationType.PARAMETER
Description: Fitting coefficients for the polynomial model of the group index.
Parameter: p_nm
Tags: parameter, fitting_coefficient
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 11** (Page 2):
Type: AnnotationType.EQUATION
Description: This auxiliary function, z, is defined to quantify the difference between the modeled group index and the experimentally measured group index (ng*). It accounts for a systematic shrinkage in the fabricated waveguide width (Δw) compared to the design value. By minimizing the sum of squares of this function (Σ||z||^2), the optimal fitting coefficients (pnm) and the average width shrinkage (Δw) are determined. This process is crucial for creating a fabrication-aware model that accurately predicts the performance of the fabricated devices.
Equation: z(p\_{nm}, \Delta w) = n_g(\lambda, w - \Delta w) - n_g^*, n \in \{0,...,3\}, m \in \{0,...,4\}
Tags: equation, fabrication_robustness, optimization, error_function
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 12** (Page 2):
Type: AnnotationType.PARAMETER
Description: The auxiliary function representing the difference between the modeled and measured group index.
Parameter: z(p_nm, Δw)
Tags: parameter, error_function
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 13** (Page 2):
Type: AnnotationType.PARAMETER
Description: The systematic shrinkage in waveguide width across the fabricated wafer.
Parameter: Δw = 40.0 nm
Tags: parameter, fabrication_variation, waveguide_width
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 14** (Page 2):
Type: AnnotationType.PARAMETER
Description: The extracted group index from experimental measurements.
Parameter: n_g\*
Tags: parameter, group_index, experimental_data
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 15** (Page 3):
Type: AnnotationType.TEXT
Description: To reproduce the results shown in Figure 2a, which plots the extracted group indices against wavelength for various waveguide widths, one must consider the experimental setup. For each of the six selected waveguide widths (400, 480, 600, 800, 1200, and 2000 nm), 35 different MZI devices were measured. The group index for each device was extracted from its transmission spectrum. Figure 2a displays the average group index values at each wavelength for the devices of a given width, illustrating the impact of waveguide geometry on dispersion.
Tags: methodology, experimental_setup, reproducibility, group_index
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 16** (Page 3):
Type: AnnotationType.TEXT
Description: A key aspect of the design methodology is the co-optimization of dispersion and fabrication robustness. The trade-off is analyzed by plotting the derivative of the effective index with respect to width (dneff/dw) and the derivative of the group index with respect to wavelength (dng/dλ) against the waveguide width. The term dneff/dw indicates sensitivity to fabrication variations (robustness), while dng/dλ is proportional to the group velocity dispersion (GVD). Figure 2c shows that a waveguide width of approximately 630 nm provides a near-zero dispersion at 1550 nm, while also offering improved fabrication robustness compared to narrower waveguides.
Tags: design_principle, dispersion_engineering, fabrication_robustness, trade-off_analysis
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.

**Annotation 17** (Page 3):
Type: AnnotationType.TEXT
Description: The paper concludes that the proposed design methodology allows for the engineering of SOI waveguides with co-optimized dispersion and fabrication robustness. An optimal waveguide width of 630 nm is identified, which can achieve near-zero dispersion across the S, C, and L bands. This design improves fabrication robustness by a factor of 2 compared to standard foundry-provided waveguides. For applications where robustness is more critical than ultra-broadband dispersion, wider waveguides (w > 1200 nm) can be used to achieve an order of magnitude improvement in fabrication robustness.
Tags: conclusion, key_finding, design_principle, DWDM
Reference: Yuyang Wang, Songli Wang, Asher Novick, Aneek James, Robert Parsons, Anthony Rizzo, and Keren Bergman, "Dispersion-Engineered and Fabrication-Robust SOI Waveguides for Ultra-Broadband DWDM", OFC 2023 Optica Publishing Group 2023.
