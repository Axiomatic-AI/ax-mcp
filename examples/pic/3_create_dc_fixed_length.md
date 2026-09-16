## Case 3: Directional coupler of a fixed length

### User Query
Create a directional coupler with a coupling length of 20 um using CSPDK O-band


### Tool Action
```
Called: list_available_pdks
Parameters: {}
```

Tool Response (Raw JSON)
```
{
  "pdks": [
    {
      "pdk_type": "cspdk.si220.cband",
      "description": "Cornerstone PDK on platform Si220 for C-band",
      "granted": true
    },
    {
      "pdk_type": "cspdk.si220.oband",
      "description": "Cornerstone PDK on platform Si220 for O-band",
      "granted": true
    },
    {
      "pdk_type": "amf.cband",
      "description": "AMF PDK for C-band",
      "granted": true
    },
    {
      "pdk_type": "amf.oband",
      "description": "AMF PDK for O-band",
      "granted": true
    }
```
### Tool Action
```
Called: get_pdk_info
Parameters: {
  "pdk_type": "cspdk.si220.oband"
}
```
Tool Response (Raw JSON)
```
{
  "pdk_type": "cspdk.si220.oband",
  "cross_sections": [
    {
      "name": "strip",
      "parameters": [
        {
          "name": "wl0",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 1.31
        },
        {
          "name": "neff",
          "unit": "dimensionless",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 2.52
        },
        {
          "name": "ng",
          "unit": "dimensionless",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 4.33
        }
      ]
    },
    {
      "name": "rib",
      "parameters": [
        {
          "name": "wl0",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 1.31
        },
        {
          "name": "neff",
          "unit": "dimensionless",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 2.72
        },
        {
          "name": "ng",
          "unit": "dimensionless",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 3.98
        }
      ]
    }
  ],
  "components": [
    {
      "name": "bend_s",
      "description": "An S-shaped waveguide bend for lateral offset and alignment, strip cross-section.",
      "cross_section": "strip",
      "tunable_parameters": [
        {
          "name": "size",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": [
            11,
            1.8
          ]
        }
      ],
      "fixed_parameters": [],
      "optimizable_parameters": [
        {
          "name": "size",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": [
            11,
            1.8
          ]
        }
      ]
    },
    {
      "name": "bend_s",
      "description": "An S-shaped waveguide bend for lateral offset and alignment, rib cross-section.",
      "cross_section": "rib",
      "tunable_parameters": [
        {
          "name": "size",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": [
            17,
            1.8
          ]
        }
      ],
      "fixed_parameters": [],
      "optimizable_parameters": [
        {
          "name": "size",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": [
            17,
            1.8
          ]
        }
      ]
    },
    {
      "name": "bend_euler",
      "description": "An Euler 90 degree bend, strip cross-section.",
      "cross_section": "strip",
      "tunable_parameters": [
        {
          "name": "radius",
          "unit": "micrometer",
          "bounds": [
            5,
            "inf"
          ],
          "default": 5
        }
      ],
      "fixed_parameters": [
        {
          "name": "angle",
          "unit": "degree",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 90
        }
      ],
      "optimizable_parameters": [
        {
          "name": "radius",
          "unit": "micrometer",
          "bounds": [
            5,
            "inf"
          ],
          "default": 5
        }
      ]
    },
    {
      "name": "bend_euler",
      "description": "An Euler 90 degree bend, rib cross-section.",
      "cross_section": "rib",
      "tunable_parameters": [
        {
          "name": "radius",
          "unit": "micrometer",
          "bounds": [
            25,
            "inf"
          ],
          "default": 25
        }
      ],
      "fixed_parameters": [
        {
          "name": "angle",
          "unit": "degree",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 90
        }
      ],
      "optimizable_parameters": [
        {
          "name": "radius",
          "unit": "micrometer",
          "bounds": [
            25,
            "inf"
          ],
          "default": 25
        }
      ]
    },
    {
      "name": "coupler",
      "description": "A symmetric coupler in a strip cross-section.",
      "cross_section": "strip",
      "tunable_parameters": [
        {
          "name": "length",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 20
        }
      ],
      "fixed_parameters": [
        {
          "name": "gap",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 0.27
        }
      ],
      "optimizable_parameters": [
        {
          "name": "length",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 20
        }
      ]
    },
    {
      "name": "coupler_rib",
      "description": "A symmetric coupler in a rib cross-section.",
      "cross_section": "rib",
      "tunable_parameters": [
        {
          "name": "length",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 20
        }
      ],
      "fixed_parameters": [
        {
          "name": "gap",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 0.27
        }
      ],
      "optimizable_parameters": [
        {
          "name": "length",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 20
        }
      ]
    },
    {
      "name": "coupler_ring",
      "description": "A ring coupler in a strip cross-section.",
      "cross_section": "strip",
      "tunable_parameters": [
        {
          "name": "length_x",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 4
        },
        {
          "name": "radius",
          "unit": "micrometer",
          "bounds": [
            5,
            "inf"
          ],
          "default": 5
        }
      ],
      "fixed_parameters": [
        {
          "name": "gap",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 0.27
        }
      ],
      "optimizable_parameters": [
        {
          "name": "length_x",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 4
        },
        {
          "name": "radius",
          "unit": "micrometer",
          "bounds": [
            5,
            "inf"
          ],
          "default": 5
        }
      ]
    },
    {
      "name": "grating_coupler_rectangular",
      "description": "A grating coupler in a strip cross-section.",
      "cross_section": "strip",
      "tunable_parameters": [],
      "fixed_parameters": [
        {
          "name": "period",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 0.5
        },
        {
          "name": "n_periods",
          "unit": "dimensionless",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 60
        },
        {
          "name": "length_taper",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 350
        }
      ],
      "optimizable_parameters": []
    },
    {
      "name": "grating_coupler_rectangular",
      "description": "A grating coupler in a rib cross-section.",
      "cross_section": "rib",
      "tunable_parameters": [],
      "fixed_parameters": [
        {
          "name": "period",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 0.5
        },
        {
          "name": "n_periods",
          "unit": "dimensionless",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 60
        },
        {
          "name": "length_taper",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 350
        }
      ],
      "optimizable_parameters": []
    },
    {
      "name": "grating_coupler_elliptical",
      "description": "A grating coupler in a strip cross-section.",
      "cross_section": "strip",
      "tunable_parameters": [],
      "fixed_parameters": [
        {
          "name": "grating_line_width",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 0.315
        }
      ],
      "optimizable_parameters": []
    },
    {
      "name": "grating_coupler_elliptical",
      "description": "A grating coupler in a rib cross-section.",
      "cross_section": "rib",
      "tunable_parameters": [],
      "fixed_parameters": [
        {
          "name": "grating_line_width",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 0.315
        }
      ],
      "optimizable_parameters": []
    },
    {
      "name": "mmi1x2",
      "description": "A 1x2 MMI coupler in a strip cross-section.",
      "cross_section": "strip",
      "tunable_parameters": [],
      "fixed_parameters": [
        {
          "name": "width_taper",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 1.5
        },
        {
          "name": "length_taper",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 20
        },
        {
          "name": "length_mmi",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 40
        },
        {
          "name": "width_mmi",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 6
        },
        {
          "name": "gap_mmi",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 1.64
        }
      ],
      "optimizable_parameters": []
    },
    {
      "name": "mmi1x2",
      "description": "A 1x2 MMI coupler in a rib cross-section.",
      "cross_section": "rib",
      "tunable_parameters": [],
      "fixed_parameters": [
        {
          "name": "width_taper",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 1.5
        },
        {
          "name": "length_taper",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 20
        },
        {
          "name": "length_mmi",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 40.8
        },
        {
          "name": "width_mmi",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 6
        },
        {
          "name": "gap_mmi",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 1.55
        }
      ],
      "optimizable_parameters": []
    },
    {
      "name": "mmi2x2",
      "description": "A 2x2 MMI coupler in a strip cross-section.",
      "cross_section": "strip",
      "tunable_parameters": [],
      "fixed_parameters": [
        {
          "name": "width_taper",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 1.5
        },
        {
          "name": "length_taper",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 20
        },
        {
          "name": "length_mmi",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 53.5
        },
        {
          "name": "width_mmi",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 6
        },
        {
          "name": "gap_mmi",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 0.53
        }
      ],
      "optimizable_parameters": []
    },
    {
      "name": "mmi2x2",
      "description": "A 2x2 MMI coupler in a rib cross-section.",
      "cross_section": "rib",
      "tunable_parameters": [],
      "fixed_parameters": [
        {
          "name": "width_taper",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 1.5
        },
        {
          "name": "length_taper",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 20
        },
        {
          "name": "length_mmi",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 55
        },
        {
          "name": "width_mmi",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 6
        },
        {
          "name": "gap_mmi",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 0.53
        }
      ],
      "optimizable_parameters": []
    },
    {
      "name": "mzi",
      "description": "A Mach-Zehnder Interferometer in strip cross-section.",
      "cross_section": "strip",
      "tunable_parameters": [
        {
          "name": "delta_length",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        }
      ],
      "fixed_parameters": [],
      "optimizable_parameters": [
        {
          "name": "delta_length",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        }
      ]
    },
    {
      "name": "ring_single",
      "description": "A single bus ring resonator in a strip cross-section.",
      "cross_section": "strip",
      "tunable_parameters": [
        {
          "name": "radius",
          "unit": "micrometer",
          "bounds": [
            5,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "length_x",
          "unit": "micrometer",
          "bounds": [
            0.01,
            "inf"
          ],
          "default": 4
        },
        {
          "name": "length_y",
          "unit": "micrometer",
          "bounds": [
            0.01,
            "inf"
          ],
          "default": 0.6
        }
      ],
      "fixed_parameters": [
        {
          "name": "gap",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 0.27
        }
      ],
      "optimizable_parameters": [
        {
          "name": "radius",
          "unit": "micrometer",
          "bounds": [
            5,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "length_x",
          "unit": "micrometer",
          "bounds": [
            0.01,
            "inf"
          ],
          "default": 4
        },
        {
          "name": "length_y",
          "unit": "micrometer",
          "bounds": [
            0.01,
            "inf"
          ],
          "default": 0.6
        }
      ]
    },
    {
      "name": "ring_double",
      "description": "A double bus ring resonator in a strip cross-section.",
      "cross_section": "strip",
      "tunable_parameters": [
        {
          "name": "radius",
          "unit": "micrometer",
          "bounds": [
            5,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "length_x",
          "unit": "micrometer",
          "bounds": [
            0.01,
            "inf"
          ],
          "default": 0.01
        },
        {
          "name": "length_y",
          "unit": "micrometer",
          "bounds": [
            0.01,
            "inf"
          ],
          "default": 0.01
        }
      ],
      "fixed_parameters": [
        {
          "name": "gap",
          "unit": "micrometer",
          "bounds": [
            "-inf",
            "inf"
          ],
          "default": 0.27
        }
      ],
      "optimizable_parameters": [
        {
          "name": "radius",
          "unit": "micrometer",
          "bounds": [
            5,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "length_x",
          "unit": "micrometer",
          "bounds": [
            0.01,
            "inf"
          ],
          "default": 0.01
        },
        {
          "name": "length_y",
          "unit": "micrometer",
          "bounds": [
            0.01,
            "inf"
          ],
          "default": 0.01
        }
      ]
    },
    {
      "name": "straight",
      "description": "A straight waveguide in a strip cross-section.",
      "cross_section": "strip",
      "tunable_parameters": [
        {
          "name": "length",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        }
      ],
      "fixed_parameters": [],
      "optimizable_parameters": [
        {
          "name": "length",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        }
      ]
    },
    {
      "name": "straight_rib",
      "description": "A straight waveguide in a rib cross-section.",
      "cross_section": "rib",
      "tunable_parameters": [
        {
          "name": "length",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        }
      ],
      "fixed_parameters": [],
      "optimizable_parameters": [
        {
          "name": "length",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        }
      ]
    },
    {
      "name": "taper",
      "description": "A linear taper in a strip cross-section.",
      "cross_section": "strip",
      "tunable_parameters": [
        {
          "name": "length",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "width1",
          "unit": "micrometer",
          "bounds": [
            0.45,
            "inf"
          ],
          "default": 0.45
        },
        {
          "name": "width2",
          "unit": "micrometer",
          "bounds": [
            0.45,
            "inf"
          ],
          "default": 0.45
        }
      ],
      "fixed_parameters": [],
      "optimizable_parameters": [
        {
          "name": "length",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "width1",
          "unit": "micrometer",
          "bounds": [
            0.45,
            "inf"
          ],
          "default": 0.45
        },
        {
          "name": "width2",
          "unit": "micrometer",
          "bounds": [
            0.45,
            "inf"
          ],
          "default": 0.45
        }
      ]
    },
    {
      "name": "taper",
      "description": "A linear taper in a rib cross-section.",
      "cross_section": "rib",
      "tunable_parameters": [
        {
          "name": "length",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "width1",
          "unit": "micrometer",
          "bounds": [
            0.45,
            "inf"
          ],
          "default": 0.45
        },
        {
          "name": "width2",
          "unit": "micrometer",
          "bounds": [
            0.45,
            "inf"
          ],
          "default": 0.45
        }
      ],
      "fixed_parameters": [],
      "optimizable_parameters": [
        {
          "name": "length",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "width1",
          "unit": "micrometer",
          "bounds": [
            0.45,
            "inf"
          ],
          "default": 0.45
        },
        {
          "name": "width2",
          "unit": "micrometer",
          "bounds": [
            0.45,
            "inf"
          ],
          "default": 0.45
        }
      ]
    }
  ],
  "circuit_library": [
    {
      "name": "crow_filter",
      "description": "A CROW filter.\n- num_rings (int): number of rings\n- lengths_x (list[num_rings + 1]): lengths of the couplers\n- lengths_y (list[num_rings]): lengths of the straights\n",
      "cross_section": null,
      "tunable_parameters": [
        {
          "name": "num_rings",
          "unit": "dimensionless",
          "bounds": [
            1,
            "inf"
          ],
          "default": 1
        },
        {
          "name": "lengths_x",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": null
        },
        {
          "name": "lengths_y",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": null
        }
      ],
      "fixed_parameters": [],
      "optimizable_parameters": [
        {
          "name": "length_x_0",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 30
        },
        {
          "name": "length_x_1",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 30
        },
        {
          "name": "length_y_0",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 40
        }
      ]
    },
    {
      "name": "mzi_lattice_filter",
      "description": "An MZI lattice filter.\n- num_stages (int): number of stages of the mzi lattice, that is, the total number of mzis cascaded in the lattice filter, the number of couplers is one more than number of stages\n- spacing (float): spacing between the couplers\n- delta_lengths (list[num_stages]): difference in length between the two arms between each pair of consecutive couplers\n- coupling_lengths (list[num_stages+1]): lengths of the couplers\n",
      "cross_section": null,
      "tunable_parameters": [
        {
          "name": "num_stages",
          "unit": "dimensionless",
          "bounds": [
            1,
            "inf"
          ],
          "default": 1
        },
        {
          "name": "spacing",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 100
        },
        {
          "name": "delta_lengths",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": null
        },
        {
          "name": "coupling_lengths",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": null
        }
      ],
      "fixed_parameters": [],
      "optimizable_parameters": [
        {
          "name": "delta_length_0",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "coupling_length_0",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "coupling_length_1",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        }
      ]
    },
    {
      "name": "rings_single_in_series",
      "description": "A series of num_rings single bus rings connected to a bus waveguide and spaced uniformly.\n- num_rings (int): number of rings\n- spacing (float): spacing between the rings\n- lengths_x (list[num_rings]): lengths of the rings\n- lengths_y (list[num_rings]): lengths of the rings\n- radii (list[num_rings]): radii of the rings\n",
      "cross_section": null,
      "tunable_parameters": [
        {
          "name": "num_rings",
          "unit": "dimensionless",
          "bounds": [
            1,
            "inf"
          ],
          "default": 3
        },
        {
          "name": "spacing",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 150
        },
        {
          "name": "lengths_x",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": null
        },
        {
          "name": "lengths_y",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": null
        },
        {
          "name": "radii",
          "unit": "micrometer",
          "bounds": [
            5,
            "inf"
          ],
          "default": null
        }
      ],
      "fixed_parameters": [],
      "optimizable_parameters": [
        {
          "name": "length_x_0",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "length_x_1",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "length_x_2",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "length_y_0",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "length_y_1",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "length_y_2",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "radius_0",
          "unit": "micrometer",
          "bounds": [
            5,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "radius_1",
          "unit": "micrometer",
          "bounds": [
            5,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "radius_2",
          "unit": "micrometer",
          "bounds": [
            5,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "spacing",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 150
        }
      ]
    },
    {
      "name": "splitter_1xn",
      "description": "A cell representing a splitter that goes from 1 output to n_outputs based on a tree of mmi1x2.\n- n_outputs (int): number of outputs\n- x_spacing (float): horizontal spacing between the outputs\n- y_spacing (float): vertical spacing between the outputs\n",
      "cross_section": null,
      "tunable_parameters": [
        {
          "name": "n_outputs",
          "unit": "dimensionless",
          "bounds": [
            2,
            "inf"
          ],
          "default": 4
        },
        {
          "name": "x_spacing",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 50
        },
        {
          "name": "y_spacing",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 50
        }
      ],
      "fixed_parameters": [],
      "optimizable_parameters": []
    },
    {
      "name": "wdm_rings",
      "description": "A series of num_rings double bus rings connected to a bus waveguide and spaced uniformly.",
      "cross_section": null,
      "tunable_parameters": [
        {
          "name": "num_rings",
          "unit": "dimensionless",
          "bounds": [
            1,
            "inf"
          ],
          "default": 3
        },
        {
          "name": "spacing",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 150
        },
        {
          "name": "lengths_x",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": null
        },
        {
          "name": "lengths_y",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": null
        },
        {
          "name": "radii",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": null
        },
        {
          "name": "alternate_mirror",
          "unit": "dimensionless",
          "bounds": [
            0,
            1
          ],
          "default": null
        }
      ],
      "fixed_parameters": [],
      "optimizable_parameters": [
        {
          "name": "length_x_0",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "length_x_1",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "length_x_2",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "length_y_0",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "length_y_1",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "length_y_2",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "radius_0",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "radius_1",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "radius_2",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 10
        },
        {
          "name": "spacing",
          "unit": "micrometer",
          "bounds": [
            0,
            "inf"
          ],
          "default": 150
        }
      ]
    }
  ]
}
```
### Tool Action
```
Called: design_circuit
Parameters: {
  "query": "Create a directional coupler with a coupling length of 20 um using CSPDK O-band",
  "pdk_type": "cspdk.si220.oband",
  "output_path": "C:\\Users\\aitor\\Desktop\\repos\\test-mcp"
}
```

Tool Response (Raw JSON)
```
{
  "circuit_file_path": "C:\\Users\\aitor\\Desktop\\repos\\test-mcp\\circuit.py",
  "code": "import gdsfactory as gf\nimport cspdk.si220.oband\n\npdk = cspdk.si220.oband.get_pdk()\npdk.activate()\nc = gf.Component()\n\ncoupler = c << pdk.get_component(\"coupler\", length=20, gap=0.270)\ncoupler.move((-10.0, -0.335))\ncoupler.name = \"coupler\"\n\nc.add_port(\"in0\", port=coupler.ports[\"o1\"])\nc.add_port(\"in1\", port=coupler.ports[\"o2\"])\nc.add_port(\"out0\", port=coupler.ports[\"o3\"])\nc.add_port(\"out1\", port=coupler.ports[\"o4\"])\n\nc\n",
  "statements_file_path": "C:\\Users\\aitor\\Desktop\\repos\\test-mcp\\statements.json",
  "statements": {
    "statements": [
      {
        "type": "PARAMETER_CONSTRAINT",
        "text": "The circuit contains a 'coupler'",
        "formalization": {
          "code": "n_coupler == 1",
          "default_tolerance": 0.05,
          "mapping": {
            "n_coupler": {
              "name": "number_of_instances",
              "arguments": {
                "component": "coupler"
              }
            }
          }
        },
        "validation": null
      },
      {
        "type": "PARAMETER_CONSTRAINT",
        "text": "The 'length' of all 'coupler' is 20 um",
        "formalization": {
          "code": "length_coupler == 20",
          "default_tolerance": 0.05,
          "mapping": {
            "length_coupler": {
              "name": "parameter",
              "arguments": {
                "component_path": "coupler,length"
              }
            }
          }
        },
        "validation": null
      }
    ]
  }
}

```
### Tool Action
```
Called: simulate_circuit
Parameters: {
  "file_path": "C:\\Users\\aitor\\Desktop\\repos\\test-mcp\\circuit.py"
}
```
Tool Response
Creation of .ipynb notebook path

### Final Rendered Response to User

#### Circuit Design
The directional coupler was designed using the cspdk.si220.oband PDK with the following specifications:
- Coupling length: 20 µm (as requested)
- Gap: 0.27 µm (default for the O-band PDK)
- Cross-section: Strip waveguide
- Ports: Four ports (in0, in1, out0, out1) for full directional coupler functionality
#### Generated Files
- circuit.py - Contains the Python code to generate the directional coupler using gdsfactory and the CSPDK O-band PDK
```
import gdsfactory as gf
import cspdk.si220.oband

pdk = cspdk.si220.oband.get_pdk()
pdk.activate()
c = gf.Component()

coupler = c << pdk.get_component("coupler", length=20, gap=0.270)
coupler.move((-10.0, -0.335))
coupler.name = "coupler"

c.add_port("in0", port=coupler.ports["o1"])
c.add_port("in1", port=coupler.ports["o2"])
c.add_port("out0", port=coupler.ports["o3"])
c.add_port("out1", port=coupler.ports["o4"])

c
```
<img width="786" height="597" alt="image" src="https://github.com/user-attachments/assets/f1d9f4e9-f970-4da8-b775-928ec353c613" />

- statements.json - Contains formalized statements about the circuit parameters and constraints
```
{
    "statements": [
        {
            "type": "PARAMETER_CONSTRAINT",
            "text": "The circuit contains a 'coupler'",
            "formalization": {
                "code": "n_coupler == 1",
                "default_tolerance": 0.05,
                "mapping": {
                    "n_coupler": {
                        "name": "number_of_instances",
                        "arguments": {
                            "component": "coupler"
                        }
                    }
                }
            },
            "validation": null
        },
        {
            "type": "PARAMETER_CONSTRAINT",
            "text": "The 'length' of all 'coupler' is 20 um",
            "formalization": {
                "code": "length_coupler == 20",
                "default_tolerance": 0.05,
                "mapping": {
                    "length_coupler": {
                        "name": "parameter",
                        "arguments": {
                            "component_path": "coupler,length"
                        }
                    }
                }
            },
            "validation": null
        }
    ]
}
```
- circuit_simulation.ipynb - Interactive Jupyter notebook with simulation results and plots
<img width="1134" height="379" alt="image" src="https://github.com/user-attachments/assets/928ffa89-cb5e-4fb3-8ac3-85a31af71ec0" />

#### Simulation Results
The circuit was simulated across the O-band wavelength range (1.125-1.375 µm) and shows the expected directional coupler behavior:
- Through port (in0→out0, in1→out1): Shows increasing transmission with wavelength
- Cross port (in0→out1, in1→out0): Shows decreasing transmission with wavelength
- The coupling behavior is wavelength-dependent, which is typical for directional couplers

The simulation results are presented in an interactive Jupyter notebook with:
- Linear and logarithmic scale options
- Interactive plots showing transmission vs. wavelength
- All four port-to-port transmission paths
- Zoom and pan capabilities for detailed analysis
The directional coupler is now ready for use in your photonic circuit design!

