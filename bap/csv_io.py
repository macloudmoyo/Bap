"""CSV import/export – bridges the spreadsheet workflow to automated scoring.

Handles the Humble Roots BAP Framework spreadsheet format with flexible
column name matching.
"""

import csv
from pathlib import Path

from .models import AdFormat, BapScoreResult, CampaignEntry


# ── Column name mappings (flexible, case-insensitive) ──────────────────

_COLUMN_ALIASES = {
    "ad_format": ["format", "ad_format", "ad_type"],
    "campaign_name": [
        "campaign_name", "campaign", "campaign / ad name",
        "campaign/ad name", "ad name", "name",
    ],
    "icp_size": ["icp_size", "icp size", "icp", "audience_size", "target_audience_size"],
    "reach": ["reach", "reach (unique)", "unique_reach", "unique reach"],
    "avg_dwell": ["avg_dwell", "avg dwell", "avg dwell (s)", "dwell", "dwell_time"],
    "baseline_dwell": [
        "baseline_dwell", "baseline dwell", "baseline dwell (s)", "baseline_dwell_s",
    ],
    "ctr": ["ctr", "ctr (%)", "ctr_pct", "click_through_rate"],
    "baseline_ctr": ["baseline_ctr", "baseline ctr", "baseline ctr (%)", "baseline_ctr_pct"],
    "view_rate": ["view_rate", "view rate", "view rate (%)", "view_rate_pct"],
    "baseline_view_rate": [
        "baseline_view_rate", "baseline view rate", "baseline view rate (%)",
    ],
    "views_25": ["views_25", "views @25%", "views_at_25", "views 25"],
    "views_50": ["views_50", "views @50%", "views_at_50", "views 50"],
    "views_75": ["views_75", "views @75%", "views_at_75", "views 75"],
    "total_views": ["total_views", "total views", "views"],
    "completion_rate": [
        "completion_rate", "completion rate", "completion rate (%)",
        "completion_rate_pct",
    ],
    "baseline_completion_rate": [
        "baseline_completion_rate", "baseline completion rate",
        "baseline completion rate (%)",
    ],
    "spend": ["spend", "spend (£)", "spend (gbp)", "cost", "amount_spent", "total_spend"],
}


def _build_column_map(header: list[str]) -> dict[str, int]:
    """Map canonical field names to column indices, tolerating various aliases."""
    lower_header = [h.strip().lower() for h in header]
    col_map = {}
    for field_name, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_header:
                col_map[field_name] = lower_header.index(alias)
                break
    return col_map


def _parse_format(val: str) -> AdFormat:
    cleaned = val.strip()
    for member in AdFormat:
        if member.value.lower() == cleaned.lower():
            return member
    # Fuzzy matching
    lower = cleaned.lower()
    if "doc" in lower or "cara" in lower or "carousel" in lower:
        return AdFormat.DOC_CAROUSEL
    if "video" in lower and lower.endswith("s"):
        return AdFormat.VIDEOS
    if "video" in lower:
        return AdFormat.VIDEO
    if "single" in lower:
        return AdFormat.SINGLE
    return AdFormat.IMAGE


def _int(val: str) -> int:
    try:
        return int(float(val.strip().replace(",", "")))
    except (ValueError, AttributeError):
        return 0


def _float(val: str) -> float:
    try:
        return float(val.strip().replace(",", "").replace("£", "").replace("$", "").replace("%", ""))
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
                "CSV must have a 'Campaign / Ad name' (or 'campaign_name') column. "
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
                    ad_format=_parse_format(_get("ad_format", "Image")),
                    campaign_name=_get("campaign_name", f"Campaign_{row_num}"),
                    icp_size=_int(_get("icp_size")),
                    reach=_int(_get("reach")),
                    avg_dwell=_float(_get("avg_dwell")),
                    baseline_dwell=_float(_get("baseline_dwell")),
                    ctr=_float(_get("ctr")),
                    baseline_ctr=_float(_get("baseline_ctr")),
                    view_rate=_float(_get("view_rate")),
                    baseline_view_rate=_float(_get("baseline_view_rate")),
                    views_25=_int(_get("views_25")),
                    views_50=_int(_get("views_50")),
                    views_75=_int(_get("views_75")),
                    total_views=_int(_get("total_views")),
                    completion_rate=_float(_get("completion_rate")),
                    baseline_completion_rate=_float(_get("baseline_completion_rate")),
                    spend=_float(_get("spend")),
                )
                # Skip rows with no meaningful data
                if entry.reach == 0 and entry.spend == 0 and entry.ctr == 0:
                    continue
                entries.append(entry)
            except Exception as e:
                print(f"Warning: skipping row {row_num}: {e}")

    return entries


def export_results_csv(results: list[BapScoreResult], path: str | Path) -> None:
    """Export scored results to CSV."""
    path = Path(path)
    fieldnames = [
        "campaign_name", "format", "icp_size", "reach", "ap",
        "aqi", "bap", "spend", "bap_per_1k", "cost_per_bap",
        "rating", "recommendations",
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "campaign_name": r.campaign_name,
                "format": r.ad_format.value,
                "icp_size": r.icp_size,
                "reach": r.reach,
                "ap": r.ap,
                "aqi": r.aqi,
                "bap": r.bap,
                "spend": r.spend,
                "bap_per_1k": r.bap_per_1k,
                "cost_per_bap": r.cost_per_bap,
                "rating": r.rating.value,
                "recommendations": " | ".join(r.recommendations),
            })
