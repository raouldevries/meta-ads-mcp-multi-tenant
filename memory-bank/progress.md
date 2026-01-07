# Meta Ads MCP Server Setup Progress

**Date:** 2026-01-06
**Project:** Meta Ads Analyzer
**Goal:** Self-hosted Meta Ads MCP server for Claude Code (and later Claude Desktop)

---

## Environment

- **OS:** macOS (Darwin)
- **Python:** 3.12.12 (installed via Homebrew)
- **MCP Client:** Claude Code (stdio mode)
- **Repository:** https://github.com/pipeboard-co/meta-ads-mcp

---

## Completed Steps

### Step 1: Clone and Install Repository ✅

```bash
cd /Users/raouldevries/Work/Apps/Meta\ Ads\ Analyzer
git clone https://github.com/pipeboard-co/meta-ads-mcp.git
```

Installed Python 3.12 via Homebrew (system had Python 3.9 which was insufficient):
```bash
brew install python@3.12
```

Created virtual environment and installed package:
```bash
cd meta-ads-mcp
/opt/homebrew/bin/python3.12 -m venv venv
source venv/bin/activate
pip install -e .
```

**Location:** `/Users/raouldevries/Work/Apps/Meta Ads Analyzer/meta-ads-mcp`

---

### Step 2: Configure Environment Variables ✅

Created `.env` file at: `/Users/raouldevries/Work/Apps/Meta Ads Analyzer/meta-ads-mcp/.env`

Contains:
- `META_APP_ID`
- `META_APP_SECRET`
- `META_ACCESS_TOKEN`
- `META_AD_ACCOUNT_ID`

---

### Step 3: Verify API Connection ✅

Tested Meta API connection - **SUCCESS**
- Connected as: Conversions API System User
- Ad account found: Solutions Engineering Team - Advertentieaccount (act_576714580087420)

---

### Step 4: Configure Claude Code MCP ✅

Added MCP server to Claude Code:
```bash
claude mcp add --transport stdio meta-ads-mcp \
  -e META_ACCESS_TOKEN="..." \
  -e META_APP_ID="..." \
  -e META_AD_ACCOUNT_ID="..." \
  -- /Users/raouldevries/Work/Apps/Meta\ Ads\ Analyzer/meta-ads-mcp/venv/bin/python -m meta_ads_mcp
```

Verified connection:
```bash
claude mcp list
# Output: meta-ads-mcp: ✓ Connected
```

---

### Step 5: Test Full Integration ✅

**Completed:** 2026-01-06

Successfully tested Meta API connection and retrieved ad accounts:

| Field | Value |
|-------|-------|
| Account ID | `act_576714580087420` |
| Name | Solutions Engineering Team - Advertentieaccount |
| Status | Active |
| Amount Spent | €65,631.03 |
| Balance | €418.55 |
| Currency | EUR |
| Location | Arnhem, NL |

---

### Step 6: Configure Claude Desktop ✅

**Completed:** 2026-01-06

Created config file at: `~/Library/Application Support/Claude/claude_desktop_config.json`

Configuration includes:
- Command: Python from virtual environment
- Args: `-m meta_ads_mcp`
- Environment variables: META_ACCESS_TOKEN, META_APP_ID, META_AD_ACCOUNT_ID

**Note:** Restart Claude Desktop to load the new MCP server configuration.

---

## Available MCP Tools (26 total)

**Core:**
- get_ad_accounts, get_account_info, get_campaigns, get_campaign_details
- get_adsets, get_adset_details, get_ads, get_ad_details
- get_insights, get_ad_creatives, get_ad_image

**Management:**
- create_campaign, create_adset, create_ad, create_ad_creative
- update_ad, update_adset, upload_ad_image

**Targeting:**
- search_interests, get_interest_suggestions, validate_interests
- search_behaviors, search_demographics, search_geo_locations

**Other:**
- create_budget_schedule, get_account_pages, search

---

## Key Paths

| Item | Path |
|------|------|
| Project root | `/Users/raouldevries/Work/Apps/Meta Ads Analyzer` |
| MCP repo | `/Users/raouldevries/Work/Apps/Meta Ads Analyzer/meta-ads-mcp` |
| Virtual env | `/Users/raouldevries/Work/Apps/Meta Ads Analyzer/meta-ads-mcp/venv` |
| .env file | `/Users/raouldevries/Work/Apps/Meta Ads Analyzer/meta-ads-mcp/.env` |
| Python binary | `/Users/raouldevries/Work/Apps/Meta Ads Analyzer/meta-ads-mcp/venv/bin/python` |
| Claude Desktop config | `~/Library/Application Support/Claude/claude_desktop_config.json` |

---

## Troubleshooting

If MCP connection fails:
1. Check token validity: `echo $META_ACCESS_TOKEN`
2. Verify server starts: `cd meta-ads-mcp && source venv/bin/activate && python -m meta_ads_mcp`
3. Check Claude MCP config: `claude mcp list`
4. Restart Claude Code after config changes

---

## Setup Complete

All steps completed successfully on 2026-01-06.

The Meta Ads MCP server is now available in:
- **Claude Code** - Ready to use immediately
- **Claude Desktop** - Restart the app to activate

---

## Git History

| Commit | Description |
|--------|-------------|
| `31aea3c` | Add git history to progress documentation |
| `a92f664` | Complete Meta Ads MCP setup (Steps 5-6) |
| `1f28ac2` | Initial commit: Meta Ads MCP server setup |
