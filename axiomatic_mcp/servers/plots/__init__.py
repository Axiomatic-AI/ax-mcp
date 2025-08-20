from .server import plots


def main():
    """Main entry point for the plots server."""
    plots.run(transport="stdio")
