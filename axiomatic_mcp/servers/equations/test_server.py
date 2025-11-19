from pathlib import Path

from axiomatic_mcp.shared.api_client import AxiomaticAPIClient

sample_pdf_path = Path("/Users/tymek_axai/Desktop/Quantum_basics.pdf")
sample_markdown_path = Path("/Users/tymek_axai/Desktop/Quantum_basics.md")

sample_task = "Check if the first equation is correct"

with AxiomaticAPIClient() as client:
    response = client.post(
        "/equations/derive", data={"task": sample_task}, files={"pdf_file": (sample_pdf_path.name, sample_pdf_path.read_bytes(), "application/pdf")}
    )
    print(response)
