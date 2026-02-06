"""Data models for BAP scoring framework.

Aligned with the Humble Roots BAP Framework spreadsheet structure.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class AdFormat(Enum):
    IMAGE = "Image"
    SINGLE = "Single"
    DOC_CAROUSEL = "Doc/Cara"
    VIDEO = "Video"
    VIDEOS = "Videos"


class Rating(Enum):
    POOR = "Poor"
    GOOD = "Good"
    GREAT = "Great"
    EXCELLENT = "Excellent"
    ELITE = "Elite"


# Colour codes for ratings (used in CLI and dashboard)
RATING_COLOURS = {
    Rating.POOR: "#ef4444",       # red
    Rating.GOOD: "#f59e0b",       # amber
    Rating.GREAT: "#22c55e",      # green
    Rating.EXCELLENT: "#3b82f6",  # blue
    Rating.ELITE: "#a855f7",      # purple
}


@dataclass
class CampaignEntry:
    """A single campaign data entry (one row from the spreadsheet).

    Columns map to the Humble Roots BAP Framework spreadsheet:
    Format | Campaign/Ad name | ICP Size | Reach (unique) | AP |
    Avg Dwell (s) | Baseline Dwell (s) | CTR (%) | Baseline CTR (%) |
    View Rate (%) | Baseline View Rate (%) | Views @25% | Views @50% |
    Views @75% | Total Views | Completion Rate (%) |
    Baseline Completion Rate (%) | Spend (£)
    """

    # Identity
    ad_format: AdFormat = AdFormat.IMAGE
    campaign_name: str = ""

    # Audience
    icp_size: int = 0
    reach: int = 0

    # Dwell / attention
    avg_dwell: float = 0.0
    baseline_dwell: float = 0.0

    # Click-through
    ctr: float = 0.0
    baseline_ctr: float = 0.0

    # View rate (for video / doc formats)
    view_rate: float = 0.0
    baseline_view_rate: float = 0.0

    # Video funnel
    views_25: int = 0
    views_50: int = 0
    views_75: int = 0
    total_views: int = 0

    # Completion
    completion_rate: float = 0.0
    baseline_completion_rate: float = 0.0

    # Cost
    spend: float = 0.0


@dataclass
class BapScoreResult:
    """Computed BAP scores for a campaign entry."""

    campaign_name: str
    ad_format: AdFormat = AdFormat.IMAGE

    # Core metrics
    ap: float = 0.0               # Awareness Penetration (Reach / ICP Size)
    aqi: float = 0.0              # Awareness Quality Index
    bap: float = 0.0              # Brand Awareness Penetration score
    bap_per_1k: float = 0.0       # BAP per £1k spend
    cost_per_bap: float = 0.0     # Cost per BAP point
    rating: Rating = Rating.POOR

    # Sub-scores for transparency
    dwell_index: float = 0.0
    ctr_index: float = 0.0
    view_index: float = 0.0
    completion_index: float = 0.0

    # Raw inputs carried through
    icp_size: int = 0
    reach: int = 0
    spend: float = 0.0

    # Recommendations
    recommendations: list = field(default_factory=list)


def get_rating(bap: float) -> Rating:
    """Classify a BAP score into a performance rating."""
    if bap < 5:
        return Rating.POOR
    elif bap < 15:
        return Rating.GOOD
    elif bap < 30:
        return Rating.GREAT
    elif bap < 50:
        return Rating.EXCELLENT
    else:
        return Rating.ELITE
