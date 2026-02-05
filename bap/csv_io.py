"""CSV import/export – bridges the spreadsheet workflow to automated scoring."""

import csv
from datetime import date, datetime
from pathlib import Path
from typing import TextIO

from .models import AdFormat, BapScoreResult, CampaignEntry, CampaignObjective


# ── Column name mappings (flexible, case-insensitive) ──────────────────

_COLUMN_ALIASES = {
    "campaign_name": ["campaign_name", "campaign", "name"],
    "date": ["date", "report_date", "day"],
    "objective": ["objective", "campaign_objective"],
    "ad_format": ["ad_format", "format", "ad_type"],
    "impressions": ["impressions", "imps"],
    "unique_reach": ["unique_reach", "reach", "unique_impressions"],
    "frequency": ["frequency", "avg_frequency"],
    "clicks": ["clicks", "link_clicks"],
    "reactions": ["reactions", "likes"],
    "comments": ["comments"],
    "shares": ["shares", "reposts"],
    "follows": ["follows", "new_followers"],
    "video_views": ["video_views", "views"],
    "video_completions": ["video_completions", "completions", "complete_views"],
    "spend": ["spend", "cost", "amount_spent", "total_spend"],
    "target_audience_size": ["target_audience_size", "audience_size", "audience"],
}


def _build_column_map(header: list[str]) -> dict[str, int]:
    """Map canonical field names to column indices, tolerating various aliases."""
    lower_header = [h.strip().lower().replace(" ", "_") for h in header]
    col_map = {}
    for field, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_header:
                col_map[field] = lower_header.index(alias)
                break
    return col_map


def _parse_date(val: str) -> date:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(val.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {val!r}")


def _parse_objective(val: str) -> CampaignObjective:
    cleaned = val.strip().lower().replace(" ", "_")
    for member in CampaignObjective:
        if member.value == cleaned:
            return member
    return CampaignObjective.BRAND_AWARENESS


def _parse_ad_format(val: str) -> AdFormat:
    cleaned = val.strip().lower().replace(" ", "_")
    for member in AdFormat:
        if member.value == cleaned:
            return member
    return AdFormat.SINGLE_IMAGE


def _int(val: str) -> int:
    try:
        return int(val.strip().replace(",", ""))
    except (ValueError, AttributeError):
        return 0


def _float(val: str) -> float:
    try:
        return float(val.strip().replace(",", "").replace("£", "").replace("$", ""))
    except (ValueError, AttributeError):
        return 0.0


def load_csv(path: str | Path) -> list[CampaignEntry]:
    """Load campaign entries from a CSV file."""
    entries = []
    path = Path(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        col_map = _build_column_map(header)

        if "campaign_name" not in col_map:
            raise ValueError(
                "CSV must have a 'campaign_name' (or 'campaign') column. "
                f"Found columns: {header}"
            )

        for row_num, row in enumerate(reader, start=2):
            if not any(cell.strip() for cell in row):
                continue  # skip blank rows

            def _get(field: str, default: str = "") -> str:
                idx = col_map.get(field)
                if idx is not None and idx < len(row):
                    return row[idx]
                return default

            try:
                entry = CampaignEntry(
                    campaign_name=_get("campaign_name", f"Campaign_{row_num}"),
                    date=_parse_date(_get("date", "2025-01-01")),
                    objective=_parse_objective(_get("objective", "brand_awareness")),
                    ad_format=_parse_ad_format(_get("ad_format", "single_image")),
                    impressions=_int(_get("impressions")),
                    unique_reach=_int(_get("unique_reach")),
                    frequency=_float(_get("frequency")),
                    clicks=_int(_get("clicks")),
                    reactions=_int(_get("reactions")),
                    comments=_int(_get("comments")),
                    shares=_int(_get("shares")),
                    follows=_int(_get("follows")),
                    video_views=_int(_get("video_views")),
                    video_completions=_int(_get("video_completions")),
                    spend=_float(_get("spend")),
                    target_audience_size=_int(_get("target_audience_size")),
                )
                entries.append(entry)
            except Exception as e:
                print(f"Warning: skipping row {row_num}: {e}")

    return entries


def export_results_csv(results: list[BapScoreResult], path: str | Path) -> None:
    """Export scored results to CSV."""
    path = Path(path)
    fieldnames = [
        "campaign_name", "date", "recall_score", "trust_score",
        "penetration_score", "overall_score", "band", "recommendations",
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "campaign_name": r.campaign_name,
                "date": r.date.isoformat(),
                "recall_score": r.recall_score,
                "trust_score": r.trust_score,
                "penetration_score": r.penetration_score,
                "overall_score": r.overall_score,
                "band": r.band.value,
                "recommendations": " | ".join(r.recommendations),
            })
