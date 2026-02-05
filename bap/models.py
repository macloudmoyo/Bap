"""Data models for BAP scoring framework."""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class AdFormat(Enum):
    SINGLE_IMAGE = "single_image"
    CAROUSEL = "carousel"
    VIDEO = "video"
    TEXT = "text"
    EVENT = "event"
    DOCUMENT = "document"


class CampaignObjective(Enum):
    BRAND_AWARENESS = "brand_awareness"
    ENGAGEMENT = "engagement"
    WEBSITE_VISITS = "website_visits"
    VIDEO_VIEWS = "video_views"
    LEAD_GEN = "lead_gen"


class ScoreBand(Enum):
    CRITICAL = "Critical"
    LOW = "Low"
    MODERATE = "Moderate"
    STRONG = "Strong"
    EXCEPTIONAL = "Exceptional"


@dataclass
class CampaignEntry:
    """A single campaign data entry (one row from the spreadsheet)."""

    campaign_name: str
    date: date
    objective: CampaignObjective
    ad_format: AdFormat

    # Reach & Impressions
    impressions: int = 0
    unique_reach: int = 0
    frequency: float = 0.0

    # Engagement
    clicks: int = 0
    reactions: int = 0
    comments: int = 0
    shares: int = 0
    follows: int = 0
    video_views: int = 0
    video_completions: int = 0

    # Cost
    spend: float = 0.0

    # Audience
    target_audience_size: int = 0


@dataclass
class BapScoreResult:
    """Computed BAP scores for a campaign entry."""

    campaign_name: str
    date: date

    # Pillar scores (0-100)
    recall_score: float = 0.0
    trust_score: float = 0.0
    penetration_score: float = 0.0

    # Overall BAP score (weighted composite)
    overall_score: float = 0.0
    band: ScoreBand = ScoreBand.CRITICAL

    # Component details for transparency
    components: dict = field(default_factory=dict)

    # Recommendations
    recommendations: list = field(default_factory=list)


@dataclass
class TrendPoint:
    """A single point in a BAP trend over time."""

    date: date
    overall_score: float
    recall_score: float
    trust_score: float
    penetration_score: float


def get_band(score: float) -> ScoreBand:
    """Classify a 0-100 score into a performance band."""
    if score < 20:
        return ScoreBand.CRITICAL
    elif score < 40:
        return ScoreBand.LOW
    elif score < 60:
        return ScoreBand.MODERATE
    elif score < 80:
        return ScoreBand.STRONG
    else:
        return ScoreBand.EXCEPTIONAL
