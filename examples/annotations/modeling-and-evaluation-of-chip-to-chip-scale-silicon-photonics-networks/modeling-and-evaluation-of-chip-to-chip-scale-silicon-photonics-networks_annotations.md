**Annotation 0** (Page 4):
Type: AnnotationType.EQUATION
Description: This equation represents the link budget for a WDM optical interconnect, expressed in decibels. It establishes the relationship between the input laser power, the total power penalty (attenuation and other losses), the photodetector sensitivity, and the maximum number of wavelength channels (Nλ) that can be supported on the link. To maximize the link bandwidth (which is proportional to Nλ), the total power penalty (PPdB) must be minimized. This equation is fundamental for calculating the link capacity for each network architecture discussed in the paper.
Equation: P_{in_{dBm}} - PP_{dB} > P_{d_{dBm}} + 10 \log_{10}{N_{\lambda}}
Tags: equation, physical_layer, link_budget, key_concept
Reference: Hendry, R., Nikolova, D., Rumley, S., & Bergman, K. (2014). Modeling and Evaluation of Chip-to-Chip Scale Silicon Photonic Networks. 2014 IEEE 22nd Annual Symposium on High-Performance Interconnects.

**Annotation 1** (Page 4):
Type: AnnotationType.PARAMETER
Description: The maximum optical power that can be injected into a waveguide by the laser before non-linear effects cause significant signal distortion. This value limits the total power available for all wavelength channels on a link.
Parameter: P_in = 100.0 mW
Tags: parameter, physical_layer, laser
Reference: Hendry, R., Nikolova, D., Rumley, S., & Bergman, K. (2014). Modeling and Evaluation of Chip-to-Chip Scale Silicon Photonic Networks. 2014 IEEE 22nd Annual Symposium on High-Performance Interconnects.

**Annotation 2** (Page 4):
Type: AnnotationType.PARAMETER
Description: The sensitivity of the photodetector, which is the minimum optical power required to reliably detect a signal at a given data rate. This value is for a non-return-to-zero (NRZ) modulation at 10 Gb/s.
Parameter: P_d = 6.3 uW
Tags: parameter, physical_layer, photodetector
Reference: Hendry, R., Nikolova, D., Rumley, S., & Bergman, K. (2014). Modeling and Evaluation of Chip-to-Chip Scale Silicon Photonic Networks. 2014 IEEE 22nd Annual Symposium on High-Performance Interconnects.

**Annotation 3** (Page 4):
Type: AnnotationType.TEXT
Description: The loss model for microring modulators includes several components. A 1dB signal attenuation occurs for a modulated 'one' bit. A 2dB power penalty is assumed due to imperfect extinction. For on-off keying with a 50% probability of modulating a 'one' or 'zero', the average optical power loss is 2.4 dB. Additionally, modulators on other waveguides contribute a small amount of loss. Figure 4(a) plots the total modulator loss as a function of the number of wavelengths for configurations with no waveguide sharing (1S) and two-way waveguide sharing (2S).
Tags: methodology, loss_model, modulator
Reference: Hendry, R., Nikolova, D., Rumley, S., & Bergman, K. (2014). Modeling and Evaluation of Chip-to-Chip Scale Silicon Photonic Networks. 2014 IEEE 22nd Annual Symposium on High-Performance Interconnects.

**Annotation 4** (Page 4):
Type: AnnotationType.TEXT
Description: The loss in silicon photonic waveguides is primarily a constant loss of 1 dB/cm. However, the total waveguide loss for a link is dependent on the number of wavelength channels (Nλ). This is because a higher number of channels requires more modulating rings and filters, which in turn increases the total waveguide length needed to interconnect these components. Furthermore, in networked architectures like the Benes network, larger switch sizes are needed for more wavelengths, which also increases the required waveguide length. Figure 4(b) illustrates this relationship, showing how waveguide loss increases with the number of wavelengths.
Tags: methodology, loss_model, waveguide
Reference: Hendry, R., Nikolova, D., Rumley, S., & Bergman, K. (2014). Modeling and Evaluation of Chip-to-Chip Scale Silicon Photonic Networks. 2014 IEEE 22nd Annual Symposium on High-Performance Interconnects.

**Annotation 5** (Page 4):
Type: AnnotationType.TEXT
Description: The loss attributed to the network switch fabric, as shown in Figure 4(c), accounts for both the insertion loss and crosstalk penalty from passing through multiple stages of 2x2 microring switches. In a Benes network, the number of switches an optical signal must traverse is dependent on the radix (R) of the switch, which is related to the number of interconnected PNI's. The plot shows how this loss scales with the size of the switch (e.g., 2x2, 4x4, 8x8, 16x16).
Tags: methodology, loss_model, switch
Reference: Hendry, R., Nikolova, D., Rumley, S., & Bergman, K. (2014). Modeling and Evaluation of Chip-to-Chip Scale Silicon Photonic Networks. 2014 IEEE 22nd Annual Symposium on High-Performance Interconnects.

**Annotation 6** (Page 5):
Type: AnnotationType.TEXT
Description: The loss associated with demultiplexing the WDM signal at the receiver end is shown in Figure 4(d). This loss is composed of power penalties from signal truncation by the microring filters and a constant insertion loss. In configurations with waveguide sharing (2S), an additional 1x2 switch is needed to direct the signal to the correct bank of filters, which adds to the loss. This additional switch loss is calculated similarly to the network switch losses.
Tags: methodology, loss_model, demux_filter
Reference: Hendry, R., Nikolova, D., Rumley, S., & Bergman, K. (2014). Modeling and Evaluation of Chip-to-Chip Scale Silicon Photonic Networks. 2014 IEEE 22nd Annual Symposium on High-Performance Interconnects.

**Annotation 7** (Page 5):
Type: AnnotationType.PARAMETER
Description: A fixed power penalty of 2dB is assumed to account for jitter in the clocking and data recovery (CDR) mechanisms. This is a system-level impairment that degrades signal quality.
Parameter: Jitter Power Penalty = 2.0 dB
Tags: parameter, physical_layer, impairment
Reference: Hendry, R., Nikolova, D., Rumley, S., & Bergman, K. (2014). Modeling and Evaluation of Chip-to-Chip Scale Silicon Photonic Networks. 2014 IEEE 22nd Annual Symposium on High-Performance Interconnects.

**Annotation 8** (Page 5):
Type: AnnotationType.PARAMETER
Description: The loss incurred when light is coupled from an off-chip optical fiber to an on-chip silicon waveguide. The paper assumes a 1dB loss per coupler. A signal in a Benes network traverses four such couplers, while a signal in a full-mesh network traverses two.
Parameter: Waveguide-fiber coupler loss = 1.0 dB
Tags: parameter, physical_layer, loss_model
Reference: Hendry, R., Nikolova, D., Rumley, S., & Bergman, K. (2014). Modeling and Evaluation of Chip-to-Chip Scale Silicon Photonic Networks. 2014 IEEE 22nd Annual Symposium on High-Performance Interconnects.
