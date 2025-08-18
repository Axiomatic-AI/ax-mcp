"""Base server class for all MCP servers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, Optional, Type, TypeVar

from fastmcp import FastMCP

from .config import BaseConfig, load_config
from .logger import Logger

T = TypeVar("T", bound=BaseConfig)


class BaseServer(ABC, Generic[T]):
    """Base class for all MCP servers."""
    
    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        config_class: Type[T] = BaseConfig,
    ):
        """
        Initialize base server.
        
        Args:
            name: Server name
            version: Server version
            description: Server description
            config_class: Configuration class to use
        """
        self.name = name
        self.version = version
        self.description = description
        self.config_class = config_class
        self.config: T = None
        self.logger: Logger = None
        self.mcp: FastMCP = None
    
    def initialize(self, config_path: Optional[Path] = None) -> None:
        """
        Initialize server configuration and logging.
        
        Args:
            config_path: Optional path to configuration file
        """
        # Load configuration
        self.config = load_config(self.config_class, config_path)
        
        # Initialize logger
        self.logger = Logger(self.name, self.config.log_level)
        self.logger.info(f"Initializing {self.name} v{self.version}")
        
        # Initialize FastMCP
        self.mcp = FastMCP(
            name=self.name,
            version=self.version,
            description=self.description,
        )
        
        # Setup server-specific tools
        try:
            self.setup_tools()
            self.logger.info(f"{self.name} initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to setup tools: {e}")
            raise
    
    @abstractmethod
    def setup_tools(self) -> None:
        """
        Setup server-specific tools.
        Must be implemented by subclasses.
        """
        pass
    
    def run(self, config_path: Optional[Path] = None) -> None:
        """
        Run the MCP server.
        
        Args:
            config_path: Optional path to configuration file
        """
        try:
            self.initialize(config_path)
            self.logger.info(f"Starting {self.name} server...")
            self.mcp.run()
        except KeyboardInterrupt:
            self.logger.info("Server stopped by user")
        except Exception as e:
            self.logger.exception(f"Server error: {e}")
            raise