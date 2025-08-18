"""PIC (Photonic Integrated Circuit) domain MCP server."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ...shared import (
    AxiomaticAPIClient,
    AxiomaticAPIConfig,
    BaseConfig,
    BaseServer,
)


class PICConfig(BaseConfig):
    """Configuration for PIC domain server."""
    
    api_url: str = Field(
        default="https://api.axiomatic.ai",
        description="Axiomatic API URL"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="Axiomatic API key"
    )
    default_wavelength: float = Field(
        default=1550.0,
        description="Default wavelength in nm"
    )
    default_material: str = Field(
        default="silicon",
        description="Default material system"
    )


class PICDesignParams(BaseModel):
    """Parameters for PIC design."""
    
    components: List[Dict[str, Any]] = Field(
        ...,
        description="List of photonic components to include"
    )
    connections: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Connections between components"
    )
    optimization_goals: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Design optimization objectives"
    )
    constraints: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Design constraints"
    )
    wavelength: Optional[float] = Field(
        default=None,
        description="Operating wavelength in nm"
    )
    material: Optional[str] = Field(
        default=None,
        description="Material system (silicon, inp, sin)"
    )


class ComponentLibraryParams(BaseModel):
    """Parameters for querying component library."""
    
    component_type: Optional[str] = Field(
        default=None,
        description="Type of component to search for"
    )
    material: Optional[str] = Field(
        default=None,
        description="Material system filter"
    )
    wavelength_range: Optional[List[float]] = Field(
        default=None,
        description="Wavelength range [min, max] in nm"
    )


class PICServer(BaseServer[PICConfig]):
    """Server for PIC domain operations."""
    
    def __init__(self):
        """Initialize PIC server."""
        super().__init__(
            name="axiomatic-pic",
            version="1.0.0",
            description="Photonic Integrated Circuit design and simulation MCP server",
            config_class=PICConfig,
        )
        self.api_client: Optional[AxiomaticAPIClient] = None
    
    def initialize(self, config_path=None):
        """Initialize server with API client."""
        super().initialize(config_path)
        
        # Initialize Axiomatic API client
        api_config = AxiomaticAPIConfig(
            base_url=self.config.api_url,
            api_key=self.config.api_key,
            timeout=self.config.timeout // 1000,  # Convert ms to seconds
            max_retries=self.config.max_retries,
        )
        self.api_client = AxiomaticAPIClient(api_config)
        self.logger.info("Axiomatic API client initialized")
    
    def setup_tools(self) -> None:
        """Setup PIC domain tools."""
        
        @self.mcp.tool()
        def design_pic(params: PICDesignParams) -> Dict[str, Any]:
            """
            Design a Photonic Integrated Circuit using the Axiomatic API.
            
            This tool takes component specifications and creates an optimized PIC layout.
            """
            self.logger.info("Starting PIC design process")
            
            # Build specification
            specification = {
                "components": params.components,
                "connections": params.connections or [],
                "wavelength": params.wavelength or self.config.default_wavelength,
                "material": params.material or self.config.default_material,
            }
            
            # Call Axiomatic API
            try:
                result = self.api_client.design_pic(
                    specification=specification,
                    optimization_goals=params.optimization_goals,
                    constraints=params.constraints,
                )
                
                self.logger.info(f"PIC design completed: {result.get('design_id')}")
                return result
                
            except Exception as e:
                self.logger.error(f"PIC design failed: {e}")
                raise
        
        @self.mcp.tool()
        def get_component_library(params: ComponentLibraryParams) -> Dict[str, Any]:
            """
            Get available photonic components from the library.
            
            Returns a list of components that can be used in PIC designs.
            """
            self.logger.debug("Fetching component library")
            
            # Fake component library for demonstration
            components = [
                {
                    "type": "grating_coupler",
                    "name": "GC1550",
                    "description": "Grating coupler optimized for 1550nm",
                    "parameters": {
                        "center_wavelength": 1550,
                        "bandwidth": 40,
                        "coupling_efficiency": 0.7,
                        "pitch": 0.63,
                        "duty_cycle": 0.5,
                    },
                    "material": "silicon",
                },
                {
                    "type": "mmi_coupler",
                    "name": "MMI_1x2",
                    "description": "1x2 Multi-mode interference coupler",
                    "parameters": {
                        "split_ratio": [0.5, 0.5],
                        "insertion_loss": 0.1,
                        "width": 12,
                        "length": 50,
                    },
                    "material": "silicon",
                },
                {
                    "type": "ring_resonator",
                    "name": "RR10",
                    "description": "10µm radius ring resonator",
                    "parameters": {
                        "radius": 10,
                        "fsr": 10,
                        "q_factor": 15000,
                        "coupling_gap": 0.2,
                    },
                    "material": "silicon",
                },
                {
                    "type": "phase_shifter",
                    "name": "PS_Thermal",
                    "description": "Thermal phase shifter",
                    "parameters": {
                        "length": 500,
                        "power_consumption": 20,
                        "response_time": 1,
                        "phase_shift_efficiency": 0.03,
                    },
                    "material": "silicon",
                },
                {
                    "type": "photodetector",
                    "name": "PD_Ge",
                    "description": "Germanium photodetector",
                    "parameters": {
                        "responsivity": 1.0,
                        "dark_current": 100,
                        "bandwidth": 50,
                        "active_area": [10, 10],
                    },
                    "material": "germanium",
                },
                {
                    "type": "modulator",
                    "name": "MZM_PN",
                    "description": "Mach-Zehnder modulator with PN junction",
                    "parameters": {
                        "vpi_l": 2,
                        "insertion_loss": 3,
                        "extinction_ratio": 30,
                        "bandwidth": 40,
                    },
                    "material": "silicon",
                },
            ]
            
            # Filter based on parameters
            filtered = components
            
            if params.component_type:
                filtered = [c for c in filtered if c["type"] == params.component_type]
            
            if params.material:
                filtered = [c for c in filtered if c["material"] == params.material]
            
            if params.wavelength_range and len(params.wavelength_range) == 2:
                min_wl, max_wl = params.wavelength_range
                filtered = [
                    c for c in filtered
                    if "center_wavelength" not in c["parameters"]
                    or (min_wl <= c["parameters"]["center_wavelength"] <= max_wl)
                ]
            
            self.logger.info(f"Found {len(filtered)} components matching criteria")
            
            return {
                "components": filtered,
                "total": len(filtered),
                "filters_applied": {
                    "type": params.component_type,
                    "material": params.material,
                    "wavelength_range": params.wavelength_range,
                },
            }
        
        @self.mcp.tool()
        def simulate_pic(
            design_id: str,
            simulation_type: str = "transmission",
            wavelength_start: float = 1540,
            wavelength_end: float = 1560,
            num_points: int = 100,
        ) -> Dict[str, Any]:
            """
            Simulate a PIC design to analyze its performance.
            
            Available simulation types: transmission, reflection, mode, thermal
            """
            self.logger.info(f"Starting {simulation_type} simulation for design {design_id}")
            
            simulation_params = {
                "wavelength_range": [wavelength_start, wavelength_end],
                "num_points": num_points,
            }
            
            try:
                result = self.api_client.simulate_pic(
                    design_id=design_id,
                    simulation_type=simulation_type,
                    parameters=simulation_params,
                )
                
                self.logger.info(f"Simulation completed: {result.get('simulation_id')}")
                return result
                
            except Exception as e:
                self.logger.error(f"Simulation failed: {e}")
                raise
        
        @self.mcp.tool()
        def optimize_pic_design(
            design_id: str,
            optimize_for: List[str],
            target_values: Optional[Dict[str, float]] = None,
        ) -> Dict[str, Any]:
            """
            Optimize an existing PIC design for specific performance metrics.
            
            Optimization targets: insertion_loss, crosstalk, bandwidth, footprint, power
            """
            self.logger.info(f"Optimizing design {design_id} for {optimize_for}")
            
            objectives = {}
            for metric in optimize_for:
                if metric in ["insertion_loss", "crosstalk", "footprint", "power"]:
                    objectives[metric] = "minimize"
                elif metric in ["bandwidth", "q_factor", "extinction_ratio"]:
                    objectives[metric] = "maximize"
                else:
                    objectives[metric] = "optimize"
            
            if target_values:
                objectives.update({"targets": target_values})
            
            try:
                result = self.api_client.optimize_pic(
                    design_id=design_id,
                    objectives=objectives,
                )
                
                self.logger.info(f"Optimization completed: {result.get('optimized_design_id')}")
                return result
                
            except Exception as e:
                self.logger.error(f"Optimization failed: {e}")
                raise
        
        @self.mcp.tool()
        def create_pic_from_template(
            template_name: str,
            custom_parameters: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            """
            Create a PIC design from a predefined template.
            
            Available templates: optical_switch, transceiver, sensor, filter_bank, modulator_array
            """
            self.logger.info(f"Creating PIC from template: {template_name}")
            
            # Template definitions
            templates = {
                "optical_switch": {
                    "components": [
                        {"type": "grating_coupler", "id": "gc_in", "port": "input"},
                        {"type": "mmi_coupler", "id": "mmi1", "config": "1x2"},
                        {"type": "phase_shifter", "id": "ps1"},
                        {"type": "phase_shifter", "id": "ps2"},
                        {"type": "mmi_coupler", "id": "mmi2", "config": "2x2"},
                        {"type": "grating_coupler", "id": "gc_out1", "port": "output"},
                        {"type": "grating_coupler", "id": "gc_out2", "port": "output"},
                    ],
                    "connections": [
                        {"from": "gc_in", "to": "mmi1"},
                        {"from": "mmi1.out1", "to": "ps1"},
                        {"from": "mmi1.out2", "to": "ps2"},
                        {"from": "ps1", "to": "mmi2.in1"},
                        {"from": "ps2", "to": "mmi2.in2"},
                        {"from": "mmi2.out1", "to": "gc_out1"},
                        {"from": "mmi2.out2", "to": "gc_out2"},
                    ],
                },
                "transceiver": {
                    "components": [
                        {"type": "grating_coupler", "id": "gc_tx", "port": "input"},
                        {"type": "modulator", "id": "mod1"},
                        {"type": "grating_coupler", "id": "gc_rx", "port": "output"},
                        {"type": "photodetector", "id": "pd1"},
                    ],
                    "connections": [
                        {"from": "gc_tx", "to": "mod1"},
                        {"from": "gc_rx", "to": "pd1"},
                    ],
                },
                "sensor": {
                    "components": [
                        {"type": "grating_coupler", "id": "gc_in", "port": "input"},
                        {"type": "ring_resonator", "id": "rr1", "config": "sensing"},
                        {"type": "ring_resonator", "id": "rr2", "config": "reference"},
                        {"type": "photodetector", "id": "pd1"},
                        {"type": "photodetector", "id": "pd2"},
                    ],
                    "connections": [
                        {"from": "gc_in", "to": "splitter"},
                        {"from": "splitter.out1", "to": "rr1"},
                        {"from": "splitter.out2", "to": "rr2"},
                        {"from": "rr1", "to": "pd1"},
                        {"from": "rr2", "to": "pd2"},
                    ],
                },
            }
            
            if template_name not in templates:
                return {
                    "error": f"Template '{template_name}' not found",
                    "available_templates": list(templates.keys()),
                }
            
            template = templates[template_name]
            
            # Apply custom parameters if provided
            if custom_parameters:
                for component in template["components"]:
                    if component["id"] in custom_parameters:
                        component.update(custom_parameters[component["id"]])
            
            # Design the PIC using the template
            design_params = PICDesignParams(
                components=template["components"],
                connections=template["connections"],
            )
            
            return design_pic(design_params)
        
        self.logger.info("PIC domain tools registered successfully")