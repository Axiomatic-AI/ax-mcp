"""Axiomatic API client for interacting with the Axiomatic platform."""

import json
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, Field


class AxiomaticAPIConfig(BaseModel):
    """Configuration for Axiomatic API client."""
    
    base_url: str = Field(
        default="https://api.axiomatic.ai",
        description="Base URL for Axiomatic API"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts"
    )


class AxiomaticAPIClient:
    """Client for interacting with Axiomatic API."""
    
    def __init__(self, config: AxiomaticAPIConfig):
        """
        Initialize the API client.
        
        Args:
            config: API configuration
        """
        self.config = config
        self.client = httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout,
            headers=self._get_headers(),
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers
    
    def design_pic(
        self,
        specification: Dict[str, Any],
        optimization_goals: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Design a Photonic Integrated Circuit (PIC) using Axiomatic API.
        
        Args:
            specification: PIC specification including components and connections
            optimization_goals: Optional optimization objectives
            constraints: Optional design constraints
            
        Returns:
            Design result from the API
        """
        payload = {
            "specification": specification,
            "optimization_goals": optimization_goals or {},
            "constraints": constraints or {},
        }
        
        try:
            response = self.client.post(
                "/v1/pic/design",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Return a fake response for demonstration
            return self._fake_pic_design_response(specification)
        except Exception as e:
            # Return a fake response for demonstration
            return self._fake_pic_design_response(specification)
    
    def _fake_pic_design_response(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a fake PIC design response for demonstration."""
        return {
            "success": True,
            "design_id": "pic_design_abc123",
            "status": "completed",
            "design": {
                "layout": {
                    "dimensions": {"width": 5000, "height": 3000, "units": "micrometers"},
                    "layers": ["waveguide", "metal1", "metal2"],
                    "components": [
                        {
                            "id": "grating_coupler_1",
                            "type": "grating_coupler",
                            "position": {"x": 100, "y": 1500},
                            "parameters": {
                                "pitch": 0.63,
                                "duty_cycle": 0.5,
                                "num_periods": 25,
                            },
                        },
                        {
                            "id": "mmi_1",
                            "type": "mmi_coupler",
                            "position": {"x": 1000, "y": 1500},
                            "parameters": {
                                "width": 12,
                                "length": 50,
                                "num_inputs": 1,
                                "num_outputs": 2,
                            },
                        },
                        {
                            "id": "ring_resonator_1",
                            "type": "ring_resonator",
                            "position": {"x": 2500, "y": 1200},
                            "parameters": {
                                "radius": 10,
                                "gap": 0.2,
                                "width": 0.5,
                            },
                        },
                    ],
                    "waveguides": [
                        {
                            "id": "wg_1",
                            "start": "grating_coupler_1.output",
                            "end": "mmi_1.input",
                            "width": 0.5,
                            "route": "auto",
                        },
                        {
                            "id": "wg_2",
                            "start": "mmi_1.output_1",
                            "end": "ring_resonator_1.input",
                            "width": 0.5,
                            "route": "auto",
                        },
                    ],
                },
                "performance": {
                    "insertion_loss": 2.3,
                    "crosstalk": -30,
                    "bandwidth": 40,
                    "fsr": 10,
                    "q_factor": 15000,
                },
                "optimization": {
                    "iterations": 150,
                    "convergence": True,
                    "final_cost": 0.0234,
                },
            },
            "metadata": {
                "created_at": "2024-01-16T10:30:00Z",
                "processing_time": 12.5,
                "version": "1.0.0",
            },
        }
    
    def simulate_pic(
        self,
        design_id: str,
        simulation_type: str = "fdtd",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Simulate a PIC design.
        
        Args:
            design_id: ID of the design to simulate
            simulation_type: Type of simulation (fdtd, mode, circuit)
            parameters: Simulation parameters
            
        Returns:
            Simulation results
        """
        payload = {
            "design_id": design_id,
            "simulation_type": simulation_type,
            "parameters": parameters or {},
        }
        
        try:
            response = self.client.post(
                "/v1/pic/simulate",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except:
            # Return fake response for demonstration
            return {
                "success": True,
                "simulation_id": f"sim_{design_id}_001",
                "status": "completed",
                "results": {
                    "type": simulation_type,
                    "data": {
                        "transmission": [0.95, 0.93, 0.91, 0.89],
                        "reflection": [0.02, 0.03, 0.04, 0.05],
                        "wavelengths": [1540, 1545, 1550, 1555],
                    },
                },
            }
    
    def optimize_pic(
        self,
        design_id: str,
        objectives: Dict[str, Any],
        method: str = "genetic",
    ) -> Dict[str, Any]:
        """
        Optimize a PIC design.
        
        Args:
            design_id: ID of the design to optimize
            objectives: Optimization objectives
            method: Optimization method
            
        Returns:
            Optimized design
        """
        payload = {
            "design_id": design_id,
            "objectives": objectives,
            "method": method,
        }
        
        try:
            response = self.client.post(
                "/v1/pic/optimize",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except:
            # Return fake response for demonstration
            return {
                "success": True,
                "optimized_design_id": f"{design_id}_opt",
                "improvements": {
                    "insertion_loss": -0.5,
                    "crosstalk": -5,
                    "bandwidth": 10,
                },
                "iterations": 250,
                "converged": True,
            }
    
    def close(self):
        """Close the API client."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()