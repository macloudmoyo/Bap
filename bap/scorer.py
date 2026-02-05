"""Core BAP scoring engine.

Scores campaigns across three pillars:
  1. Recall   – Are people seeing and remembering the ads?
  2. Trust    – Are people engaging meaningfully (not just scrolling past)?
  3. Penetration – How deeply is the campaign reaching the target audience?

Each pillar is scored 0-100, then combined into an overall BAP score using
configurable weights (default 35/35/30).
"""

from dataclasses import dataclass
from typing import Optional

from .models import BapScoreResult, CampaignEntry, get_band


@dataclass
class ScoringWeights:
    """Weights for the three BAP pillars (must sum to 1.0)."""

    recall: float = 0.35
    trust: float = 0.35
    penetration: float = 0.30

    def __post_init__(self):
        total = self.recall + self.trust + self.penetration
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


# ---------------------------------------------------------------------------
# Benchmark thresholds for LinkedIn ads (used to normalise raw metrics).
# These represent "excellent" performance – hitting the benchmark = 100.
# ---------------------------------------------------------------------------

# Recall benchmarks
CTR_BENCHMARK = 0.60          # 0.60% CTR is strong for LinkedIn
FREQUENCY_SWEET_SPOT = 4.0    # 3-5 is the recall sweet spot
FREQUENCY_MIN = 1.5           # Below this, too few touches
FREQUENCY_MAX = 8.0           # Above this, fatigue sets in

# Trust benchmarks
ENGAGEMENT_RATE_BENCHMARK = 2.0   # 2% engagement rate is strong
SHARE_RATE_BENCHMARK = 0.15       # Shares are rare and high-value
COMMENT_RATE_BENCHMARK = 0.10     # Comments show deep engagement
VIDEO_COMPLETION_BENCHMARK = 0.30 # 30% completion rate

# Penetration benchmarks
REACH_PENETRATION_BENCHMARK = 0.25  # Reaching 25% of target = excellent
CPM_BENCHMARK = 35.0               # £/$35 CPM is efficient for LinkedIn


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def score_recall(entry: CampaignEntry) -> tuple[float, dict]:
    """Score the Recall pillar (0-100).

    Components:
      - CTR quality (40%): Higher CTR = ads are noticed and clicked
      - Frequency score (35%): Sweet-spot frequency = better recall
      - Impression consistency (25%): Reach-to-impression ratio
    """
    components = {}

    # CTR quality
    ctr = _safe_div(entry.clicks, entry.impressions) * 100
    ctr_score = _clamp((ctr / CTR_BENCHMARK) * 100)
    components["ctr_pct"] = round(ctr, 3)
    components["ctr_score"] = round(ctr_score, 1)

    # Frequency score – bell curve around the sweet spot
    freq = entry.frequency if entry.frequency > 0 else _safe_div(
        entry.impressions, entry.unique_reach
    )
    if freq < FREQUENCY_MIN:
        freq_score = _clamp((freq / FREQUENCY_MIN) * 60)  # cap at 60 if under min
    elif freq <= FREQUENCY_SWEET_SPOT:
        freq_score = 60 + _clamp(
            ((freq - FREQUENCY_MIN) / (FREQUENCY_SWEET_SPOT - FREQUENCY_MIN)) * 40
        )
    elif freq <= FREQUENCY_MAX:
        # Diminishing returns above sweet spot
        overshoot = (freq - FREQUENCY_SWEET_SPOT) / (FREQUENCY_MAX - FREQUENCY_SWEET_SPOT)
        freq_score = _clamp(100 - (overshoot * 30))
    else:
        # Fatigue zone
        freq_score = _clamp(70 - ((freq - FREQUENCY_MAX) * 5))
    components["frequency"] = round(freq, 2)
    components["frequency_score"] = round(freq_score, 1)

    # Impression-to-reach ratio (lower = fresher audience)
    reach_ratio = _safe_div(entry.unique_reach, entry.impressions)
    consistency_score = _clamp(reach_ratio * 100 * 1.5)  # scale up, unique reach < impressions
    components["reach_ratio"] = round(reach_ratio, 3)
    components["consistency_score"] = round(consistency_score, 1)

    pillar = (ctr_score * 0.40) + (freq_score * 0.35) + (consistency_score * 0.25)
    return round(_clamp(pillar), 1), components


def score_trust(entry: CampaignEntry) -> tuple[float, dict]:
    """Score the Trust pillar (0-100).

    Components:
      - Engagement rate (35%): Total engagements / impressions
      - Share rate (25%): Shares signal high trust (people stake reputation)
      - Comment rate (20%): Comments show active interest
      - Video completion (20%): Only if video format, else redistributed
    """
    components = {}

    total_engagements = (
        entry.clicks + entry.reactions + entry.comments
        + entry.shares + entry.follows
    )
    eng_rate = _safe_div(total_engagements, entry.impressions) * 100
    eng_score = _clamp((eng_rate / ENGAGEMENT_RATE_BENCHMARK) * 100)
    components["engagement_rate_pct"] = round(eng_rate, 3)
    components["engagement_score"] = round(eng_score, 1)

    share_rate = _safe_div(entry.shares, entry.impressions) * 100
    share_score = _clamp((share_rate / SHARE_RATE_BENCHMARK) * 100)
    components["share_rate_pct"] = round(share_rate, 4)
    components["share_score"] = round(share_score, 1)

    comment_rate = _safe_div(entry.comments, entry.impressions) * 100
    comment_score = _clamp((comment_rate / COMMENT_RATE_BENCHMARK) * 100)
    components["comment_rate_pct"] = round(comment_rate, 4)
    components["comment_score"] = round(comment_score, 1)

    has_video = entry.video_views > 0 or entry.video_completions > 0
    if has_video:
        vid_completion_rate = _safe_div(entry.video_completions, entry.video_views)
        vid_score = _clamp((vid_completion_rate / VIDEO_COMPLETION_BENCHMARK) * 100)
        components["video_completion_rate"] = round(vid_completion_rate, 3)
        components["video_score"] = round(vid_score, 1)

        pillar = (
            eng_score * 0.35
            + share_score * 0.25
            + comment_score * 0.20
            + vid_score * 0.20
        )
    else:
        # Redistribute video weight to engagement and shares
        pillar = (
            eng_score * 0.45
            + share_score * 0.30
            + comment_score * 0.25
        )

    return round(_clamp(pillar), 1), components


def score_penetration(entry: CampaignEntry) -> tuple[float, dict]:
    """Score the Penetration pillar (0-100).

    Components:
      - Audience reach % (50%): unique_reach / target_audience_size
      - Cost efficiency (30%): CPM relative to benchmark
      - Follow conversion (20%): Follows / unique_reach
    """
    components = {}

    # Audience reach penetration
    if entry.target_audience_size > 0:
        reach_pct = _safe_div(entry.unique_reach, entry.target_audience_size)
        reach_score = _clamp((reach_pct / REACH_PENETRATION_BENCHMARK) * 100)
        components["reach_penetration_pct"] = round(reach_pct * 100, 2)
    else:
        # Without audience size, use raw reach as a proxy (scaled loosely)
        reach_score = _clamp(min(entry.unique_reach / 1000, 100))
        components["reach_penetration_pct"] = None
    components["reach_score"] = round(reach_score, 1)

    # Cost efficiency (CPM)
    cpm = _safe_div(entry.spend, entry.impressions) * 1000
    if cpm > 0:
        cpm_score = _clamp((CPM_BENCHMARK / cpm) * 100)  # lower CPM = higher score
    else:
        cpm_score = 0.0
    components["cpm"] = round(cpm, 2)
    components["cpm_score"] = round(cpm_score, 1)

    # Follow conversion
    follow_rate = _safe_div(entry.follows, max(entry.unique_reach, 1)) * 100
    follow_score = _clamp(follow_rate * 50)  # 2% follow rate = 100
    components["follow_rate_pct"] = round(follow_rate, 3)
    components["follow_score"] = round(follow_score, 1)

    pillar = reach_score * 0.50 + cpm_score * 0.30 + follow_score * 0.20
    return round(_clamp(pillar), 1), components


def score_campaign(
    entry: CampaignEntry,
    weights: Optional[ScoringWeights] = None,
) -> BapScoreResult:
    """Compute the full BAP score for a single campaign entry."""
    if weights is None:
        weights = ScoringWeights()

    recall, recall_comp = score_recall(entry)
    trust, trust_comp = score_trust(entry)
    penetration, pen_comp = score_penetration(entry)

    overall = (
        recall * weights.recall
        + trust * weights.trust
        + penetration * weights.penetration
    )
    overall = round(overall, 1)

    return BapScoreResult(
        campaign_name=entry.campaign_name,
        date=entry.date,
        recall_score=recall,
        trust_score=trust,
        penetration_score=penetration,
        overall_score=overall,
        band=get_band(overall),
        components={
            "recall": recall_comp,
            "trust": trust_comp,
            "penetration": pen_comp,
        },
    )
