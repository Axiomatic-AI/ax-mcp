"""Configuration management for MCP servers."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

T = TypeVar("T", bound="BaseConfig")


class BaseConfig(BaseModel):
    """Base configuration for all MCP servers."""
    
    log_level: str = Field(default="info", description="Logging level")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    timeout: int = Field(default=30000, description="Operation timeout in milliseconds")
    
    class Config:
        extra = "allow"
        validate_assignment = True


def get_config_path() -> Path:
    """Get the configuration file path."""
    # Check environment variable first
    if config_path := os.getenv("AXIOMATIC_CONFIG_PATH"):
        return Path(config_path)
    
    # Check standard locations
    home = Path.home()
    
    # Try ~/.axiomatic/config.json
    axiomatic_dir = home / ".axiomatic"
    if axiomatic_dir.exists():
        config_file = axiomatic_dir / "config.json"
        if config_file.exists():
            return config_file
    
    # Try local config.json
    local_config = Path("config.json")
    if local_config.exists():
        return local_config
    
    # Return default path (may not exist)
    return axiomatic_dir / "config.json"


def load_config(
    config_class: Type[T] = BaseConfig,
    config_path: Optional[Path] = None,
) -> T:
    """
    Load configuration from file and environment variables.
    
    Args:
        config_class: The configuration class to use
        config_path: Optional path to configuration file
        
    Returns:
        Loaded configuration instance
    """
    config_data: Dict[str, Any] = {}
    
    # Load from file if it exists
    config_file = config_path or get_config_path()
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                config_data = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config from {config_file}: {e}")
    
    # Override with environment variables
    # Convert AXIOMATIC_LOG_LEVEL to log_level, etc.
    prefix = "AXIOMATIC_"
    for key, value in os.environ.items():
        if key.startswith(prefix):
            config_key = key[len(prefix):].lower()
            # Try to parse JSON values (for lists, dicts, etc.)
            try:
                config_data[config_key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                config_data[config_key] = value
    
    # Create and return config instance
    return config_class(**config_data)