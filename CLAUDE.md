# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Meta Ads Analyzer project that uses a self-hosted Meta Ads MCP (Model Context Protocol) server to interact with Meta's Advertising API. The MCP server enables AI assistants to analyze, manage, and optimize Meta advertising campaigns.

## Repository Structure

```
Meta Ads Analyzer/
├── meta-ads-mcp/           # Cloned from pipeboard-co/meta-ads-mcp
│   ├── meta_ads_mcp/       # Main Python package
│   │   └── core/           # Core modules (server, auth, API tools)
│   ├── tests/              # Integration and unit tests
│   └── venv/               # Python virtual environment
└── memory-bank/            # Project documentation and progress tracking
```

## Development Commands

### Activate Virtual Environment
```bash
cd meta-ads-mcp
source venv/bin/activate
```

### Run MCP Server (stdio mode for Claude Code)
```bash
python -m meta_ads_mcp
```

### Run MCP Server (HTTP mode)
```bash
python -m meta_ads_mcp --transport streamable-http --port 8080 --host localhost
```

### Run Tests
```bash
# Run all unit tests (excludes e2e tests by default)
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_targeting.py -v

# Run e2e tests (requires running MCP server)
python -m pytest tests/ -v -m e2e

# Run with custom server URL
MCP_TEST_SERVER_URL=http://localhost:9000 python -m pytest tests/ -v
```

### Install Package in Development Mode
```bash
pip install -e .
```

## Architecture

### MCP Server (`meta_ads_mcp/core/server.py`)
- Uses FastMCP framework for MCP protocol implementation
- Supports two transports: `stdio` (default for MCP clients) and `streamable-http` (for HTTP API)
- Tools are auto-registered via decorators in the core modules

### Authentication Flow (`meta_ads_mcp/core/auth.py`)
Token precedence: `META_ACCESS_TOKEN` env var > OAuth flow > cached token

### Core Modules
- `accounts.py` - Ad account management tools
- `campaigns.py` - Campaign CRUD operations
- `adsets.py` - Ad set management
- `ads.py` - Ad and creative management
- `insights.py` - Performance metrics and reporting
- `targeting.py` - Audience targeting (interests, behaviors, demographics, geo)

### Authentication Modes

The server supports two authentication modes:

1. **Multi-tenant mode (recommended)** - Uses `credentials.json` for multiple business portfolios
2. **Legacy mode** - Uses `.env` file for single account (backward compatible)

## Multi-Tenant Credentials Setup

### Credentials File Location (Cross-Platform)

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/meta-ads-mcp/credentials.json` |
| Windows | `%APPDATA%\meta-ads-mcp\credentials.json` |
| Linux | `~/.config/meta-ads-mcp/credentials.json` |

### credentials.json Schema (v2)

```json
{
  "version": 2,
  "api_keys": {
    "business_name": {
      "access_token": "YOUR_ACCESS_TOKEN_HERE"
    }
  },
  "accounts": {
    "account_key": {
      "display_name": "Friendly Account Name",
      "ad_account_id": "act_XXXXXXXXX",
      "api_key": "business_name"
    }
  }
}
```

### Structure Explanation

- **api_keys**: Store access tokens per business portfolio. The key name links to accounts below.
- **accounts**: Map friendly names to ad accounts. `api_key` references which token to use.

Multiple ad accounts can share the same token (same business portfolio):

```json
"accounts": {
  "location_a": { "ad_account_id": "act_111", "api_key": "my_business" },
  "location_b": { "ad_account_id": "act_222", "api_key": "my_business" }
}
```

### Legacy Environment Variables (Single Account)

For backward compatibility, you can still use `.env`:
- `META_ACCESS_TOKEN` - Meta API access token
- `META_APP_ID` - Meta App ID (for OAuth flows)
- `META_AD_ACCOUNT_ID` - Default ad account ID (format: act_XXXXXXXXX)

## Key Configuration Files

| File | Purpose |
|------|---------|
| `credentials.json` | Multi-tenant credentials (see paths above) |
| `meta-ads-mcp/.env` | Legacy single-account config (optional) |
| `meta-ads-mcp/pyproject.toml` | Package dependencies and pytest config |
| `~/Library/Application Support/Claude/claude_desktop_config.json` | Claude Desktop MCP config |

## Test Markers

Tests use pytest markers defined in `pyproject.toml`:
- Default: Runs all tests except e2e
- `e2e`: End-to-end tests requiring a running MCP server

## API Notes

- Campaign objectives use ODAX format: `OUTCOME_AWARENESS`, `OUTCOME_TRAFFIC`, `OUTCOME_ENGAGEMENT`, `OUTCOME_LEADS`, `OUTCOME_SALES`, `OUTCOME_APP_PROMOTION`
- Budgets are specified in cents (e.g., 10000 = $100.00)
- Ad account IDs must include the `act_` prefix

## Performance Queries Best Practices

When a user asks performance-related questions about campaigns, ad sets, or ads, **always filter to items with actual ad spend** within the selected period. This is the default behavior for performance analysis.

### Using the `only_with_spend` Parameter

The following tools support `only_with_spend=True` and `time_range` parameters:
- `get_campaigns(account_id, time_range="last_30d", only_with_spend=True)`
- `get_adsets(account_id, time_range="last_30d", only_with_spend=True)`
- `get_ads(account_id, time_range="last_30d", only_with_spend=True)`

### Time Range Options

Use preset strings or custom date ranges:
- Presets: `today`, `yesterday`, `last_7d`, `last_14d`, `last_30d`, `last_90d`, `this_month`, `last_month`, `this_quarter`, `last_quarter`
- Custom: `{"since": "2024-01-01", "until": "2024-01-31"}`

### Analysis Tools

For more detailed performance analysis, use the dedicated analysis tools:
- `get_active_ads_analysis(account_id, time_range, performance_metric)` - Segments ads into top/middle/bottom performers
- `get_campaign_performance_summary(account_id, time_range)` - Campaign-level aggregated metrics

### Example Usage

```python
# Get only campaigns that had spend in the last 30 days
get_campaigns(account_id="act_123456789", time_range="last_30d", only_with_spend=True)

# Get ads with spend, filtered by campaign
get_ads(account_id="act_123456789", campaign_id="123", time_range="last_7d", only_with_spend=True)

# Analyze top and bottom performing ads by CTR
get_active_ads_analysis(account_id="act_123456789", time_range="last_30d", performance_metric="ctr")
```

## Creative Analysis

When analyzing ad creatives (video or image), follow the detailed methodology in `memory-bank/creative-analyzer-agent.md`.

### Quick Reference

**Video Analysis Workflow:**
1. **Subtitle Extraction**: Extract EVERY subtitle (1 frame/second minimum). Classify each as hook/benefit/social_proof/cta.
2. **Frame Visual Analysis**: For each frame, document person (gender, age, expression, eye contact), setting (indoor/outdoor), scene type, and text overlays.
3. **Content-Retention Mapping**: Map each subtitle/frame to the retention curve percentage. Identify critical drop-off points (>20% drop).
4. **Insights Generation**: Identify key issues (weak hook, late key message, late CTA), strengths, and specific recommendations with examples.

**Key Questions to Answer:**
- What's the hook (first 3 seconds)? Is it a question (bad) or outcome (good)?
- Where is the key benefit/outcome mentioned? What % of viewers see it?
- When does the CTA appear? What % of viewers are still watching?
- Is there visual variety or static talking head?

**Common Issues:**
- Question hook format ("Why did you...?") → Replace with outcome statement
- Best content appears late (>10s) → Front-load the value proposition
- CTA when no one watching → Show earlier or create shorter cut

### Creative Analysis Tools

```python
# Unified analysis (auto-detects type)
analyze_creative(ad_id, account_name, time_range, extract_frames=True, extract_subtitles=True)

# Video-specific
analyze_video_creative(ad_id, account_name, time_range, extract_frames=True, extract_subtitles=True)

# Image-specific
analyze_image_creative(ad_id, account_name, time_range, include_benchmarks=True)

# Batch analysis
analyze_account_creatives(account_id, account_name, time_range, limit=20, min_spend=1.0)

# Get insights only
get_creative_insights(ad_id, account_name, time_range)
```

## Custom Commands

- **"Big Tony"** or **"call Tony"**: Run `/big-tony` to review and fix code issues
