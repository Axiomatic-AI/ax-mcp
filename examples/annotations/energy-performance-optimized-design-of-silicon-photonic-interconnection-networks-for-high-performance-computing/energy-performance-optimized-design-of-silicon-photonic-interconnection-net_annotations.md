**Annotation 0** (Page 1):
Type: AnnotationType.TEXT
Description: Specifies the cross-sectional dimensions of the silicon waveguides that form the Mach-Zehnder Interferometer (MZI) depicted in Figure 1a. These dimensions are crucial for determining the modal properties and light confinement of the waveguide.
Tags: device_specification, geometric_dimension, methodology
Reference: Bahadori, M., Rumley, S., Polster, R., Gazman, A., Traverso, M., Webster, M., ... & Bergman, K. (2017, March). Energy-performance optimized design of silicon photonic interconnection networks for high-performance computing. In 2017 Design, Automation & Test in Europe (DATE) (pp. 326-331). IEEE.

**Annotation 1** (Page 1):
Type: AnnotationType.PARAMETER
Description: The 3dB bandwidth of the spectral dips in the transmission response of the Mach-Zehnder Interferometer (MZI). This parameter indicates the wavelength range over which the MZI provides significant attenuation.
Parameter: 3dB Bandwidth = 9.35 nm
Tags: device_specification, performance_metric
Reference: Bahadori, M., Rumley, S., Polster, R., Gazman, A., Traverso, M., Webster, M., ... & Bergman, K. (2017, March). Energy-performance optimized design of silicon photonic interconnection networks for high-performance computing. In 2017 Design, Automation & Test in Europe (DATE) (pp. 326-331). IEEE.

**Annotation 2** (Page 1):
Type: AnnotationType.PARAMETER
Description: The physical radius of the microring resonator shown in Figure 1b. The radius is a fundamental design parameter that influences the free spectral range (FSR) and bending loss of the resonator.
Parameter: Radius = 5.0 µm
Tags: device_specification, geometric_dimension
Reference: Bahadori, M., Rumley, S., Polster, R., Gazman, A., Traverso, M., Webster, M., ... & Bergman, K. (2017, March). Energy-performance optimized design of silicon photonic interconnection networks for high-performance computing. In 2017 Design, Automation & Test in Europe (DATE) (pp. 326-331). IEEE.

**Annotation 3** (Page 1):
Type: AnnotationType.PARAMETER
Description: The 3dB bandwidth of the resonances for the 5µm radius microring resonator. This value is inversely related to the quality factor (Q) of the resonator and determines its selectivity as a filter.
Parameter: 3dB Bandwidth = 0.5 nm
Tags: device_specification, performance_metric
Reference: Bahadori, M., Rumley, S., Polster, R., Gazman, A., Traverso, M., Webster, M., ... & Bergman, K. (2017, March). Energy-performance optimized design of silicon photonic interconnection networks for high-performance computing. In 2017 Design, Automation & Test in Europe (DATE) (pp. 326-331). IEEE.

**Annotation 4** (Page 3):
Type: AnnotationType.TEXT
Description: The standard cross-sectional dimensions for the rectangular silicon waveguides used throughout the photonic interconnection network. These dimensions are chosen to ensure single-mode operation.
Tags: device_specification, geometric_dimension, fabrication_parameter
Reference: Bahadori, M., Rumley, S., Polster, R., Gazman, A., Traverso, M., Webster, M., ... & Bergman, K. (2017, March). Energy-performance optimized design of silicon photonic interconnection networks for high-performance computing. In 2017 Design, Automation & Test in Europe (DATE) (pp. 326-331). IEEE.

**Annotation 5** (Page 3):
Type: AnnotationType.PARAMETER
Description: The thickness of the silicon slab layer in the rib waveguides used for the microring resonator structures. This is a critical dimension in the fabrication process that affects mode confinement.
Parameter: Slab Thickness = 100.0 nm
Tags: device_specification, geometric_dimension, fabrication_parameter
Reference: Bahadori, M., Rumley, S., Polster, R., Gazman, A., Traverso, M., Webster, M., ... & Bergman, K. (2017, March). Energy-performance optimized design of silicon photonic interconnection networks for high-performance computing. In 2017 Design, Automation & Test in Europe (DATE) (pp. 326-331). IEEE.

**Annotation 6** (Page 3):
Type: AnnotationType.PARAMETER
Description: The assumed propagation loss for straight silicon waveguides, which is a key factor in the overall link power budget. This loss is primarily caused by light scattering from sidewall roughness.
Parameter: Waveguide Propagation Loss = 1.0 dB/cm
Tags: device_specification, material_property
Reference: Bahadori, M., Rumley, S., Polster, R., Gazman, A., Traverso, M., Webster, M., ... & Bergman, K. (2017, March). Energy-performance optimized design of silicon photonic interconnection networks for high-performance computing. In 2017 Design, Automation & Test in Europe (DATE) (pp. 326-331). IEEE.

**Annotation 7** (Page 3):
Type: AnnotationType.EQUATION
Description: An empirical power law equation used to model the bending loss in curved silicon waveguides as a function of the bend radius (R_µm). This model is critical for designing compact ring resonators with low loss. The parameters are given as a = 1.09×10^6, b = 10.15, and c = 1 dB/cm. The output of the equation is the bending loss in dB/cm.
Equation: Loss_{dB/cm} = a \times (R_{\mu m})^{-b} + c
Tags: methodology, key_concept, design_consideration
Reference: Bahadori, M., Rumley, S., Polster, R., Gazman, A., Traverso, M., Webster, M., ... & Bergman, K. (2017, March). Energy-performance optimized design of silicon photonic interconnection networks for high-performance computing. In 2017 Design, Automation & Test in Europe (DATE) (pp. 326-331). IEEE.

**Annotation 8** (Page 4):
Type: AnnotationType.TEXT
Description: Specifies the doping concentration and mechanism (PN carrier depletion) used to create the high-speed microring modulators. The modulation effect is achieved by altering the free-carrier concentration in the waveguide, which changes its refractive index.
Tags: device_specification, fabrication_parameter, material_property
Reference: Bahadori, M., Rumley, S., Polster, R., Gazman, A., Traverso, M., Webster, M., ... & Bergman, K. (2017, March). Energy-performance optimized design of silicon photonic interconnection networks for high-performance computing. In 2017 Design, Automation & Test in Europe (DATE) (pp. 326-331). IEEE.

**Annotation 9** (Page 2):
Type: AnnotationType.PARAMETER
Description: The quality factor (Q-factor) assumed for the microring resonator when used as a modulator. The Q-factor is a measure of the sharpness of the resonance and affects the modulator's performance.
Parameter: Modulator Q-factor = 6000.0
Tags: device_specification, performance_metric
Reference: Bahadori, M., Rumley, S., Polster, R., Gazman, A., Traverso, M., Webster, M., ... & Bergman, K. (2017, March). Energy-performance optimized design of silicon photonic interconnection networks for high-performance computing. In 2017 Design, Automation & Test in Europe (DATE) (pp. 326-331). IEEE.

**Annotation 10** (Page 2):
Type: AnnotationType.PARAMETER
Description: The maximum peak-to-peak voltage used to drive the microring modulator. This voltage determines the extent of the refractive index change and thus the modulation depth.
Parameter: Max Modulator Drive Voltage = 5.0 V
Tags: device_specification, design_consideration
Reference: Bahadori, M., Rumley, S., Polster, R., Gazman, A., Traverso, M., Webster, M., ... & Bergman, K. (2017, March). Energy-performance optimized design of silicon photonic interconnection networks for high-performance computing. In 2017 Design, Automation & Test in Europe (DATE) (pp. 326-331). IEEE.

**Annotation 11** (Page 2):
Type: AnnotationType.PARAMETER
Description: The electrical power consumed by the micro-heater to tune the resonance wavelength of a single microring resonator. Thermal tuning is necessary to align the resonator's wavelength with the desired channel wavelength.
Parameter: Thermal Tuning Power = 1.0 mW/ring
Tags: device_specification, energy_performance
Reference: Bahadori, M., Rumley, S., Polster, R., Gazman, A., Traverso, M., Webster, M., ... & Bergman, K. (2017, March). Energy-performance optimized design of silicon photonic interconnection networks for high-performance computing. In 2017 Design, Automation & Test in Europe (DATE) (pp. 326-331). IEEE.

**Annotation 12** (Page 5):
Type: AnnotationType.PARAMETER
Description: The thermo-optic coefficient of silicon, representing the change in its refractive index per unit change in temperature. This physical property is the basis for thermal tuning of the silicon microring resonators.
Parameter: Thermo-optic coefficient (dnsi/dT) = 0.000186 /K
Tags: material_property, key_concept
Reference: Bahadori, M., Rumley, S., Polster, R., Gazman, A., Traverso, M., Webster, M., ... & Bergman, K. (2017, March). Energy-performance optimized design of silicon photonic interconnection networks for high-performance computing. In 2017 Design, Automation & Test in Europe (DATE) (pp. 326-331). IEEE.

**Annotation 13** (Page 6):
Type: AnnotationType.TEXT
Description: The energy performance of the link is optimized by selecting the ideal combination of the number of wavelength channels and the data rate per channel. This optimization process involves adjusting the ring radius to minimize energy consumption, with a radius of about 7µm identified as optimal. The rings are operated at their critical coupling point to ensure maximum efficiency.
Tags: energy_performance, design_consideration, optimization
Reference: Bahadori, M., Rumley, S., Polster, R., Gazman, A., Traverso, M., Webster, M., ... & Bergman, K. (2017, March). Energy-performance optimized design of silicon photonic interconnection networks for high-performance computing. In 2017 Design, Automation & Test in Europe (DATE) (pp. 326-331). IEEE.
