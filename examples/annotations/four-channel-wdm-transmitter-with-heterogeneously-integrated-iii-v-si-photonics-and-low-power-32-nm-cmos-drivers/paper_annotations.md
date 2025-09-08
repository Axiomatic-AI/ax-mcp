**Annotation 0** (Page 1):
Type: AnnotationType.TEXT
Description: The paper demonstrates a four-channel wavelength division multiplexing (WDM) transmitter that integrates III-V materials on a silicon photonics platform (III-V/Si). This transmitter is co-packaged with low-power 32 nm SOI CMOS drivers and operates at a 1.3 µm wavelength. It achieves error-free performance (BER < 10^-12) at 25 Gb/s per channel over distances up to 10 km of single-mode fiber, making it suitable for datacenter interconnects.
Tags: key_concept, results
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B. G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.

**Annotation 1** (Page 2):
Type: AnnotationType.TEXT
Description: The Photonic Integrated Circuit (PIC) consists of four tunable lasers, each connected to an electro-absorption modulator (EAM). The outputs of the four EAMs are combined using a multimode interference (MMI) multiplexer. The entire PIC has dimensions of 2.75 mm × 7.6 mm.
Tags: design_specifications, device_physics
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B. G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.

**Annotation 2** (Page 2):
Type: AnnotationType.TEXT
Description: The electro-absorption modulators (EAMs) are fabricated using Aurrion's heterogeneous integration process. They feature a wide bandwidth of approximately 30 nm, low insertion loss of less than 3 dB, and require a low drive voltage between 1 and 2 Vpp.
Tags: device_physics, optical_characteristics, design_specifications
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B. G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.

**Annotation 3** (Page 3):
Type: AnnotationType.TEXT
Description: The CMOS driver IC is designed to have a low power consumption, with a simple architecture consisting of six consecutive CMOS inverters for signal amplification. The driver has an on-chip 50 Ω termination for impedance matching and a series 45 Ω resistor at the output to dampen ringing effects from wire-bond inductance and EAM capacitance. The driver operates with a 1V supply (VDD) and delivers a 1 Vpp output swing.
Tags: design_specifications, electrical_performance, device_physics
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B. G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.

**Annotation 4** (Page 4):
Type: AnnotationType.TEXT
Description: To reproduce the results, the entire WDM transmitter assembly is temperature stabilized at 32 °C using a thermal electric-cooler (TEC). This is a critical operating condition for maintaining stable laser wavelengths and device performance.
Tags: methodology, operating_conditions, measurement_setups
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B. G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.

**Annotation 5** (Page 4):
Type: AnnotationType.TEXT
Description: The Bit Error Rate (BER) measurements were performed using a PRBS-31 sequence. Two pattern generators were used to provide four decorrelated 700 mV peak-to-peak RF input signals to the driver ICs at 25 Gb/s. All four channels of the transmitter were running simultaneously during the test.
Tags: methodology, measurement_setups, electrical_performance
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B. G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.

**Annotation 6** (Page 4):
Type: AnnotationType.TEXT
Description: The receiver setup for BER testing includes a custom 130-nm SiGe IC with a DC-coupled transimpedance stage, which is wire-bonded to a commercial photodetector. The photodetector has a responsivity of 0.6 A/W at 1310 nm. The differential outputs of the receiver are connected to an SHF error detector.
Tags: measurement_setups, methodology
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B.G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.

**Annotation 7** (Page 4):
Type: AnnotationType.TEXT
Description: A trade-off is noted between the driver IC's power consumption and the optical link's performance. By using a 1 Vpp output stage driver to lower power consumption, the achievable optical extinction ratio is reduced (3.3 to 3.9 dB), which can affect the overall operating bitrate and signal integrity of the link.
Tags: results, electrical_performance, optical_characteristics
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B. G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.

**Annotation 8** (Page 5):
Type: AnnotationType.TEXT
Description: The total power consumption of the WDM transmitter operating at 100 Gb/s (4 x 25 Gb/s) is 1151.6 mW. The breakdown is as follows: Lasers consume 1103.85 mW, EAMs consume 28.54 mW, and the four driver ICs consume 19.2 mW. This results in a total energy efficiency of 11.5 pJ/bit.
Tags: results, electrical_performance
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B. G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.

**Annotation 9** (Page 4):
Type: AnnotationType.PARAMETER
Description: The biasing voltage for the Electro-Absorption Modulator (EAM) for channel 1, which is required to reproduce the optical eye diagrams and BER measurements.
Parameter: EAM Bias Voltage (Channel 1) = 2.3 V
Tags: operating_conditions, methodology, parameter
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B. G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.

**Annotation 10** (Page 4):
Type: AnnotationType.PARAMETER
Description: The biasing voltage for the Electro-Absorption Modulator (EAM) for channel 2, a key parameter for setting the modulator's operating point and achieving the reported performance.
Parameter: EAM Bias Voltage (Channel 2) = 2.4 V
Tags: operating_conditions, methodology, parameter
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B. G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.

**Annotation 11** (Page 4):
Type: AnnotationType.PARAMETER
Description: The biasing voltage for the Electro-Absorption Modulator (EAM) for channel 3. This voltage is necessary to correctly bias the device to reproduce the experimental results.
Parameter: EAM Bias Voltage (Channel 3) = 2.9 V
Tags: operating_conditions, methodology, parameter
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B. G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.

**Annotation 12** (Page 4):
Type: AnnotationType.PARAMETER
Description: The biasing voltage for the Electro-Absorption Modulator (EAM) for channel 4, essential for replicating the device's performance as shown in the eye diagrams and BER plots.
Parameter: EAM Bias Voltage (Channel 4) = 3.3 V
Tags: operating_conditions, methodology, parameter
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B. G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.

**Annotation 13** (Page 4):
Type: AnnotationType.PARAMETER
Description: The measured extinction ratio for channel 1, resulting from the specified EAM bias and driver voltage. This value is critical for understanding the signal quality shown in Figure 5.
Parameter: Extinction Ratio (Channel 1) = 3.49 dB
Tags: results, optical_characteristics, parameter
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B. G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.

**Annotation 14** (Page 4):
Type: AnnotationType.PARAMETER
Description: The measured extinction ratio for channel 2. This parameter is a direct result of the operating conditions and is a key indicator of the performance seen in the eye diagrams.
Parameter: Extinction Ratio (Channel 2) = 3.27 dB
Tags: results, optical_characteristics, parameter
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B. G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.

**Annotation 15** (Page 4):
Type: AnnotationType.PARAMETER
Description: The measured extinction ratio for channel 3, which is needed to correlate the input electrical signals and biasing with the output optical signal quality.
Parameter: Extinction Ratio (Channel 3) = 3.68 dB
Tags: results, optical_characteristics, parameter
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B. G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.

**Annotation 16** (Page 4):
Type: AnnotationType.PARAMETER
Description: The measured extinction ratio for channel 4. This value is essential for reproducing the experimental results and understanding the performance limitations of the link.
Parameter: Extinction Ratio (Channel 4) = 3.87 dB
Tags: results, optical_characteristics, parameter
Reference: Huynh, T. N., Ramaswamy, A., Rimolo-Donadio, R., Schow, C., Roth, J. E., Norberg, E. J., ... & Lee, B. G. (2016). Four-channel WDM transmitter with heterogeneously integrated III-V/Si photonics and low power 32 nm CMOS drivers. Journal of Lightwave Technology, 34(13), 3131-3137.
