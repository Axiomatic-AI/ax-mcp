from .server import plot_parser_server

def main():
    """Main entry point for the plot_parser server."""
    plot_parser_server.run(transport="stdio")
