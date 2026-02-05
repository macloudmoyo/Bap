"""Command-line interface for BAP scoring."""

import argparse
import sys
from pathlib import Path

from tabulate import tabulate

from .csv_io import export_results_csv, load_csv
from .models import ScoreBand
from .recommender import generate_recommendations
from .scorer import ScoringWeights, score_campaign


# Band display colours (ANSI)
_BAND_COLOUR = {
    ScoreBand.CRITICAL: "\033[91m",   # red
    ScoreBand.LOW: "\033[93m",        # yellow
    ScoreBand.MODERATE: "\033[33m",   # orange-ish
    ScoreBand.STRONG: "\033[92m",     # green
    ScoreBand.EXCEPTIONAL: "\033[96m",  # cyan
}
_RESET = "\033[0m"


def _coloured_band(band: ScoreBand) -> str:
    return f"{_BAND_COLOUR.get(band, '')}{band.value}{_RESET}"


def run_score(args: argparse.Namespace) -> None:
    """Score campaigns from a CSV and display results."""
    entries = load_csv(args.input)
    if not entries:
        print("No campaign entries found in the CSV.")
        sys.exit(1)

    weights = ScoringWeights(
        recall=args.weight_recall,
        trust=args.weight_trust,
        penetration=args.weight_penetration,
    )

    results = []
    for entry in entries:
        result = score_campaign(entry, weights)
        result.recommendations = generate_recommendations(result)
        results.append(result)

    # Summary table
    table_rows = []
    for r in results:
        table_rows.append([
            r.campaign_name,
            r.date.isoformat(),
            r.recall_score,
            r.trust_score,
            r.penetration_score,
            r.overall_score,
            _coloured_band(r.band),
        ])

    print("\n" + "=" * 70)
    print("  BAP SCORECARD")
    print("=" * 70)
    print(tabulate(
        table_rows,
        headers=["Campaign", "Date", "Recall", "Trust", "Penetration", "BAP Score", "Band"],
        tablefmt="simple_grid",
        floatfmt=".1f",
    ))

    # Detailed breakdown per campaign
    for r in results:
        print(f"\n{'─' * 70}")
        print(f"  {r.campaign_name} ({r.date.isoformat()}) — {_coloured_band(r.band)} ({r.overall_score}/100)")
        print(f"{'─' * 70}")

        # Pillar breakdown
        print(f"\n  Recall:      {r.recall_score:5.1f}/100")
        for k, v in r.components.get("recall", {}).items():
            print(f"    {k:25s} {v}")

        print(f"\n  Trust:       {r.trust_score:5.1f}/100")
        for k, v in r.components.get("trust", {}).items():
            print(f"    {k:25s} {v}")

        print(f"\n  Penetration: {r.penetration_score:5.1f}/100")
        for k, v in r.components.get("penetration", {}).items():
            print(f"    {k:25s} {v}")

        # Recommendations
        if r.recommendations:
            print(f"\n  Recommendations:")
            for i, rec in enumerate(r.recommendations, 1):
                print(f"    {i}. {rec}")

    # Export if requested
    if args.output:
        export_results_csv(results, args.output)
        print(f"\nResults exported to: {args.output}")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bap",
        description="BAP — Brand Awareness Penetration scoring for LinkedIn Ads",
    )
    subparsers = parser.add_subparsers(dest="command")

    # score command
    score_parser = subparsers.add_parser("score", help="Score campaigns from a CSV file")
    score_parser.add_argument("input", help="Path to input CSV file")
    score_parser.add_argument(
        "-o", "--output", help="Path to export scored results CSV"
    )
    score_parser.add_argument(
        "--weight-recall", type=float, default=0.35,
        help="Weight for Recall pillar (default: 0.35)",
    )
    score_parser.add_argument(
        "--weight-trust", type=float, default=0.35,
        help="Weight for Trust pillar (default: 0.35)",
    )
    score_parser.add_argument(
        "--weight-penetration", type=float, default=0.30,
        help="Weight for Penetration pillar (default: 0.30)",
    )

    # template command
    template_parser = subparsers.add_parser(
        "template", help="Generate a blank CSV template to fill in"
    )
    template_parser.add_argument(
        "-o", "--output", default="bap_template.csv",
        help="Output path (default: bap_template.csv)",
    )

    args = parser.parse_args()

    if args.command == "score":
        run_score(args)
    elif args.command == "template":
        _generate_template(args.output)
    else:
        parser.print_help()


def _generate_template(output: str) -> None:
    """Generate a blank CSV template."""
    import csv

    headers = [
        "campaign_name", "date", "objective", "ad_format",
        "impressions", "unique_reach", "frequency",
        "clicks", "reactions", "comments", "shares", "follows",
        "video_views", "video_completions",
        "spend", "target_audience_size",
    ]

    path = Path(output)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        # Write one example row
        writer.writerow([
            "Example Campaign Q1", "2025-01-15", "brand_awareness", "single_image",
            "50000", "25000", "2.0",
            "350", "200", "15", "8", "12",
            "0", "0",
            "500.00", "100000",
        ])

    print(f"Template created: {path}")
    print("Fill in your campaign data and run: bap score <file.csv>")


if __name__ == "__main__":
    main()
