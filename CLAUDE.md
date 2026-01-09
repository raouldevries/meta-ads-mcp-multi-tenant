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

### Required Environment Variables
- `META_ACCESS_TOKEN` - Meta API access token
- `META_APP_ID` - Meta App ID (for OAuth flows)
- `META_AD_ACCOUNT_ID` - Default ad account ID (format: act_XXXXXXXXX)

## Key Configuration Files

| File | Purpose |
|------|---------|
| `meta-ads-mcp/.env` | Local environment variables (tokens, app IDs) |
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

## Custom Commands

- **"Big Tony"** or **"call Tony"**: Run `/big-tony` to review and fix code issues
