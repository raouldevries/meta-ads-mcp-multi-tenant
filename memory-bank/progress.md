# Meta Ads MCP Server Setup Progress

**Date:** 2026-01-08 (Updated)
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

## Available MCP Tools (63 total)

### Core Account & Campaign Tools
- get_ad_accounts, get_account_info, get_campaigns, get_campaign_details
- get_adsets, get_adset_details, get_ads, get_ad_details
- get_ad_creatives, get_ad_image

### Management Tools
- create_campaign, create_adset, create_ad, create_ad_creative
- update_campaign, update_ad, update_adset, update_ad_creative, upload_ad_image

### Targeting Tools
- search_interests, get_interest_suggestions, estimate_audience_size
- search_behaviors, search_demographics, search_geo_locations

### Insights & Analytics Tools (NEW - 2026-01-08)
- get_insights (enhanced with action_breakdowns, filtering, sort, time_increment)
- get_insights_by_time, get_insights_with_actions
- get_async_job_status, get_async_job_results
- get_video_insights, get_demographic_insights
- get_placement_insights, get_device_insights
- get_deleted_archived_insights

### Audience Tools (NEW - 2026-01-08)
- get_custom_audiences, get_custom_audience_details
- get_saved_audiences, get_saved_audience_details

### Pixel & Conversion Tools (NEW - 2026-01-08)
- get_pixels, get_pixel_details, get_pixel_stats
- get_pixel_events, get_pixel_code
- get_custom_conversions, get_custom_conversion_details
- get_offline_conversion_data_sets

### Lead Generation Tools (NEW - 2026-01-08)
- get_lead_forms, get_lead_form_details
- get_leads, get_ad_leads (requires leads_retrieval permission)
- get_page_lead_access, get_lead_gen_quality_score

### Ad Preview Tools (NEW - 2026-01-08)
- get_ad_previews, get_ad_preview_all_formats, get_creative_previews

### Other Tools
- create_budget_schedule, get_account_pages, search, fetch, search_pages_by_name
- search_ads_archive, get_login_link

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

## Extended API Coverage (2026-01-08)

### Overview

Performed comprehensive Meta API permission audit and added 31 new read-only tools across 5 areas. Total tools increased from 26 to 63.

### New Modules Created

| Module | Tools | Description |
|--------|-------|-------------|
| `audiences.py` | 4 | Custom Audiences and Saved Audiences read-only access |
| `pixels.py` | 9 | Meta Pixel management, stats, custom conversions |
| `leads.py` | 6 | Lead forms and lead retrieval (requires `leads_retrieval` permission) |

### Enhanced Modules

| Module | Changes |
|--------|---------|
| `insights.py` | Added 10 new functions + enhanced `get_insights` with action_breakdowns, filtering, sort, time_increment, custom fields |
| `ads.py` | Added 3 preview functions for ad rendering |

### Key Features Added

**Insights API Enhancements:**
- Action breakdowns (action_type, action_device, action_destination, etc.)
- Filtering support for insights queries
- Sorting by any metric
- Time increment for daily/weekly/monthly breakdowns
- Async job support for large queries
- Video completion metrics (video_p25_watched_actions, etc.)
- Specialized helpers: demographic, placement, device insights

**Audience Management:**
- Custom audience listing with subtype filtering
- Saved audience (targeting presets) access
- Lookalike audience specifications

**Pixel & Conversion Tracking:**
- Meta Pixel listing and details
- Pixel stats by event, device, browser
- Pixel JavaScript code retrieval
- Custom conversions and offline data sets

**Lead Generation:**
- Lead form listing and details
- Lead retrieval from forms and ads
- Quality scores and page access permissions

### Testing

All 257 tests passed after implementation and audit fixes.

### Permissions Note

Most new tools work with existing `ads_read` permission. Exception:
- `get_leads` and `get_ad_leads` require `leads_retrieval` permission (App Review required)

---

## Git History

| Commit | Description |
|--------|-------------|
| `4f5aa5e` | Add extended Meta API coverage with read-only tools |
| `512b81b` | Add CLAUDE.md to gitignore |
| `abd8599` | Add video completion metrics and scalable architecture plan |
| `9fa377e` | Fix Ad Library API: update deprecated fields and add separate token support |
| `2d3dd0c` | Update progress documentation |
| `c46244e` | Fix multiple bugs found during code review |
| `31aea3c` | Add git history to progress documentation |
| `a92f664` | Complete Meta Ads MCP setup (Steps 5-6) |
| `1f28ac2` | Initial commit: Meta Ads MCP server setup |
