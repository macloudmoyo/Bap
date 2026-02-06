"""Command-line interface for BAP scoring."""

import argparse
import csv
import sys
from pathlib import Path

from tabulate import tabulate

from .csv_io import export_results_csv, load_csv
from .dashboard import generate_dashboard
from .models import Rating, RATING_COLOURS
from .recommender import generate_recommendations
from .scorer import score_campaign


# Rating display colours (ANSI)
_RATING_ANSI = {
    Rating.POOR: "\033[91m",        # red
    Rating.GOOD: "\033[93m",        # yellow
    Rating.GREAT: "\033[92m",       # green
    Rating.EXCELLENT: "\033[96m",   # cyan
    Rating.ELITE: "\033[95m",       # magenta
}
_RESET = "\033[0m"


def _coloured_rating(rating: Rating) -> str:
    return f"{_RATING_ANSI.get(rating, '')}{rating.value}{_RESET}"


def _score_entries(input_path: str):
    """Load CSV, score all entries, attach recommendations."""
    entries = load_csv(input_path)
    if not entries:
        print("No campaign entries found in the CSV.")
        sys.exit(1)

    results = []
    for entry in entries:
        result = score_campaign(entry)
        result.recommendations = generate_recommendations(result)
        results.append(result)
    return results


def run_score(args: argparse.Namespace) -> None:
    """Score campaigns from a CSV and display results."""
    results = _score_entries(args.input)

    # Summary table
    table_rows = []
    for r in results:
        table_rows.append([
            r.campaign_name,
            r.ad_format.value,
            f"{r.ap * 100:.1f}%",
            f"{r.aqi:.2f}",
            f"{r.bap:.2f}",
            f"£{r.spend:,.0f}",
            f"{r.bap_per_1k:.2f}",
            f"£{r.cost_per_bap:.2f}",
            _coloured_rating(r.rating),
        ])

    print("\n" + "=" * 80)
    print("  HUMBLE ROOTS — BAP SCORECARD")
    print("=" * 80)
    print(tabulate(
        table_rows,
        headers=["Campaign", "Format", "AP", "AQI", "BAP", "Spend", "BAP/£1k", "Cost/BAP", "Rating"],
        tablefmt="simple_grid",
    ))

    # Detailed breakdown per campaign
    for r in results:
        print(f"\n{'─' * 80}")
        print(f"  {r.campaign_name} ({r.ad_format.value}) — {_coloured_rating(r.rating)} (BAP: {r.bap:.2f})")
        print(f"{'─' * 80}")

        print(f"\n  AP (Awareness Penetration):  {r.ap * 100:.1f}%  (Reach {r.reach:,} / ICP {r.icp_size:,})")
        print(f"  AQI (Quality Index):          {r.aqi:.2f}")
        print(f"    Dwell Index:      {r.dwell_index:.3f}")
        print(f"    CTR Index:        {r.ctr_index:.3f}")
        print(f"    View Index:       {r.view_index:.3f}")
        print(f"    Completion Index: {r.completion_index:.3f}")
        print(f"  BAP Score:                    {r.bap:.2f}")
        print(f"  BAP per £1k:                  {r.bap_per_1k:.2f}")
        print(f"  Cost per BAP:                 £{r.cost_per_bap:.2f}")

        if r.recommendations:
            print(f"\n  Recommendations:")
            for i, rec in enumerate(r.recommendations, 1):
                print(f"    {i}. {rec}")

    # Export if requested
    if args.output:
        export_results_csv(results, args.output)
        print(f"\nResults exported to: {args.output}")

    print()


def run_dashboard(args: argparse.Namespace) -> None:
    """Generate an HTML dashboard from campaign data."""
    results = _score_entries(args.input)
    output = args.output or "bap_dashboard.html"
    generate_dashboard(results, output)
    print(f"Dashboard generated: {output}")
    print(f"Open in your browser: file://{Path(output).resolve()}")


def run_template(args: argparse.Namespace) -> None:
    """Generate a blank CSV template."""
    headers = [
        "Format", "Campaign / Ad name", "ICP Size", "Reach (unique)",
        "Avg Dwell (s)", "Baseline Dwell (s)", "CTR (%)", "Baseline CTR (%)",
        "View Rate (%)", "Baseline View Rate (%)",
        "Views @25%", "Views @50%", "Views @75%", "Total Views",
        "Completion Rate (%)", "Baseline Completion Rate (%)", "Spend (£)",
    ]

    output = args.output or "bap_template.csv"
    path = Path(output)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow([
            "Image", "Example Campaign", "4000", "1500",
            "4.2", "4.0", "0.35", "0.38",
            "", "",
            "", "", "", "",
            "", "", "1000",
        ])

    print(f"Template created: {path}")
    print("Fill in your campaign data and run:")
    print(f"  python -m bap score {path}")
    print(f"  python -m bap dashboard {path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bap",
        description="BAP — Brand Awareness Penetration scoring for LinkedIn Ads",
    )
    subparsers = parser.add_subparsers(dest="command")

    # score command
    score_parser = subparsers.add_parser("score", help="Score campaigns from a CSV file")
    score_parser.add_argument("input", help="Path to input CSV file")
    score_parser.add_argument("-o", "--output", help="Path to export scored results CSV")

    # dashboard command
    dash_parser = subparsers.add_parser("dashboard", help="Generate HTML dashboard")
    dash_parser.add_argument("input", help="Path to input CSV file")
    dash_parser.add_argument("-o", "--output", help="Output HTML file (default: bap_dashboard.html)")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Launch local dashboard server")
    serve_parser.add_argument("input", help="Path to input CSV file")
    serve_parser.add_argument("-p", "--port", type=int, default=8080, help="Port (default: 8080)")

    # template command
    template_parser = subparsers.add_parser("template", help="Generate a blank CSV template")
    template_parser.add_argument("-o", "--output", help="Output path (default: bap_template.csv)")

    args = parser.parse_args()

    if args.command == "score":
        run_score(args)
    elif args.command == "dashboard":
        run_dashboard(args)
    elif args.command == "serve":
        from .server import serve
        serve(args.input, args.port)
    elif args.command == "template":
        run_template(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
