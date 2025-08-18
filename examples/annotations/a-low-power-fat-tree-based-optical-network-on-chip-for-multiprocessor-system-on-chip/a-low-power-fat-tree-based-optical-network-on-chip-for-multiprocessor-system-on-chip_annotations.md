**Annotation 0** (Page 3):
Type: AnnotationType.TEXT
Description: The FONOC (fat tree-based optical NoC) topology is designed to connect 'k' processors using an 'l'-level fat tree. The number of network levels required is determined by the number of processors. For a system without an inter-chip optical network, the OTARs at the highest level can be removed.
Tags: topology, key_concept
Reference: Gu, H., Xu, J., & Zhang, W. (2009). A Low-Power Fat Tree-based Optical Network-on-Chip for Multiprocessor System-on-Chip. 2009 Design, Automation & Test in Europe Conference & Exhibition.

**Annotation 1** (Page 3):
Type: AnnotationType.EQUATION
Description: This equation calculates the number of network levels (l) required in a FONOC to connect 'k' processors. The topology is based on a fat tree structure.
Equation: l = \log\_{2} k + 1
Tags: topology, equation
Reference: Gu, H., Xu, J., & Zhang, W. (2009). A Low-Power Fat Tree-based Optical Network-on-Chip for Multiprocessor System-on-Chip. 2009 Design, Automation & Test in Europe Conference & Exhibition.

**Annotation 2** (Page 3):
Type: AnnotationType.EQUATION
Description: This equation determines the total number of Optical Turnaround Routers (OTARs) required in a FONOC that connects 'k' processors and includes an inter-chip optical network. The OTARs are distributed across the levels of the fat tree.
Equation: \text{Number of OTARs} = \frac{k}{2} \log\_{2} k
Tags: topology, equation
Reference: Gu, H., Xu, J., & Zhang, W. (2009). A Low-Power Fat Tree-based Optical Network-on-Chip for Multiprocessor System-on-Chip. 2009 Design, Automation & Test in Europe Conference & Exhibition.

**Annotation 3** (Page 3):
Type: AnnotationType.EQUATION
Description: This equation calculates the total number of Optical Turnaround Routers (OTARs) required in a FONOC that connects 'k' processors, assuming no inter-chip optical network is used. This allows for the omission of the topmost level of routers.
Equation: \text{Number of OTARs} = \frac{k}{2} (\log\_{2} k - 1)
Tags: topology, equation
Reference: Gu, H., Xu, J., & Zhang, W. (2009). A Low-Power Fat Tree-based Optical Network-on-Chip for Multiprocessor System-on-Chip. 2009 Design, Automation & Test in Europe Conference & Exhibition.

**Annotation 4** (Page 4):
Type: AnnotationType.TEXT
Description: EETAR is an energy-efficient, adaptive, and distributed turnaround routing algorithm optimized for FONOC. It routes packets up the fat tree to a common ancestor of the source and destination, and then down to the destination. It prioritizes passive routing (without powering on microresonators) to save power and reduce insertion loss, which is possible for 40% of all routing cases. This optimization also reduces the size of SETUP packets by not requiring source addresses.
Tags: methodology, key_concept, algorithm
Reference: Gu, H., Xu, J., & Zhang, W. (2009). A Low-Power Fat Tree-based Optical Network-on-Chip for Multiprocessor System-on-Chip. 2009 Design, Automation & Test in Europe Conference & Exhibition.

**Annotation 5** (Page 4):
Type: AnnotationType.EQUATION
Description: This equation defines the total energy consumed to transmit a payload packet (Epk). It is the sum of the energy directly consumed by the payload packet's journey and the energy consumed by the associated control overhead.
Equation: E*{pk} = E*{payload} + E\_{ctrl}
Tags: equation, power_consumption, energy_efficiency
Reference: Gu, H., Xu, J., & Zhang, W. (2009). A Low-Power Fat Tree-based Optical Network-on-Chip for Multiprocessor System-on-Chip. 2009 Design, Automation & Test in Europe Conference & Exhibition.

**Annotation 6** (Page 4):
Type: AnnotationType.EQUATION
Description: This equation calculates the energy consumed directly by a payload packet. It includes the power for active microresonators, propagation delay, and the energy for optical-to-electronic (OE) and electronic-to-optical (EO) conversions. Parameters are: 'm' (number of on-state microresonators), 'P*mr' (average power of an on-state microresonator), 'L_payload' (payload packet size), 'R' (data rate), 'd' (distance), 'c' (light speed in vacuum), 'n' (refractive index of the waveguide), and 'E_oeeo' (energy for 1-bit OE/EO conversion).
Equation: E*{payload} = m P*{mr} (\frac{L*{payload}}{R} + \frac{d \cdot n}{c}) + E*{oeeo} L*{payload}
Tags: equation, power_consumption, energy_efficiency
Reference: Gu, H., Xu, J., & Zhang, W. (2009). A Low-Power Fat Tree-based Optical Network-on-Chip for Multiprocessor System-on-Chip. 2009 Design, Automation & Test in Europe Conference & Exhibition.

**Annotation 7** (Page 5):
Type: AnnotationType.EQUATION
Description: This equation calculates the energy overhead from control packets required to set up the path for a payload packet. It depends on the total size of control packets, the number of hops, and the energy for the router's control unit to make decisions. Parameters are: 'E*oeeo' (energy for 1-bit OE/EO conversion), 'L_ctrl' (total size of control packets), 'h' (number of hops), and 'E_cu' (average energy for the control unit to make a decision).
Equation: E*{ctrl} = E*{oeeo} L*{ctrl} \cdot h + E\_{cu} \cdot (h+1)
Tags: equation, power_consumption, energy_efficiency
Reference: Gu, H., Xu, J., & Zhang, W. (2009). A Low-Power Fat Tree-based Optical Network-on-Chip for Multiprocessor System-on-Chip. 2009 Design, Automation & Test in Europe Conference & Exhibition.

**Annotation 8** (Page 5):
Type: AnnotationType.PARAMETER
Description: The power consumption of a single microresonator when it is in the 'on-state' (actively routing an optical signal). This value is used in the power consumption model for the FONOC.
Parameter: P_mr = 2e-05 W
Tags: parameter, power_consumption
Reference: Gu, H., Xu, J., & Zhang, W. (2009). A Low-Power Fat Tree-based Optical Network-on-Chip for Multiprocessor System-on-Chip. 2009 Design, Automation & Test in Europe Conference & Exhibition.

**Annotation 9** (Page 5):
Type: AnnotationType.PARAMETER
Description: The energy consumed for a single 1-bit optical-to-electronic (OE) and electronic-to-optical (EO) conversion when interfacing with 45nm CMOS circuits. This is a key parameter in the power model.
Parameter: E_oeeo = 1e-12 J/bit
Tags: parameter, power_consumption
Reference: Gu, H., Xu, J., & Zhang, W. (2009). A Low-Power Fat Tree-based Optical Network-on-Chip for Multiprocessor System-on-Chip. 2009 Design, Automation & Test in Europe Conference & Exhibition.

**Annotation 10** (Page 5):
Type: AnnotationType.PARAMETER
Description: The data rate at the interfaces of both the FONOC and the matched electronic NoC. This value is used in performance and power consumption calculations.
Parameter: R = 12500000000.0 bps
Tags: parameter, simulation_condition
Reference: Gu, H., Xu, J., & Zhang, W. (2009). A Low-Power Fat Tree-based Optical Network-on-Chip for Multiprocessor System-on-Chip. 2009 Design, Automation & Test in Europe Conference & Exhibition.

**Annotation 11** (Page 5):
Type: AnnotationType.PARAMETER
Description: The optical power loss incurred when an optical signal crosses a waveguide.
Parameter: Waveguide crossing insertion loss = 0.12 dB
Tags: parameter, optical_power_loss
Reference: Gu, H., Xu, J., & Zhang, W. (2009). A Low-Power Fat Tree-based Optical Network-on-Chip for Multiprocessor System-on-Chip. 2009 Design, Automation & Test in Europe Conference & Exhibition.

**Annotation 12** (Page 5):
Type: AnnotationType.PARAMETER
Description: The optical power loss incurred when an optical signal passes through a microresonator, which is a fundamental component of the optical routers.
Parameter: Microresonator insertion loss = 0.5 dB
Tags: parameter, optical_power_loss
Reference: Gu, H., Xu, J., & Zhang, W. (2009). A Low-Power Fat Tree-based Optical Network-on-Chip for Mul

tiprocessor System-on-Chip. 2009 Design, Automation & Test in Europe Conference & Exhibition.

**Annotation 13** (Page 5):
Type: AnnotationType.TEXT
Description: The network performance simulations for Figure 7 were conducted for a 64-core MPSoC. The OPNET network simulator was used. Processors generate packets independently with time intervals following a negative exponential distribution. The simulation employed a uniform traffic pattern, where each processor sends packets to all other processors with equal probability. A moderate interconnect bandwidth of 12.5 Gbps was assumed.
Tags: simulation_condition, methodology, results
Reference: Gu, H., Xu, J., & Zhang, W. (2009). A Low-Power Fat Tree-based Optical Network-on-Chip for Multiprocessor System-on-Chip. 2009 Design, Automation & Test in Europe Conference & Exhibition.

**Annotation 14** (Page 5):
Type: AnnotationType.FIGURE_DESCRIPTION
Description: Figure 7 illustrates the end-to-end (ETE) delay and network throughput of the FONOC for a 64-core MPSoC under various offered loads and for different packet sizes (32, 64, 128, 256, and 512 bytes). The delay remains low before the network saturates, after which it increases sharply. Larger packet sizes lead to higher saturation loads and consequently better throughput, because fewer control packets are needed for the same amount of data, reducing network contention during path setup.
Tags: results, figure_description, latency, throughput
Reference: Gu, H., Xu, J., & Zhang, W. (2009). A Low-Power Fat Tree-based Optical Network-on-Chip for Multiprocessor System-on-Chip. 2009 Design, Automation & Test in Europe Conference & Exhibition.
