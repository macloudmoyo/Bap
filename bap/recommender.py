"""Recommendation engine for the Humble Roots BAP Framework.

Generates actionable advice based on BAP scores and sub-metrics.
"""

from .models import AdFormat, BapScoreResult, Rating


def generate_recommendations(result: BapScoreResult) -> list[str]:
    """Return a prioritised list of recommendations based on BAP metrics."""
    recs = []

    # ── Overall rating-based recommendations ────────────────────────────
    if result.rating == Rating.POOR:
        recs.append(
            "OVERALL: BAP score is Poor (%.2f). This campaign is not building "
            "meaningful brand awareness. Consider pausing, reworking the creative "
            "strategy, and re-launching with a focused test budget." % result.bap
        )
    elif result.rating == Rating.GOOD:
        recs.append(
            "OVERALL: BAP score is Good (%.2f) but has room to improve. "
            "Focus on the weakest sub-metric first — small wins there will "
            "lift the overall score fastest." % result.bap
        )

    # ── Awareness Penetration (AP) ──────────────────────────────────────
    if result.ap < 0.05:
        recs.append(
            "[Penetration] AP is very low (%.1f%%). You're barely reaching your ICP. "
            "Increase daily budget or switch to the Reach/Brand Awareness objective "
            "to maximise unique impressions." % (result.ap * 100)
        )
    elif result.ap < 0.15:
        recs.append(
            "[Penetration] AP is below average (%.1f%%). Review your targeting — "
            "are filters too broad? Narrow to your core ICP and layer in matched "
            "audiences (company lists, retargeting) for deeper penetration."
            % (result.ap * 100)
        )

    # ── Dwell time ──────────────────────────────────────────────────────
    if result.dwell_index < 0.8 and result.dwell_index > 0:
        recs.append(
            "[Attention] Dwell time is below baseline (index: %.2f). People aren't "
            "stopping to read. Test stronger visual hooks — bold headlines, faces, "
            "data visualisations, or contrarian statements that break the scroll."
            % result.dwell_index
        )
    elif result.dwell_index >= 1.5:
        recs.append(
            "[Attention] Excellent dwell time (index: %.2f) — people are genuinely "
            "engaging with this content. Consider extending this creative's run or "
            "repurposing the concept across other formats." % result.dwell_index
        )

    # ── CTR ─────────────────────────────────────────────────────────────
    if result.ctr_index < 0.7 and result.ctr_index > 0:
        recs.append(
            "[CTR] Click-through is well below baseline (index: %.2f). A/B test "
            "your CTA copy and consider adding social proof (logos, testimonials) "
            "in the creative. Carousel and video formats typically earn higher "
            "CTR on LinkedIn." % result.ctr_index
        )
    elif result.ctr_index < 1.0 and result.ctr_index > 0:
        recs.append(
            "[CTR] Click-through is slightly below baseline (index: %.2f). "
            "Test different headline hooks — lead with a bold stat, question, "
            "or insight that creates curiosity." % result.ctr_index
        )

    # ── View rate (video/doc formats) ───────────────────────────────────
    if result.view_index > 0 and result.view_index < 0.8:
        recs.append(
            "[Views] View rate is below baseline (index: %.2f). For video, "
            "front-load your key message in the first 3 seconds and add captions "
            "(85%% of LinkedIn video is watched on mute). For carousels/docs, "
            "make the cover slide irresistible." % result.view_index
        )

    # ── Completion rate ─────────────────────────────────────────────────
    if result.completion_index > 0 and result.completion_index < 0.7:
        recs.append(
            "[Completion] Completion rate is well below baseline (index: %.2f). "
            "Content is too long or loses attention mid-way. Keep videos under "
            "30s for awareness campaigns. For docs/carousels, aim for 5-7 slides "
            "max with a strong payoff on the last slide." % result.completion_index
        )

    # ── Cost efficiency ─────────────────────────────────────────────────
    if result.cost_per_bap > 200 and result.spend > 0:
        recs.append(
            "[Efficiency] Cost per BAP is high (£%.2f). Review your bid strategy — "
            "consider manual bidding with a CPM cap. Also check audience overlap "
            "with other campaigns, as internal competition drives up costs."
            % result.cost_per_bap
        )
    elif result.cost_per_bap > 100 and result.spend > 0:
        recs.append(
            "[Efficiency] Cost per BAP is above average (£%.2f). Test broader "
            "audience segments or off-peak scheduling (mornings/weekends) where "
            "competition is lower." % result.cost_per_bap
        )

    # ── Format-specific tips ────────────────────────────────────────────
    if result.ad_format == AdFormat.IMAGE and result.bap < 10:
        recs.append(
            "[Format] Static images have limited engagement ceiling. Consider "
            "testing carousel or short video versions of this campaign to boost "
            "dwell time and view rates."
        )

    if result.ad_format in (AdFormat.VIDEO, AdFormat.VIDEOS):
        if result.completion_index < 0.5 and result.completion_index > 0:
            recs.append(
                "[Video] Very low completion rate. Try cutting the video to under "
                "15 seconds, or restructure with the key value prop in the first "
                "3 seconds followed by a clear CTA."
            )

    # ── Positive reinforcement ──────────────────────────────────────────
    if result.rating == Rating.EXCELLENT:
        recs.append(
            "OVERALL: Excellent BAP score (%.2f). This campaign is delivering strong "
            "brand awareness. Look for incremental gains in your weakest sub-metric "
            "to push into Elite territory." % result.bap
        )
    elif result.rating == Rating.ELITE:
        recs.append(
            "OVERALL: Elite BAP score (%.2f). This campaign is a benchmark performer. "
            "Document what's working (creative, targeting, timing) as a playbook for "
            "future campaigns. Consider increasing spend to scale this winner."
            % result.bap
        )

    if not recs:
        recs.append(
            "OVERALL: BAP score is %.2f (%s). Performance is solid across the board. "
            "Pick one sub-metric to experiment on this week — small focused tests "
            "beat broad changes." % (result.bap, result.rating.value)
        )

    return recs
