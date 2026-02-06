"""Local development server for the BAP dashboard."""

import http.server
import os
import sys
import webbrowser
from pathlib import Path

from .csv_io import load_csv
from .dashboard import generate_dashboard
from .recommender import generate_recommendations
from .scorer import score_campaign


def serve(csv_path: str, port: int = 8080) -> None:
    """Score the CSV, generate the dashboard, and serve it locally."""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        print(f"Error: {csv_path} not found")
        sys.exit(1)

    # Score and generate
    entries = load_csv(csv_path)
    if not entries:
        print("No campaign entries found in the CSV.")
        sys.exit(1)

    results = []
    for entry in entries:
        result = score_campaign(entry)
        result.recommendations = generate_recommendations(result)
        results.append(result)

    output_dir = Path("_bap_serve")
    output_dir.mkdir(exist_ok=True)
    dashboard_path = output_dir / "index.html"
    generate_dashboard(results, dashboard_path)

    # Serve
    os.chdir(output_dir)
    handler = http.server.SimpleHTTPRequestHandler

    with http.server.HTTPServer(("0.0.0.0", port), handler) as httpd:
        url = f"http://localhost:{port}"
        print(f"\n  BAP Dashboard running at: {url}")
        print(f"  Serving {len(results)} campaigns from {csv_path.name}")
        print(f"  Press Ctrl+C to stop\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
