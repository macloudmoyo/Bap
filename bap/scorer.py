"""Core BAP scoring engine.

Computes the Humble Roots BAP Framework metrics:

  AP  = Awareness Penetration = Reach / ICP Size
  AQI = Awareness Quality Index (composite of dwell, CTR, view, completion
        performance vs baselines)
  BAP = AP × AQI × Reach / 1000  (brand awareness penetration score)

Plus efficiency metrics:
  BAP per £1k  = BAP / Spend × 1000
  Cost per BAP = Spend / BAP
"""

from .models import BapScoreResult, CampaignEntry, Rating, get_rating


def _safe_div(num: float, den: float, default: float = 0.0) -> float:
    return num / den if den else default


def score_campaign(entry: CampaignEntry) -> BapScoreResult:
    """Compute the full BAP score for a single campaign entry."""

    # ── AP: Awareness Penetration ───────────────────────────────────────
    ap = _safe_div(entry.reach, entry.icp_size)

    # ── AQI: Awareness Quality Index ────────────────────────────────────
    # Each component compares actual performance to baseline, rewarding
    # above-baseline performance with a multiplier.

    # 1. Dwell index – time spent with the ad vs baseline
    if entry.baseline_dwell > 0:
        dwell_index = entry.avg_dwell / entry.baseline_dwell
    else:
        # No baseline: use raw dwell, 3s is par
        dwell_index = min(entry.avg_dwell / 3.0, 3.0) if entry.avg_dwell > 0 else 0.0

    # 2. CTR index – click-through vs baseline
    if entry.baseline_ctr > 0:
        ctr_index = entry.ctr / entry.baseline_ctr
    else:
        # No baseline: use absolute CTR, 0.4% is par for LinkedIn
        ctr_index = min(entry.ctr / 0.4, 3.0) if entry.ctr > 0 else 0.0

    # 3. View index – view rate vs baseline (mainly for video/doc)
    if entry.baseline_view_rate > 0:
        view_index = entry.view_rate / entry.baseline_view_rate
    else:
        view_index = min(entry.view_rate / 20.0, 3.0) if entry.view_rate > 0 else 0.0

    # 4. Completion index – completion rate vs baseline
    if entry.baseline_completion_rate > 0:
        completion_index = entry.completion_rate / entry.baseline_completion_rate
    else:
        completion_index = (
            min(entry.completion_rate / 1.0, 3.0) if entry.completion_rate > 0 else 0.0
        )

    # Combine into AQI – weight depends on format
    has_video_data = entry.total_views > 0 or entry.view_rate > 0
    if has_video_data:
        # Video / doc formats: all four components
        aqi = (
            dwell_index * 0.25
            + ctr_index * 0.25
            + view_index * 0.30
            + completion_index * 0.20
        ) * 10  # scale to roughly 0-30 range
    else:
        # Static formats (image, single): dwell + CTR only
        aqi = (
            dwell_index * 0.50
            + ctr_index * 0.50
        ) * 10

    # ── BAP: Brand Awareness Penetration ────────────────────────────────
    bap = aqi * entry.reach / 1000

    # ── Efficiency metrics ──────────────────────────────────────────────
    bap_per_1k = _safe_div(bap, entry.spend) * 1000
    cost_per_bap = _safe_div(entry.spend, bap)

    # ── Rating ──────────────────────────────────────────────────────────
    rating = get_rating(bap)

    return BapScoreResult(
        campaign_name=entry.campaign_name,
        ad_format=entry.ad_format,
        ap=round(ap, 4),
        aqi=round(aqi, 2),
        bap=round(bap, 2),
        bap_per_1k=round(bap_per_1k, 2),
        cost_per_bap=round(cost_per_bap, 2),
        rating=rating,
        dwell_index=round(dwell_index, 3),
        ctr_index=round(ctr_index, 3),
        view_index=round(view_index, 3),
        completion_index=round(completion_index, 3),
        icp_size=entry.icp_size,
        reach=entry.reach,
        spend=entry.spend,
    )
