from .server import plots


def main():
    """Main entry point for the AxPlotToData server."""
    plots.run(transport="stdio")
