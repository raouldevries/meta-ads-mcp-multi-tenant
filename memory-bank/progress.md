# Meta Ads MCP Server Setup Progress

**Date:** 2026-01-21 (Updated)
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

## Improvement Plan Implementation (2026-01-09)

### Step 1.1: Centralized Retry/Backoff ✅

**Completed:** 2026-01-09

Implemented a production-grade retry mechanism with exponential backoff for handling Meta API rate limits and transient errors.

#### Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `meta_ads_mcp/core/retry.py` | Created | New retry module with complete implementation |
| `meta_ads_mcp/core/__init__.py` | Modified | Exported retry components |
| `meta_ads_mcp/core/api.py` | Modified | Integrated retry imports |

#### Key Components

**RetryConfig class:**
- 16 Meta API error codes mapped with specific retry counts
- 5 HTTP status codes for retry handling (429, 500, 502, 503, 504)
- Exponential backoff: 1s → 2s → 4s → 8s... up to 60s max
- Jitter support (up to 1 second randomization)
- Honors server-provided `Retry-After` headers

**MetaApiError exception:**
- Rich error capture (code, subcode, type, status, trace_id)
- `is_retryable` property for intelligent retry decisions
- `to_dict()` for JSON serialization
- Comprehensive `__str__` for logging

**with_retry decorator:**
- Async-aware implementation
- Configurable max_retries and retry_on_all_errors
- Intelligent error-specific retry counts
- Detailed logging at each attempt

**parse_meta_error function:**
- Extracts all error details from Meta API responses
- Handles Retry-After header from multiple locations

#### Error Codes Handled

| Error Code | Description | Default Retries |
|------------|-------------|-----------------|
| 1 | Unknown error | 2 |
| 2 | Service unavailable | 3 |
| 4 | Rate limit (app level) | 3 |
| 17 | Rate limit (user level) | 3 |
| 32 | Rate limit (page level) | 3 |
| 613 | Rate limit (calls) | 3 |
| 80000 | Async job failure | 2 |
| 80004 | Transient error | 3 |
| 190 | Invalid token | 0 (no retry) |
| 200 | Permission error | 0 (no retry) |
| 100 | Invalid parameter | 0 (no retry) |

#### Completed Steps

- [x] Create `retry.py` module (RetryConfig, MetaApiError, with_retry decorator)
- [x] Export retry module from `__init__.py`
- [x] Add retry imports to `api.py`
- [x] Apply `@with_retry` decorator to `make_api_request` function
- [x] Add unit tests (`tests/test_retry.py`) - 36 tests passing

#### Test Results

```
293 passed, 9 skipped, 2 deselected in 2.51s
```

---

### Step 1.2: Health Check Tool ✅

**Completed:** 2026-01-09

Implemented a diagnostic health check tool for validating Meta API connectivity and token status.

#### Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `meta_ads_mcp/core/accounts.py` | Modified | Added `health_check` tool function |
| `tests/test_health_check.py` | Created | Comprehensive test suite (9 tests) |

#### Key Features

**health_check tool:**
- Token validation via Meta's `debug_token` API
- Ad accounts accessibility check
- API latency measurement (per-check and total)
- Diagnostics output (API base, timestamp)

**Status Levels:**
| Status | Condition |
|--------|-----------|
| `healthy` | Token valid + accounts accessible |
| `degraded` | Token valid but accounts inaccessible |
| `unhealthy` | Token invalid |
| `error` | No token configured or exception |

**Response Format:**
```json
{
  "status": "healthy|degraded|unhealthy|error",
  "checks": {
    "token": {"status": "present", "prefix": "EAAx..."},
    "token_validation": {"status": "valid", "app_id": "...", "scopes": [...]},
    "ad_accounts": {"status": "accessible", "count": 2, "sample": [...]}
  },
  "diagnostics": {
    "total_latency_ms": 450,
    "api_base": "https://graph.facebook.com/v22.0",
    "timestamp": "2026-01-09T10:00:00Z"
  }
}
```

#### Test Coverage

| Test | Description |
|------|-------------|
| `test_health_check_no_token` | Returns error when no token configured |
| `test_health_check_healthy` | Returns healthy with valid token and accounts |
| `test_health_check_invalid_token` | Returns unhealthy for invalid tokens |
| `test_health_check_degraded_status` | Returns degraded when token valid but accounts fail |
| `test_health_check_with_explicit_token` | Uses explicitly provided token |
| `test_health_check_api_error_handling` | Handles API exceptions gracefully |
| `test_health_check_includes_diagnostics` | Includes latency and timing info |
| `test_response_is_valid_json` | Validates JSON response format |
| `test_response_has_required_fields` | Validates required response fields |

#### Test Results

```
302 passed, 9 skipped, 2 deselected in 1.32s
```

---

### Step 1.3: API v23.0 Upgrade ✅

**Completed:** 2026-01-09

Upgraded Meta Graph API from v22.0 to v23.0 with configurable version support.

#### Files Modified

| File | Changes |
|------|---------|
| `meta_ads_mcp/core/api.py` | Added configurable API version via `META_API_VERSION` env var |
| `meta_ads_mcp/core/auth.py` | Updated OAuth URLs to use configurable version |
| `meta_ads_mcp/core/pipeboard_auth.py` | Updated token validation URL to use configurable version |
| `README.md` | Added Environment Variables documentation |

#### Key Features

**Configurable API Version:**
- Default: `v23.0` (upgraded from `v22.0`)
- Override via `META_API_VERSION` environment variable
- All API calls now use the configurable version
- Helper functions: `get_api_base_url()`, `get_api_version()`

**Environment Variable:**
```bash
# Use a specific API version
export META_API_VERSION=v22.0
```

**Breaking Change Mitigation:**
- Users can revert to v22.0 if needed by setting the environment variable
- All existing functionality preserved with the new version

#### Test Results

```
302 passed, 9 skipped, 2 deselected in 1.31s
```

---

### Step 1.4: Pagination Helpers ✅

**Completed:** 2026-01-09

Implemented automatic pagination support for fetching all results from paginated Meta API endpoints.

#### Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `meta_ads_mcp/core/pagination.py` | Created | New pagination helper module |
| `meta_ads_mcp/core/campaigns.py` | Modified | Added `fetch_all` parameter to get_campaigns |
| `tests/test_pagination.py` | Created | Comprehensive test suite (31 tests) |

#### Key Components

**PaginationConfig class:**
- DEFAULT_PAGE_SIZE = 25
- MAX_PAGE_SIZE = 100
- MAX_PAGES = 100 (safety limit)
- MAX_ITEMS = 10000 (safety limit)
- REQUEST_TIMEOUT = 30.0 seconds

**fetch_all_pages function:**
- Fetches all pages automatically with configurable limits
- Returns combined data with pagination_info metadata
- Handles API errors, timeouts, and partial results gracefully
- Uses httpx AsyncClient (matching codebase patterns)

**paginate_generator function:**
- Memory-efficient async generator for large datasets
- Yields items one at a time without loading all into memory
- Useful for streaming large result sets

**Helper functions:**
- `add_pagination_params()` - Add limit/after to request params
- `extract_cursor_from_response()` - Extract 'after' cursor
- `has_next_page()` - Check if more pages exist

#### Usage Example

```python
# Single page (default)
result = await get_campaigns(account_id="act_123")

# Fetch all campaigns automatically
result = await get_campaigns(account_id="act_123", fetch_all=True)

# With custom page limit
result = await get_campaigns(account_id="act_123", fetch_all=True, max_pages=10)
```

#### Response Format (fetch_all=True)

```json
{
  "data": [...all items...],
  "pagination_info": {
    "pages_fetched": 5,
    "total_items": 127,
    "complete": true,
    "hit_page_limit": false,
    "hit_item_limit": false,
    "max_pages": 100,
    "max_items": 10000
  }
}
```

#### Test Results

```
333 passed, 9 skipped, 2 deselected in 1.41s
```

---

### Step 2.1: Token Validation Tools ✅

**Completed:** 2026-01-09

Implemented detailed token validation tools for debugging authentication issues and verifying token status.

#### Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `meta_ads_mcp/core/accounts.py` | Modified | Added `get_token_info` and `validate_token` tools |
| `tests/test_token_validation.py` | Created | Comprehensive test suite (17 tests) |

#### Key Components

**get_token_info tool:**
- Retrieves detailed token information via Meta's `debug_token` API
- Returns token type, app ID, user ID, scopes, and permissions
- Calculates expiration time with remaining days/hours
- Shows `granular_scopes` for fine-grained permission inspection

**validate_token tool:**
- Quick pass/fail validation with minimal API overhead
- Uses `/me` endpoint for fast response
- Provides actionable error messages for common errors:
  - Code 190: "Token expired or invalid. Generate new token."
  - Code 102: "Session expired. Re-authenticate."
  - Code 4: "Rate limit hit. Wait and retry."
  - Code 17: "User rate limit. Wait and retry."

#### Response Format (get_token_info)

```json
{
  "is_valid": true,
  "type": "USER",
  "app_id": "123456789",
  "user_id": "987654321",
  "scopes": ["ads_management", "ads_read", "business_management"],
  "granular_scopes": [],
  "expiration": {
    "timestamp": 1234567890,
    "date": "2026-03-10T10:00:00",
    "remaining_days": 60,
    "remaining_hours": 12
  },
  "token_prefix": "EAAx1234567890abc...",
  "api_version": "v23.0"
}
```

#### Response Format (validate_token)

```json
{
  "valid": true,
  "user_id": "123456789",
  "message": "Token is valid and working"
}
```

Or on error:

```json
{
  "valid": false,
  "error_code": 190,
  "message": "Error validating access token",
  "action": "Token expired or invalid. Generate new token."
}
```

#### Test Coverage

| Test | Description |
|------|-------------|
| `test_get_token_info_no_token` | Returns error when no token configured |
| `test_get_token_info_valid_token` | Returns detailed token information |
| `test_get_token_info_with_expiration` | Calculates remaining days/hours |
| `test_get_token_info_api_error` | Handles API errors with error codes |
| `test_get_token_info_with_explicit_token` | Uses explicitly provided token |
| `test_get_token_info_network_error` | Handles network errors gracefully |
| `test_validate_token_no_token` | Returns error when no token |
| `test_validate_token_valid` | Returns success for valid token |
| `test_validate_token_expired` | Handles expired token with action |
| `test_validate_token_rate_limited` | Handles rate limit (code 4) |
| `test_validate_token_session_expired` | Handles session expired (code 102) |
| `test_validate_token_network_error` | Handles network errors |
| `test_validate_token_unknown_error` | Handles unknown error codes |

#### Test Results

```
350 passed, 9 skipped, 2 deselected in 1.34s
```

---

### Step 2.2: Compare Entities Helper ✅

**Completed:** 2026-01-09

Implemented a comparison tool for campaigns, ad sets, or ads to provide side-by-side metrics, rankings, and deltas.

#### Files Modified

| File | Action | Description |
|------|--------|-------------|
| `meta_ads_mcp/core/insights.py` | Modified | Added `compare_entities` tool for multi-entity performance comparison |

#### Key Features

**compare_entities tool:**
- Compares up to 10 entities for a given time range
- Returns metrics per entity plus rankings and averages
- Calculates deltas from average for numeric metrics
- Handles API errors and missing data per entity

#### Response Format

```json
{
  "comparison": {
    "entity_type": "campaign",
    "time_range": "last_30d",
    "metrics": ["spend", "impressions", "clicks"],
    "entity_count": 3
  },
  "entities": [
    {
      "id": "123",
      "name": "Campaign A",
      "metrics": {"spend": "123.45", "impressions": "1000", "clicks": "50"},
      "delta_from_avg": {"spend": "+5.2%"}
    }
  ],
  "rankings": {"spend": {"best": "123", "worst": "456", "ranking": ["123", "456", "789"]}},
  "averages": {"spend": 115.23}
}
```

#### Test Results

Audit: `py_compile` on `meta_ads_mcp/core/insights.py` via venv python (no errors).

---

### Step 2.3: Default Limits & Presets ✅

**Completed:** 2026-01-09

Added field presets and default time range handling to keep insight responses concise and consistent.

#### Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `meta_ads_mcp/core/presets.py` | Created | Added field presets, default limits, and time range presets |
| `meta_ads_mcp/core/insights.py` | Modified | Added `field_preset` support and defaulted to efficiency preset |

#### Key Features

**presets module:**
- Insight presets: basic, efficiency, conversions, video, full
- Campaign field presets: basic, full
- Default limits and time range presets for common contexts

**get_insights updates:**
- Default `time_range` is now `last_30d`
- `field_preset` parameter for preset fields
- Custom `fields` overrides presets

#### Audit

`py_compile` on `meta_ads_mcp/core/presets.py` and `meta_ads_mcp/core/insights.py` via venv python (no errors).

---

### Step 2.4: Get Capabilities Tool ✅

**Completed:** 2026-01-09

Added a discovery tool to list available MCP tools, presets, and defaults for quick self-documentation.

#### Files Modified

| File | Action | Description |
|------|--------|-------------|
| `meta_ads_mcp/core/server.py` | Modified | Added `get_capabilities` tool with presets and tool list output |

#### Key Features

**get_capabilities tool:**
- Lists all registered tools with short descriptions
- Reports API version and tool count
- Returns insight presets, time range presets, and default limits
- Includes common workflow hints for quick onboarding

#### Audit

`py_compile` on `meta_ads_mcp/core/server.py` via venv python (no errors).

---

### Step 3.1: Export to CSV/JSON ✅

**Completed:** 2026-01-09

Added an export helper for insights data to output CSV or JSON for downstream analysis.

#### Files Modified

| File | Action | Description |
|------|--------|-------------|
| `meta_ads_mcp/core/insights.py` | Modified | Added `export_insights` tool for CSV/JSON exports |

#### Key Features

**export_insights tool:**
- Supports JSON or CSV output
- Uses existing `get_insights` with presets and limits
- Returns compact CSV with flattened fields
- Preserves JSON structure for programmatic use

#### Audit

`py_compile` on `meta_ads_mcp/core/insights.py` via venv python (no errors).

---

### Step 3.2: Creative Validation Helpers ✅

**Completed:** 2026-01-09

Added a validation helper to check creative fields, CTA values, and image URL accessibility before submission.

#### Files Modified

| File | Action | Description |
|------|--------|-------------|
| `meta_ads_mcp/core/ads.py` | Modified | Added `validate_creative_specs` tool for creative checks |

#### Key Features

**validate_creative_specs tool:**
- Validates headline, primary text, and description length limits
- Checks CTA type against known Meta values
- Verifies image URL status and content-type
- Returns status, issues, warnings, and recommendations

#### Audit

`py_compile` on `meta_ads_mcp/core/ads.py` via venv python (no errors).

---

### Audit Updates: Improvement Plan ✅

**Completed:** 2026-01-09

Recorded audit findings and an audit-fix checklist in the improvement plan.

#### Files Modified

| File | Action | Description |
|------|--------|-------------|
| `memory-bank/improvement-plan.md` | Modified | Added audit findings section and checklist of required fixes |

---

### Systematic Audit of Improvement Plan ✅

**Completed:** 2026-01-09

Performed comprehensive audit of all improvement plan steps, verified implementations against specifications, and fixed identified issues.

#### Audit Summary

| Step | Status | Issues Found | Resolution |
|------|--------|--------------|------------|
| 1.1.1 | ✅ Verified | None | N/A |
| 1.1.2 | ✅ Verified | None | N/A |
| 1.1.3 | 🐛 Bug Fixed | `http_status` attribute error | Changed to `status_code` |
| 1.1.4 | ✅ Verified | None | N/A |
| 1.2.x | ✅ Verified | None | N/A |
| 1.3.x | ✅ Verified | None | N/A |
| 1.4.x | ✅ Verified | None | N/A |
| 2.1.1 | ✅ Verified | None | N/A |
| 2.2.x | ✅ Verified | None | N/A |
| 2.3.x | ✅ Verified | None | N/A |
| 2.4.x | ✅ Verified | None | N/A |
| 3.1.x | ✅ Verified | None | N/A |
| 3.2.x | ✅ Verified | None | N/A |

#### Critical Bug Fixed

**File:** `meta_ads_mcp/core/api.py`
**Issue:** Lines 190 and 211 referenced `e.http_status` but `MetaApiError` class defines `status_code`
**Impact:** Would cause `AttributeError` when handling auth errors (401/403)
**Fix:** Changed `e.http_status` → `e.status_code` in both locations

#### Verification

- All 348+ tests pass after fix
- No regressions introduced
- Bug would have caused runtime errors in error handling path

---

### Only With Spend Filter Default Change (2026-01-09)

**Completed:** 2026-01-09

Changed the default value of `only_with_spend` parameter from `False` to `True` in all Meta API query tools. This ensures users only see data for items with actual ad spend in the selected period by default.

#### Files Modified

| File | Functions Updated |
|------|-------------------|
| `meta_ads_mcp/core/campaigns.py` | `get_campaigns` |
| `meta_ads_mcp/core/adsets.py` | `get_adsets` |
| `meta_ads_mcp/core/ads.py` | `get_ads` |
| `meta_ads_mcp/core/insights.py` | `get_insights`, `get_insights_by_time`, `get_insights_with_actions`, `get_video_insights`, `get_demographic_insights`, `get_placement_insights`, `get_device_insights` |

#### Behavior Change

| Before | After |
|--------|-------|
| `only_with_spend=False` (default) | `only_with_spend=True` (default) |
| Returns all items regardless of spend | Returns only items with spend > 0 |
| User must opt-in to filter by spend | User must opt-out to see all items |

#### User Message

All filtered responses now include a message:
> "Showing X items with ad spend in the selected period. Set only_with_spend=False to include all Y items."

---

### Headline Performance Analysis Tool (2026-01-09)

**Completed:** 2026-01-09

Added a new tool `get_headline_performance` to analyze ad copy performance across all ads, including flexible ad (Advantage+ Creative) headline variants.

#### Files Modified

| File | Action | Description |
|------|--------|-------------|
| `meta_ads_mcp/core/analysis.py` | Modified | Added `get_headline_performance` tool |

#### Problem Solved

The existing analysis tools couldn't extract headlines from Advantage+ Creative (flexible) ads because:
- Flexible ad headlines are stored in `asset_feed_spec.titles`, not the standard `title` field
- The nested query `/{ad_id}?fields=creative{asset_feed_spec}` doesn't return the full data
- Needed to use the `/adcreatives` endpoint to get complete creative data

#### Key Features

**get_headline_performance tool:**
- Extracts all creative text elements from both flexible and standard ads
- Headlines: `asset_feed_spec.titles` (flexible) or `object_story_spec.link_data.name` (standard)
- Primary texts: `asset_feed_spec.bodies` (flexible) or `object_story_spec.link_data.message` (standard)
- Descriptions: `asset_feed_spec.descriptions` (flexible) or `object_story_spec.link_data.description` (standard)
- Returns performance metrics (CTR, CPC, spend, impressions) alongside each headline
- Sorts by worst performers first (default) to find problem headlines
- Provides summary statistics including content coverage counts

#### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `account_id` | required | Meta Ads account ID (act_XXXXXXXXX) |
| `time_range` | `last_30d` | Time range preset or custom date range |
| `min_impressions` | 100 | Minimum impressions threshold |
| `min_spend` | 1.0 | Minimum spend threshold |
| `sort_by` | `ctr` | Metric to sort by (ctr, cpc, spend, impressions) |
| `sort_order` | `asc` | Sort order (asc = worst first) |
| `limit` | 50 | Maximum ads to return |

#### Response Format

```json
{
  "summary": {
    "total_ads_analyzed": 94,
    "content_coverage": {
      "ads_with_headlines": 85,
      "ads_with_primary_texts": 72,
      "ads_with_descriptions": 45,
      "ads_without_headlines": 9
    },
    "headline_sources": {
      "flexible_ad": 45,
      "standard_ad": 40,
      "none": 9
    }
  },
  "ads": [
    {
      "ad_id": "120237045902150619",
      "ad_name": "Video ad - Member – Aan 't IJ",
      "ctr": 0.145,
      "spend": 319.48,
      "headlines": ["Sauna with a relaxing view", "75 minutes, a clear mind", ...],
      "primary_texts": ["Escape doesn't need a plane ticket...", ...],
      "descriptions": ["Win a trip to the Lofoten!"],
      "headline_source": "flexible_ad"
    }
  ]
}
```

---

## Code Audit Fixes (2026-01-21)

**Completed:** 2026-01-21

Implemented critical stability and security fixes based on comprehensive code audit. Focused on highest-risk issues that could cause crashes or protocol corruption.

### Files Modified

| File | Changes |
|------|---------|
| `meta_ads_mcp/core/callback_server.py` | Fixed event loop crash, replaced prints with logger |
| `meta_ads_mcp/core/server.py` | Redirected all prints to stderr, masked token previews |
| `meta_ads_mcp/core/auth.py` | Redirected prints to stderr |
| `meta_ads_mcp/core/utils.py` | Redirected import-time prints to stderr, replaced function prints with logger |
| `meta_ads_mcp/core/ads.py` | Replaced prints with logger calls |
| `meta_ads_mcp/core/http_auth_integration.py` | Fixed closure capture bug in middleware patching |

### Fix #1: Closure Capture Bug in HTTP Auth Middleware

**Risk Level:** Highest
**Issue:** `setup_fastmcp_http_auth()` loop captured `original_app_provider_method` by reference, causing all patched methods to call the last assigned method.
**Fix:** Added factory function `create_patched_app_provider()` to properly bind loop variables at creation time.

### Fix #2: Event Loop Crash on Python 3.10+

**Risk Level:** Highest
**Issue:** `asyncio.get_event_loop().time()` in callback server thread would raise `RuntimeError: There is no current event loop` on modern Python.
**Fix:** Replaced with `time.time()` from standard library.

### Fix #3: Stdout Prints Corrupting MCP stdio Transport

**Risk Level:** Highest
**Issue:** `print()` calls during import and runtime corrupt the JSON-RPC stream on stdio transport, making the server appear broken.
**Fix:**
- All prints now use `file=sys.stderr` to avoid protocol corruption
- Debug prints converted to `logger.debug()` calls
- Preserved user experience for HTTP transport

### Bonus Fix: Token Leakage in Logs

**Risk Level:** Medium
**Issue:** Token previews like `{token[:10]}...{token[-5:]}` were printed, enabling potential replay attacks.
**Fix:** Replaced all token previews with `***TOKEN***` placeholder.

### Verification

- ✅ 350 unit tests passed
- ✅ Health check API call succeeded
- ✅ Token validation working
- ✅ Campaign data retrieval working

---

## Git History

| Commit | Description |
|--------|-------------|
| `TBD` | Fix critical stability issues: closure bug, event loop crash, stdio corruption |
| `09504cf` | Add get_headline_performance tool for ad copy analysis |
| `65dff3d` | Change only_with_spend default to True for all Meta API query tools |
| `3f19f6b` | Simplify retry module code for clarity (bug fixes + cleanup) |
| `0332605` | Complete Step 1.1: Integrate retry into API client with tests |
| `07377c4` | Add centralized retry/backoff mechanism (Step 1.1) |
| `4f5aa5e` | Add extended Meta API coverage with read-only tools |
| `512b81b` | Add CLAUDE.md to gitignore |
| `abd8599` | Add video completion metrics and scalable architecture plan |
| `9fa377e` | Fix Ad Library API: update deprecated fields and add separate token support |
| `2d3dd0c` | Update progress documentation |
| `c46244e` | Fix multiple bugs found during code review |
| `31aea3c` | Add git history to progress documentation |
| `a92f664` | Complete Meta Ads MCP setup (Steps 5-6) |
| `1f28ac2` | Initial commit: Meta Ads MCP server setup |

---

## Multi-Credential Architecture Implementation (2026-01-22)

### Phase 1: Core Infrastructure ✅

**Completed:** 2026-01-22
**Plan Reference:** `memory-bank/multi-credential-plan-v2.md`

Implemented the core modules for multi-tenant credential management supporting 3 API keys from 3 Business Managers accessing up to 10 ad accounts.

#### Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `meta_ads_mcp/core/credentials.py` | Multi-tenant credential manager with token routing | ~350 |
| `meta_ads_mcp/core/rate_limiter.py` | Per-key rate limiting with decay model | ~230 |
| `meta_ads_mcp/core/errors.py` | Meta API error classification and handling | ~180 |
| `meta_ads_mcp/core/preflight.py` | Startup validation for tokens and accounts | ~300 |

#### Key Components Implemented

**CredentialManager (`credentials.py`):**
- Singleton pattern for global credential state
- Platform-specific credentials.json path resolution (macOS/Windows/Linux)
- Schema v2 validation with api_keys and accounts sections
- Token routing: account_name → api_key → access_token
- Backward compatibility: falls back to .env if no credentials.json
- Token expiration monitoring with 7-day warning threshold
- Account listing and session-based switching

**RateLimiter (`rate_limiter.py`):**
- Per-key rate tracking (not per-account, since accounts share keys)
- Two tiers: development (60/5min) and standard (9000/5min)
- Score-based system with time decay
- Automatic blocking when limits exceeded
- Thread-safe singleton with locking

**Error Classification (`errors.py`):**
- Maps Meta error codes to action types (RETRY, RATE_LIMIT, AUTH_ERROR, etc.)
- MetaApiError exception with is_retryable, action, max_retries properties
- Covers 11 common Meta error codes with appropriate handling
- to_dict() for JSON serialization

**Preflight Validation (`preflight.py`):**
- Async validation of all tokens via /me endpoint
- Permission checking (requires ads_read)
- Account accessibility validation via /act_{id}
- Account status mapping (ACTIVE, DISABLED, etc.)
- Parallel validation for performance
- Formatted output for CLI display

#### Validation Results

- ✅ All 4 modules pass Python syntax check
- ✅ All 4 modules pass IDE diagnostics (no errors)
- ✅ Basic functional tests pass:
  - Error classification correctly identifies auth/rate-limit/server errors
  - RateLimiter correctly tracks calls and blocks at limits
  - CredentialManager singleton pattern works correctly
  - All exception classes inherit properly

---

### Phase 2: Integration ✅

**Completed:** 2026-01-22
**Plan Reference:** `memory-bank/multi-credential-plan-v2.md`

Integrated the credential manager and rate limiter into the existing authentication and API layers.

#### Files Modified

| File | Changes |
|------|---------|
| `meta_ads_mcp/core/auth.py` | Added credential_manager imports, `get_access_token_for_account()`, `get_ad_account_id_for_account()` |
| `meta_ads_mcp/core/api.py` | Updated `meta_api_tool` decorator with rate limiting, account_name support |
| `meta_ads_mcp/core/campaigns.py` | Added `_resolve_account_id()` helper, `account_name` parameter to `get_campaigns()` |
| `meta_ads_mcp/core/__init__.py` | Added import for `account_tools` module |

#### Files Created

| File | Purpose |
|------|---------|
| `meta_ads_mcp/core/account_tools.py` | New MCP tools for multi-tenant management |

#### New MCP Tools Added

| Tool | Description |
|------|-------------|
| `list_configured_accounts()` | List all accounts with metadata and expiration alerts |
| `switch_account(account_name)` | Switch to a different configured account |
| `get_current_account()` | Get details of the current active account |
| `get_rate_limit_status()` | Show rate limit status for all API keys |
| `validate_credentials()` | Run preflight validation on all credentials |
| `get_token_expiration_status()` | Check token expiration status |

#### Key Integration Points

**auth.py additions:**
- `get_access_token_for_account(account_name)` - Token routing with credential_manager fallback
- `get_ad_account_id_for_account(account_name)` - Account ID resolution

**api.py `meta_api_tool` decorator updates:**
- Extracts `account_name` from kwargs
- Checks rate limit before API calls
- Records calls after successful requests
- Handles RateLimitError with retry_after_seconds
- Falls back to legacy auth if credential_manager empty

**campaigns.py updates:**
- `_resolve_account_id(account_id, account_name)` helper function
- `get_campaigns()` now accepts optional `account_name` parameter
- Same pattern can be applied to other tools

#### Validation Results

- ✅ All modified files pass Python syntax check
- ✅ All modified files pass IDE diagnostics (no errors)
- ✅ CredentialManager integration tested
- ✅ RateLimiter integration tested
- ✅ Account resolution logic verified

---

### Phase 3: Server Integration ✅

**Completed:** 2026-01-22
**Plan Reference:** `memory-bank/multi-credential-plan-v2.md`

Integrated credential management into server startup with preflight validation and backward compatibility.

#### Files Modified

| File | Changes |
|------|---------|
| `meta_ads_mcp/core/server.py` | Added `run_startup_checks()` async function, startup_checks() sync wrapper, integrated into main() |

#### Key Features Implemented

**Startup Preflight Checks:**
- `run_startup_checks()` - Async function that validates all credentials at server startup
- `startup_checks()` - Synchronous wrapper for use in main()
- Validates all API keys via /me endpoint
- Verifies account accessibility
- Reports status with formatted output to stderr (safe for stdio transport)
- Handles graceful degradation if checks fail

**Token Expiration Alerting:**
- Checks for tokens expiring within 7 days at startup
- Displays warning message with affected accounts
- Uses stderr for output to preserve MCP protocol

**Backward Compatibility:**
- Falls back to .env mode when no credentials.json present
- Works with legacy META_ACCESS_TOKEN + META_AD_ACCOUNT_ID environment variables
- Creates single "default" account in legacy mode
- All 4 compatibility tests passed:
  - No credentials: 0 accounts
  - Legacy .env mode: 1 account 'default'
  - Token routing in legacy mode: correct token returned
  - Current account in legacy mode: 'default'

#### Validation Results

- ✅ All modified files pass Python syntax check
- ✅ All modified files pass IDE diagnostics (no errors)
- ✅ Backward compatibility tests all pass
- ⚠️ Full pytest cannot run (Python 3.9 venv, MCP requires 3.10+)

#### Test Environment Fix

Upgraded venv from Python 3.9.6 to Python 3.12.12 (via Homebrew) since MCP requires Python 3.10+.

```bash
brew install python@3.12
rm -rf venv
/opt/homebrew/bin/python3.12 -m venv venv
./venv/bin/pip install -e .
```

**Test Results:** 350 passed, 9 skipped, 2 deselected, 9 warnings in 2.49s

---

### Phase 4: Testing ✅

**Completed:** 2026-01-22

Created comprehensive unit tests for all new multi-credential modules.

#### Test Files Created

| File | Tests | Coverage |
|------|-------|----------|
| `tests/test_credentials.py` | 35 | CredentialManager, token routing, account management, expiration monitoring |
| `tests/test_rate_limiter.py` | 26 | Tier configs, blocking, decay, thread safety |
| `tests/test_errors.py` | 30 | Error classification, MetaApiError, action mapping |
| `tests/test_preflight.py` | 23 | Token validation, account validation, result formatting |
| `tests/test_account_tools.py` | 18 | MCP tools for account management |

**Total new tests: 132**

#### Bug Fixed During Testing

**File:** `meta_ads_mcp/core/rate_limiter.py`
**Issue:** `get_all_status()` called `get_key_status()` while holding `self._lock`, causing deadlock with non-reentrant Lock
**Fix:** Changed `threading.Lock()` to `threading.RLock()` for re-entrant locking

#### Final Test Results

```
482 passed, 9 skipped, 2 deselected, 11 warnings in 0.75s
```

(Up from 350 tests before Phase 4)

---

### Phase 5: Documentation ✅

**Completed:** 2026-01-22

Updated README.md with comprehensive multi-account setup documentation and troubleshooting guide.

#### Documentation Added to README.md

**Multi-Account Setup Section:**
- Platform-specific credentials.json file locations (macOS, Windows, Linux)
- Complete JSON schema example with api_keys and accounts sections
- Configuration options tables for API keys and accounts
- New MCP tools table (6 account management tools)
- Backward compatibility note for .env fallback

**Multi-Account Troubleshooting Section:**
- 6 common error scenarios with symptoms, causes, and solutions:
  - No credentials found
  - Invalid token for API key
  - Account not accessible
  - Rate limit exceeded
  - Token expiring soon
  - Account not found

#### Total Documentation Added

~150 lines of new documentation covering:
- Configuration file format and location
- All configuration options
- New tool descriptions
- Error troubleshooting guide

---

## Implementation Complete

All 5 phases of the Multi-Credential Architecture implementation completed:

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Core Infrastructure (credentials, rate limiter, errors, preflight) | ✅ |
| Phase 2 | Integration (auth, api decorator, campaigns, account tools) | ✅ |
| Phase 3 | Server Integration (startup checks, backward compatibility) | ✅ |
| Phase 4 | Testing (132 new tests, bug fixes) | ✅ |
| Phase 5 | Documentation (README updates, troubleshooting guide) | ✅ |

**Final Test Count:** 482 passed (up from 350 before implementation)
