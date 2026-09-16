## Case 2: Show All Available PDK Components

### User Query
Show all AMF O-band PDK components

### Tool Action
```
Called: get_pdk_info
Parameters: {
  "pdk_type": "amf.oband"
}
```

Tool response (Raw JSON)
```
{
  "pdk_type": "amf.oband",
  "cross_sections": [
    {
      "name": "strip",
      "parameters": [
        {"name": "wl0", "unit": "micrometer", "bounds": ["-inf", "inf"], "default": 1.31},
        {"name": "neff", "unit": "dimensionless", "bounds": ["-inf", "inf"], "default": 2.5682},
        {"name": "ng", "unit": "dimensionless", "bounds": ["-inf", "inf"], "default": 4.3077}
      ]
    },
    {
      "name": "rib",
      "parameters": [
        {"name": "wl0", "unit": "micrometer", "bounds": ["-inf", "inf"], "default": 1.31},
        {"name": "neff", "unit": "dimensionless", "bounds": ["-inf", "inf"], "default": 2.6971},
        {"name": "ng", "unit": "dimensionless", "bounds": ["-inf", "inf"], "default": 3.9969}
      ]
    },
    {
      "name": "nitride",
      "parameters": [
        {"name": "wl0", "unit": "micrometer", "bounds": ["-inf", "inf"], "default": 1.31},
        {"name": "neff", "unit": "dimensionless", "bounds": ["-inf", "inf"], "default": 1.6485},
        {"name": "ng", "unit": "dimensionless", "bounds": ["-inf", "inf"], "default": 2.0519}
      ]
    }
  ],
  "components": [
    {
      "name": "bend_s",
      "description": "An S-shaped waveguide bend for lateral offset and alignment, strip cross-section.",
      "cross_section": "strip",
      "tunable_parameters": [{"name": "size", "unit": "micrometer", "bounds": [0, "inf"], "default": [11, 1.8]}],
      "fixed_parameters": [],
      "optimizable_parameters": [{"name": "size", "unit": "micrometer", "bounds": [0, "inf"], "default": [11, 1.8]}]
    },
    {
      "name": "bend_s",
      "description": "An S-shaped waveguide bend for lateral offset and alignment, rib cross-section.",
      "cross_section": "rib",
      "tunable_parameters": [{"name": "size", "unit": "micrometer", "bounds": [0, "inf"], "default": [17, 1.8]}],
      "fixed_parameters": [],
      "optimizable_parameters": [{"name": "size", "unit": "micrometer", "bounds": [0, "inf"], "default": [17, 1.8]}]
    },
    {
      "name": "bend_s",
      "description": "An S-shaped waveguide bend for lateral offset and alignment, nitride cross-section.",
      "cross_section": "nitride",
      "tunable_parameters": [{"name": "size", "unit": "micrometer", "bounds": [0, "inf"], "default": [22, 3.6]}],
      "fixed_parameters": [],
      "optimizable_parameters": [{"name": "size", "unit": "micrometer", "bounds": [0, "inf"], "default": [22, 3.6]}]
    },
    {
      "name": "bend_euler",
      "description": "An Euler 90 degree bend, strip cross-section.",
      "cross_section": "strip",
      "tunable_parameters": [{"name": "radius", "unit": "micrometer", "bounds": [5, "inf"], "default": 5}],
      "fixed_parameters": [{"name": "angle", "unit": "degree", "bounds": ["-inf", "inf"], "default": 90}],
      "optimizable_parameters": [{"name": "radius", "unit": "micrometer", "bounds": [5, "inf"], "default": 5}]
    },
    {
      "name": "bend_euler",
      "description": "An Euler 90 degree bend, rib cross-section.",
      "cross_section": "rib",
      "tunable_parameters": [{"name": "radius", "unit": "micrometer", "bounds": [20, "inf"], "default": 20}],
      "fixed_parameters": [{"name": "angle", "unit": "degree", "bounds": ["-inf", "inf"], "default": 90}],
      "optimizable_parameters": [{"name": "radius", "unit": "micrometer", "bounds": [20, "inf"], "default": 20}]
    },
    {
      "name": "bend_euler",
      "description": "An Euler 90 degree bend, rib cross-section.",
      "cross_section": "nitride",
      "tunable_parameters": [{"name": "radius", "unit": "micrometer", "bounds": [20, "inf"], "default": 25}],
      "fixed_parameters": [{"name": "angle", "unit": "degree", "bounds": ["-inf", "inf"], "default": 90}],
      "optimizable_parameters": [{"name": "radius", "unit": "micrometer", "bounds": [20, "inf"], "default": 25}]
    },
    ...
  ],
  "circuit_library": [
    {
      "name": "crow_filter",
      "description": "A CROW filter.\n- num_rings (int): number of rings\n- lengths_x (list[num_rings + 1]): lengths of the couplers\n- lengths_y (list[num_rings]): lengths of the straights\n",
      "cross_section": null,
      "tunable_parameters": [
        {"name": "num_rings", "unit": "dimensionless", "bounds": [1, "inf"], "default": 1},
        {"name": "lengths_x", "unit": "micrometer", "bounds": [0, "inf"], "default": null},
        {"name": "lengths_y", "unit": "micrometer", "bounds": [0, "inf"], "default": null}
      ],
      "fixed_parameters": [],
      "optimizable_parameters": [
        {"name": "length_x_0", "unit": "micrometer", "bounds": [0, "inf"], "default": 30},
        {"name": "length_x_1", "unit": "micrometer", "bounds": [0, "inf"], "default": 30},
        {"name": "length_y_0", "unit": "micrometer", "bounds": [0, "inf"], "default": 40}
      ]
    },
    {
      "name": "mzi_lattice_filter",
      "description": "An MZI lattice filter.\n- num_stages (int): number of stages ...",
      "cross_section": null,
      "tunable_parameters": [...],
      "fixed_parameters": [],
      "optimizable_parameters": [...]
    },
    {
      "name": "rings_single_in_series",
      "description": "A series of num_rings single bus rings connected ...",
      "cross_section": null,
      "tunable_parameters": [...],
      "fixed_parameters": [],
      "optimizable_parameters": [...]
    },
    {
      "name": "wdm_rings",
      "description": "A series of num_rings double bus rings connected ...",
      "cross_section": null,
      "tunable_parameters": [...],
      "fixed_parameters": [],
      "optimizable_parameters": [...]
    }
  ]
}

```

### Final Rendered Response to User

Here are all the available components in the AMF O-band PDK:

#### Cross-Sections
The PDK supports three different cross-sections:
- strip - Standard strip waveguide
- rib - Rib waveguide
- nitride - Silicon nitride waveguide
#### Basic Components
- Waveguides
  - straight - Straight waveguide (available in strip, rib, nitride)
  - bend_s - S-shaped waveguide bend for lateral offset and alignment (available in strip, rib, nitride)
  - bend_euler - Euler 90-degree bend (available in strip, rib, nitride)
  - taper - Linear taper (available in strip, rib, nitride)
  
- Couplers
  - coupler - Symmetric coupler (available in strip, rib, nitride)
  - coupler_ring - Ring coupler (strip cross-section only)
  
- Resonators
  - ring_single - Single bus ring resonator (strip cross-section)
  - ring_double - Double bus ring resonator (strip cross-section)
  
- Complex Components
  - mzi - Mach-Zehnder Interferometer (available in strip, rib, nitride)
  - spiral - Spiral waveguide (available in strip, rib, nitride)
#### AMF-Specific Components
- Grating Couplers
  - AMF_PSOI_SiGC1D_Oband_v3p0 - Grating coupler with silicon
  - AMF_SOI_GC1D_Oband_v3p0 - Standard grating coupler
  - AMF_DCI_PSOI_PSiNGC1D1_Oband_preview - Grating coupler with silicon nitride

- Edge Couplers
  - AMF_DCI_PSOI_Si1X2MMI_Oband_v3p0 - 1×2 MMI edge coupler
  - AMF_DCI_PSOI_Si2X2MMI_Oband_v3p1 - 2×2 MMI edge coupler

- Other Components
  - AMF_SOI_Crossing_Oband_v3p0 - Waveguide crossing
#### Circuit Library (Advanced Components)
- Filters
  - crow_filter - Coupled Resonator Optical Waveguide (CROW) filter
  - mzi_lattice_filter - MZI lattice filter

- Ring Arrays
  - rings_single_in_series - Series of single bus rings
  - wdm_rings - Wavelength division multiplexing ring array
#### Key Features
- Wavelength: Optimized for O-band (1310 nm)
- Cross-sections: Strip, rib, and nitride options
- Tunable parameters: Most components have configurable dimensions
- Optimizable parameters: Components support optimization for specific applications
- AMF-specific: Includes specialized AMF components for grating couplers, edge couplers, and crossings

The PDK provides a comprehensive set of components for designing photonic integrated circuits in the O-band wavelength range using AMF's fabrication process.
