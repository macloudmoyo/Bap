"""Recommendation engine that generates actionable advice from BAP scores."""

from .models import BapScoreResult, ScoreBand


def generate_recommendations(result: BapScoreResult) -> list[str]:
    """Return a prioritised list of recommendations based on the BAP scores."""
    recs = []

    # ── Recall recommendations ──────────────────────────────────────────
    rc = result.components.get("recall", {})

    if rc.get("ctr_score", 100) < 40:
        recs.append(
            "[Recall] CTR is weak (%.2f%%). Test stronger hooks in your headline "
            "and creative – lead with a bold stat, question, or contrarian take. "
            "Try carousel or video formats which typically earn higher CTR on LinkedIn."
            % rc.get("ctr_pct", 0)
        )
    elif rc.get("ctr_score", 100) < 60:
        recs.append(
            "[Recall] CTR is moderate (%.2f%%). A/B test your call-to-action copy "
            "and consider adding social proof (logos, testimonials) in the creative."
            % rc.get("ctr_pct", 0)
        )

    freq = rc.get("frequency", 0)
    if freq < 1.5:
        recs.append(
            "[Recall] Frequency is too low (%.1f). Your audience isn't seeing the ad "
            "enough to build recall. Increase budget or narrow your audience to drive "
            "at least 3-5 impressions per person." % freq
        )
    elif freq > 8:
        recs.append(
            "[Recall] Frequency is too high (%.1f) – ad fatigue risk. Rotate creatives "
            "every 2 weeks, expand your audience, or pause and restart with fresh assets."
            % freq
        )

    if rc.get("consistency_score", 100) < 30:
        recs.append(
            "[Recall] Very low unique reach relative to impressions. The same small "
            "group is seeing the ad repeatedly. Broaden targeting or use LinkedIn's "
            "audience expansion to find new pockets of your ICP."
        )

    # ── Trust recommendations ───────────────────────────────────────────
    tc = result.components.get("trust", {})

    if tc.get("engagement_score", 100) < 40:
        recs.append(
            "[Trust] Engagement rate is low (%.2f%%). The audience is scrolling past. "
            "Make the creative more thumb-stopping: use faces, data visualisations, or "
            "short-form video. Test posting organically first to validate the hook."
            % tc.get("engagement_rate_pct", 0)
        )
    elif tc.get("engagement_score", 100) < 60:
        recs.append(
            "[Trust] Engagement is moderate (%.2f%%). Consider adding interactive "
            "elements like polls in organic posts to complement your paid campaign."
            % tc.get("engagement_rate_pct", 0)
        )

    if tc.get("share_score", 100) < 30:
        recs.append(
            "[Trust] Very few shares – your content isn't resonating enough for people "
            "to put their name behind it. Create content that makes the sharer look "
            "smart: original research, surprising stats, or strong opinion pieces."
        )

    if tc.get("comment_score", 100) < 30:
        recs.append(
            "[Trust] Low comment rate. End your ad copy with a direct question to "
            "invite discussion. Respond to every comment to boost the thread and signal "
            "that real humans are behind the brand."
        )

    if "video_score" in tc and tc["video_score"] < 40:
        recs.append(
            "[Trust] Video completion rate is low (%.0f%%). Front-load your key message "
            "in the first 3 seconds. Add captions (85%% of LinkedIn video is watched "
            "on mute). Keep videos under 30s for awareness campaigns."
            % (tc.get("video_completion_rate", 0) * 100)
        )

    # ── Penetration recommendations ─────────────────────────────────────
    pc = result.components.get("penetration", {})

    if pc.get("reach_penetration_pct") is not None and pc["reach_penetration_pct"] < 5:
        recs.append(
            "[Penetration] Only reaching %.1f%% of your target audience. At this pace, "
            "awareness will take too long to build. Increase daily budget or switch to "
            "the Reach objective to maximise unique impressions."
            % pc["reach_penetration_pct"]
        )
    elif pc.get("reach_score", 100) < 40:
        recs.append(
            "[Penetration] Audience penetration is weak. Review your targeting – are "
            "filters too broad? Narrow to your core ICP and layer in matched audiences "
            "(company lists, retargeting) for deeper penetration."
        )

    if pc.get("cpm", 0) > 50:
        recs.append(
            "[Penetration] CPM is high (%.2f). Review your bid strategy – consider "
            "switching to manual bidding with a CPM cap. Also check audience overlap "
            "with other campaigns, as internal competition drives up costs."
            % pc["cpm"]
        )
    elif pc.get("cpm_score", 100) < 40:
        recs.append(
            "[Penetration] Cost efficiency is below average (CPM: %.2f). Test broader "
            "audience segments or off-peak scheduling (mornings/weekends) where "
            "competition is lower." % pc.get("cpm", 0)
        )

    if pc.get("follow_score", 100) < 20:
        recs.append(
            "[Penetration] Almost no follows from this campaign. If company follows "
            "matter to your strategy, add a clear 'Follow us for more' CTA and "
            "ensure your LinkedIn company page is well-optimised."
        )

    # ── Overall band recommendations ────────────────────────────────────
    if result.band == ScoreBand.CRITICAL:
        recs.insert(0,
            "OVERALL: BAP score is Critical (%.1f/100). This campaign is not building "
            "meaningful brand awareness. Consider pausing, reworking the creative "
            "strategy, and re-launching with a focused test budget." % result.overall_score
        )
    elif result.band == ScoreBand.LOW:
        recs.insert(0,
            "OVERALL: BAP score is Low (%.1f/100). The campaign is underperforming. "
            "Focus on the weakest pillar first – small wins there will lift the "
            "overall score fastest." % result.overall_score
        )
    elif result.band == ScoreBand.STRONG:
        recs.append(
            "OVERALL: Strong BAP score (%.1f/100). The campaign is delivering solid "
            "brand awareness. Look for incremental gains in your lowest-scoring pillar "
            "to push into Exceptional territory." % result.overall_score
        )
    elif result.band == ScoreBand.EXCEPTIONAL:
        recs.append(
            "OVERALL: Exceptional BAP score (%.1f/100). This campaign is a benchmark. "
            "Document what's working (creative, targeting, timing) as a playbook for "
            "future campaigns." % result.overall_score
        )

    # If nothing triggered, give a generic nudge
    if not recs:
        recs.append(
            "OVERALL: Moderate BAP score (%.1f/100). Performance is average across the "
            "board. Pick one pillar to experiment on this week – small focused tests "
            "beat broad changes." % result.overall_score
        )

    return recs
