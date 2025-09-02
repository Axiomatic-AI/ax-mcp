import nbformat


class AnalysisCellsTemplate:
    """Factory class to generate analysis cells for a simulation notebook."""

    @staticmethod
    def get_cells() -> list:
        """Return nbformat cells for simulation analysis."""
        return [
            # SimulationResult class definition
            nbformat.v4.new_code_cell(
                """class SimulationResult:
    # The component's range of wavelengths in nanometers
    wavelengths: list[float]
    # The simulated transmission spectrum in dimensionless units.
    # Dictionary which has port pairs as key, and simulated transmission values
    # as value.
    transmission_lin: dict[str, list[float]]
    # The simulated transmission spectrum in dB
    # Dictionary which has port pairs as key, and simulated transmission values
    # as value.
    transmission_log: dict[str, list[float]]
    # The names of the port pairs in the simulation. Shared between the linear
    # and logarithmic transmission spectra.
    port_pairs: list[str]

    def __init__(
        self, wavelengths: list[float], simulation_data: dict[str, list[float]]
    ):
        \"\"\"Initializes the result object from the simulated results.\"\"\"
        self.wavelengths = wavelengths
        self.transmission_lin = simulation_data["spectrum"]
        self.transmission_log = simulation_data["spectrum_db"]
        self.port_pairs = list(self.transmission_lin.keys())


simulation_result = SimulationResult(wavelengths, simulation_data)"""
            ),
            # Markdown explanation
            nbformat.v4.new_markdown_cell(
                """# Your Simulation Results

Welcome! This interactive notebook has been generated to help you explore
the data from your component simulation.

The cells above contain your data and setup code. You can expand any cell
to see its content, but you don't need to edit the first two cells to
generate the plot.

## Interactive Plot

The cell below displays a plot showing the simulated transmission for all
port pairs across the full wavelength range.

You can directly interact with this plot:

- Show or Hide Data: Click the names in the legend on the right to toggle
  which port pairs are displayed (applies if there are multiple port pairs).
- Switch the Scale: Use the "Log" and "Linear" buttons to change the view.
- Zoom and Explore: Click and drag on the plot to zoom in. Double-click to
  reset the view. Use the range selector below the plot to adjust the visible
  wavelength range.

The plot is created with [Plotly](https://plotly.com/). If you'd like to make
custom changes, such as changing titles or colors, you can find many examples
in the [Plotly documentation](https://plotly.com/python)."""
            ),
            # Plotly visualization
            nbformat.v4.new_code_cell(
                """import plotly.graph_objects as go
import plotly.express as px


color_palette = px.colors.qualitative.G10
lin_traces = []
log_traces = []

for i, name in enumerate(simulation_result.port_pairs):
    color = color_palette[i % len(color_palette)]

    lin_traces.append(
        go.Scatter(
            x=simulation_result.wavelengths,
            y=simulation_result.transmission_lin[name][0],
            name=name,
            line=dict(color=color),
            visible=True,
        )
    )
    log_traces.append(
        go.Scatter(
            x=simulation_result.wavelengths,
            y=simulation_result.transmission_log[name][0],
            name=name,
            line=dict(color=color),
            visible=False,
        )
    )

# We use both log and linear traces together, and toggle the visibility
# using the buttons (see updatemenus below).
fig = go.Figure(data=log_traces + lin_traces)

min_wl = min(simulation_result.wavelengths)
max_wl = max(simulation_result.wavelengths)

fig.update_layout(
    xaxis=dict(
        title="Wavelength (µm)",
        rangeslider=dict(visible=True),
        minallowed=min_wl,
        maxallowed=max_wl,
    ),
    yaxis_title="Transmission",
    updatemenus=[
        dict(
            type="buttons",
            direction="left",
            showactive=True,
            x=0.5,
            xanchor="center",
            y=-0.7,
            yanchor="top",
            buttons=[
                dict(
                    label="Linear",
                    method="update",
                    args=[
                        {
                            "visible": [False] * len(log_traces)
                            + [True] * len(lin_traces)
                        },
                        {"yaxis.title.text": "Transmission"},
                    ],
                ),
                dict(
                    label="Log",
                    method="update",
                    args=[
                        {
                            "visible": [True] * len(log_traces)
                            + [False] * len(lin_traces)
                        },
                        {"yaxis.title.text": "Transmission (dB)"},
                    ],
                ),
            ],
        ),
    ],
)

fig.show()"""
            ),
        ]
