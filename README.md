# BAP — Brand Awareness Penetration Scoring

**Humble Roots BAP Framework** — automated scoring that measures how much brand recall and trust your LinkedIn ads generate over time. Replaces the manual spreadsheet with a CLI tool + visual dashboard.

## How It Works

BAP scores each campaign using metrics from your LinkedIn ad data:

| Metric | What it is |
|---|---|
| **AP** (Awareness Penetration) | `Reach / ICP Size` — what % of your target you've reached |
| **AQI** (Awareness Quality Index) | Composite of Dwell time, CTR, View Rate, and Completion Rate vs baselines |
| **BAP** (Brand Awareness Penetration) | `AQI × Reach / 1000` — the headline score |
| **BAP per £1k** | `BAP / Spend × 1000` — efficiency metric |
| **Cost per BAP** | `Spend / BAP` — cost to generate one BAP point |

### AQI Components

AQI compares each metric against its baseline to generate an index:

- **Dwell Index** — Avg Dwell Time / Baseline Dwell
- **CTR Index** — CTR / Baseline CTR
- **View Index** — View Rate / Baseline View Rate (video/doc formats)
- **Completion Index** — Completion Rate / Baseline Completion Rate (video/doc formats)

Static formats (Image, Single) use Dwell + CTR only. Video/Doc formats use all four.

### Rating Bands

| Rating | Meaning |
|---|---|
| **Poor** | Not building awareness — consider pausing |
| **Good** | Underperforming — focus on weakest metric |
| **Great** | Solid — look for incremental gains |
| **Excellent** | Strong — push for Elite territory |
| **Elite** | Benchmark — document and scale what's working |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate a blank CSV template matching your spreadsheet
python -m bap template -o my_campaigns.csv

# Score your campaigns (CLI output with recommendations)
python -m bap score my_campaigns.csv

# Generate a visual HTML dashboard
python -m bap dashboard my_campaigns.csv

# Export scored results back to CSV
python -m bap score my_campaigns.csv -o results.csv
```

## CSV Format

Matches the Humble Roots BAP Framework spreadsheet. The tool recognises common column name variations.

| Column | Description |
|---|---|
| Format | Ad format: Image, Single, Doc/Cara, Video, Videos |
| Campaign / Ad name | Campaign name |
| ICP Size | Total ideal customer profile audience size |
| Reach (unique) | Unique people reached |
| Avg Dwell (s) | Average dwell time in seconds |
| Baseline Dwell (s) | Baseline dwell time for comparison |
| CTR (%) | Click-through rate |
| Baseline CTR (%) | Baseline CTR for comparison |
| View Rate (%) | View rate (video/doc formats) |
| Baseline View Rate (%) | Baseline view rate |
| Views @25% | Views reaching 25% |
| Views @50% | Views reaching 50% |
| Views @75% | Views reaching 75% |
| Total Views | Total video/doc views |
| Completion Rate (%) | Content completion rate |
| Baseline Completion Rate (%) | Baseline completion rate |
| Spend (£) | Total spend |

## Dashboard

Run `python -m bap dashboard your_data.csv` to generate an interactive HTML dashboard with:

- KPI summary cards (campaigns, avg BAP, total spend, top performer)
- BAP score bar chart ranked by performance
- Rating distribution doughnut chart
- AQI radar chart comparing quality indices across campaigns
- BAP vs Spend scatter plot for efficiency analysis
- Performance breakdown by ad format
- Awareness Penetration (AP) comparison
- Full scorecard table with colour-coded ratings
- Prioritised recommendations for every campaign

## Project Structure

```
bap/
  __init__.py         # Package init
  __main__.py         # python -m bap entry point
  models.py           # Data models (CampaignEntry, BapScoreResult, ratings)
  scorer.py           # Core scoring engine (AP, AQI, BAP)
  recommender.py      # Recommendation engine
  csv_io.py           # CSV import/export with flexible column mapping
  cli.py              # Command-line interface
  dashboard.py        # HTML dashboard generator
sample_data.csv       # Example data to test with
```
