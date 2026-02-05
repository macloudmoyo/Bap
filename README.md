# BAP — Brand Awareness Penetration Scoring

Automated scoring framework that measures how much brand recall and trust your LinkedIn ads generate over time. Replaces the manual spreadsheet workflow with a CLI tool that scores campaigns and generates actionable recommendations.

## How It Works

BAP scores each campaign across **three pillars** (each 0–100), then combines them into an overall BAP score:

| Pillar | Weight | What it measures |
|---|---|---|
| **Recall** | 35% | Are people seeing and remembering the ads? (CTR, frequency, reach consistency) |
| **Trust** | 35% | Are people engaging meaningfully? (engagement rate, shares, comments, video completion) |
| **Penetration** | 30% | How deeply is the campaign reaching the target audience? (reach %, CPM efficiency, follows) |

### Score Bands

| Band | Score | Meaning |
|---|---|---|
| Critical | 0–19 | Not building awareness — consider pausing |
| Low | 20–39 | Underperforming — focus on weakest pillar |
| Moderate | 40–59 | Average — pick one area to experiment on |
| Strong | 60–79 | Solid — look for incremental gains |
| Exceptional | 80–100 | Benchmark — document what's working |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate a blank CSV template
python -m bap template -o my_campaigns.csv

# Score your campaigns
python -m bap score my_campaigns.csv

# Score and export results to CSV
python -m bap score my_campaigns.csv -o results.csv

# Try with sample data
python -m bap score sample_data.csv
```

## CSV Format

Your input CSV needs at minimum a `campaign_name` column. All other columns are optional but improve scoring accuracy. The tool recognises common column name variations (e.g., `clicks` or `link_clicks`, `spend` or `cost`).

| Column | Required | Description |
|---|---|---|
| campaign_name | Yes | Name of the campaign |
| date | No | Date of the data (YYYY-MM-DD) |
| objective | No | Campaign objective (brand_awareness, engagement, website_visits, video_views, lead_gen) |
| ad_format | No | Ad format (single_image, carousel, video, text, event, document) |
| impressions | No | Total impressions |
| unique_reach | No | Unique people reached |
| frequency | No | Average frequency (impressions per person) |
| clicks | No | Link clicks |
| reactions | No | Likes/reactions |
| comments | No | Comments |
| shares | No | Shares/reposts |
| follows | No | New followers |
| video_views | No | Video views (for video ads) |
| video_completions | No | Completed video views |
| spend | No | Total spend |
| target_audience_size | No | Total size of target audience |

## Custom Weights

Adjust pillar weights based on your priorities:

```bash
# Prioritise trust-building over reach
python -m bap score data.csv --weight-recall 0.25 --weight-trust 0.50 --weight-penetration 0.25
```

Weights must sum to 1.0.

## Project Structure

```
bap/
  __init__.py         # Package init
  __main__.py         # python -m bap entry point
  models.py           # Data models (CampaignEntry, BapScoreResult, enums)
  scorer.py           # Core scoring engine (recall, trust, penetration)
  recommender.py      # Recommendation engine
  csv_io.py           # CSV import/export with flexible column mapping
  cli.py              # Command-line interface
sample_data.csv       # Example data to test with
```
