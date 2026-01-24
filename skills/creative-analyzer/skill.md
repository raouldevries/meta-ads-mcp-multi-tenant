# Creative Analyzer Skill

## Metadata

| Field | Value |
|-------|-------|
| **Name** | creative-analyzer |
| **Version** | 1.0.0 |
| **Author** | Meta Ads MCP Team |
| **Description** | Analyze Meta Ads image and video creatives with performance correlation |
| **Triggers** | "analyze creative", "analyze ad", "why is this ad performing", "creative analysis" |

## When to Activate

Activate this skill when the user:
- Asks to analyze an ad creative (video or image)
- Wants to understand why an ad is performing well or poorly
- Asks about video retention, hook effectiveness, or creative improvements
- Wants to compare creative performance to benchmarks
- Requests A/B testing recommendations for creatives

## Required MCP Tools

This skill requires the following tools from `meta-ads-mcp`:
- `analyze_video_creative()` - Video creative analysis with frame extraction
- `get_ad_image()` - Fetch ad image for analysis
- `get_ads()` - Fetch ad metadata
- `get_video_insights()` - Video retention metrics

## Quick Start

```
1. User provides: ad_id or ad name + account
2. Detect creative type (image vs video)
3. Load appropriate workflow from ./workflows/
4. Execute analysis phases
5. Generate HTML report (optional)
```

## Directory Structure

```
creative-analyzer/
├── skill.md                    # This file - metadata & entry point
├── README.md                   # How the full app works
├── workflows/
│   ├── video-analysis.md       # Video analysis workflow
│   └── image-analysis.md       # Image analysis workflow
├── scripts/
│   └── generate_report.py      # HTML report generator
├── templates/
│   └── report.html             # HTML report template
└── data/
    └── benchmarks.json         # Industry benchmarks
```

## Entry Point

When activated, follow this decision tree:

```
                    ┌─────────────────┐
                    │  User Request   │
                    │ (analyze ad X)  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Fetch Ad Data  │
                    │  via MCP Server │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Detect Creative │
                    │     Type        │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
         ┌────────┐    ┌────────┐    ┌────────┐
         │ VIDEO  │    │ IMAGE  │    │CAROUSEL│
         └───┬────┘    └───┬────┘    └───┬────┘
             │             │             │
             ▼             ▼             ▼
    workflows/      workflows/      (analyze each
    video-          image-          asset separately)
    analysis.md     analysis.md
```

## Output Schema

All analyses produce this standardized output:

```json
{
  "ad_id": "string",
  "ad_name": "string",
  "creative_type": "video|image|carousel",
  "summary": {
    "spend": 0.00,
    "impressions": 0,
    "key_finding": "string"
  },
  "performance": {
    "metrics": {},
    "vs_benchmark": {}
  },
  "analysis": {
    "visual": {},
    "content": {},
    "retention": {}
  },
  "issues": [],
  "strengths": [],
  "recommendations": []
}
```

## Escalation

If analysis cannot be completed:
1. Missing ad data → Ask user for correct ad_id or account
2. No frames extractable → Fall back to thumbnail analysis
3. No retention data → Focus on visual/content analysis only
