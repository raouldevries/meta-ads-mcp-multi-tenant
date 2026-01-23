# Meta Ads MCP Server - Multi-Tenant Progress

**Project:** Meta Ads MCP (Multi-Tenant Fork)
**Repository:** `/Users/raouldevries/Work/Apps/meta-ads-mcp-multi-tenant/meta-ads-mcp`
**Base:** Forked from `pipeboard-co/meta-ads-mcp`

---

## Environment

| Item | Value |
|------|-------|
| OS | macOS (Darwin) |
| Python | 3.12.12 (Homebrew) |
| Virtual Env | `.venv` |
| MCP Client | Claude Code (stdio mode) |

---

## Multi-Credential Architecture (2026-01-22)

**Plan Reference:** `memory-bank/multi-credential-plan-v2.md`

### Phase 1: Core Infrastructure ✅

**Completed:** 2026-01-22

Implemented core modules for multi-tenant credential management supporting 3 API keys from 3 Business Managers accessing up to 10 ad accounts.

#### Files Created

| File | Purpose |
|------|---------|
| `meta_ads_mcp/core/credentials.py` | Multi-tenant credential manager with token routing |
| `meta_ads_mcp/core/rate_limiter.py` | Per-key rate limiting with decay model |
| `meta_ads_mcp/core/errors.py` | Meta API error classification and handling |
| `meta_ads_mcp/core/preflight.py` | Startup validation for tokens and accounts |

#### Key Components

- **CredentialManager:** Singleton pattern, platform-specific paths, schema v2 validation, backward compatibility
- **RateLimiter:** Per-key tracking, two tiers (dev/standard), score-based with decay
- **Error Classification:** Maps Meta error codes to actions (RETRY, RATE_LIMIT, AUTH_ERROR)
- **Preflight Validation:** Async token validation, permission checking, account accessibility

---

### Phase 2: Integration ✅

**Completed:** 2026-01-22

Integrated credential manager and rate limiter into authentication and API layers.

#### Files Modified

| File | Changes |
|------|---------|
| `meta_ads_mcp/core/auth.py` | Added `get_access_token_for_account()`, `get_ad_account_id_for_account()` |
| `meta_ads_mcp/core/api.py` | Updated `meta_api_tool` decorator with rate limiting, account_name support |
| `meta_ads_mcp/core/campaigns.py` | Added `_resolve_account_id()`, `account_name` parameter |

#### Files Created

| File | Purpose |
|------|---------|
| `meta_ads_mcp/core/account_tools.py` | MCP tools for multi-tenant management |

#### New MCP Tools

| Tool | Description |
|------|-------------|
| `list_configured_accounts()` | List all accounts with metadata |
| `switch_account(account_name)` | Switch to different account |
| `get_current_account()` | Get current active account |
| `get_rate_limit_status()` | Show rate limit status |
| `validate_credentials()` | Run preflight validation |
| `get_token_expiration_status()` | Check token expiration |

---

### Phase 3: Server Integration ✅

**Completed:** 2026-01-22

Integrated credential management into server startup with preflight validation.

#### Key Features

- `run_startup_checks()` - Async validation at startup
- Token expiration alerting (7-day warning)
- Backward compatibility with `.env` mode
- Safe stderr output for stdio transport

---

### Phase 4: Testing ✅

**Completed:** 2026-01-22

#### Test Files Created

| File | Tests |
|------|-------|
| `tests/test_credentials.py` | 35 |
| `tests/test_rate_limiter.py` | 26 |
| `tests/test_errors.py` | 30 |
| `tests/test_preflight.py` | 23 |
| `tests/test_account_tools.py` | 18 |

**Total new tests:** 132

#### Bug Fixed

- `rate_limiter.py`: Changed `threading.Lock()` to `threading.RLock()` to fix deadlock in `get_all_status()`

---

### Phase 5: Documentation ✅

**Completed:** 2026-01-22

- Added multi-account setup section to README.md
- Platform-specific credentials.json locations
- Complete JSON schema with examples
- Troubleshooting guide for 6 common errors

---

## Multi-Credential Implementation Complete ✅

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Core Infrastructure | ✅ |
| Phase 2 | Integration | ✅ |
| Phase 3 | Server Integration | ✅ |
| Phase 4 | Testing (132 new tests) | ✅ |
| Phase 5 | Documentation | ✅ |

**Final Test Count:** 482 passed

---

## Creative Analysis Agent (In Progress)

**Plan Reference:** `memory-bank/creative-analysis-plan.md`
**Status:** In Progress

### Steps Overview

| Step | Description | Status |
|------|-------------|--------|
| Step 1 | Core Infrastructure | ✅ |
| Step 2 | Image Analysis | ✅ |
| Step 3 | Video Processing Module | ✅ |
| Step 4 | Video Analysis Integration | ✅ |
| Step 5 | Main Tools & Insights | ✅ |
| Step 6 | Testing | ⏳ Pending |
| Step 7 | Documentation & Integration | ⏳ Pending |

---

### Step 1: Core Infrastructure ✅

**Completed:** 2026-01-23

Created the main `creative_analysis.py` module with foundational components.

#### File Created

| File | Purpose |
|------|---------|
| `meta_ads_mcp/core/creative_analysis.py` | Main creative analysis module (~475 lines) |

#### Components Implemented

| Component | Description |
|-----------|-------------|
| `CreativeAnalysisError` | Base exception with details dict |
| `VideoProcessingError` | Exception for ffmpeg/download errors |
| `CreativeNotFoundError` | Exception when creative not accessible |
| `CreativeType` | Enum: IMAGE, VIDEO, CAROUSEL, UNKNOWN |
| `AnalysisLevel` | Enum: FULL, THUMBNAIL_ONLY, METADATA_ONLY |
| `CreativeDimensions` | Dataclass for width/height/aspect_ratio |
| `CreativeContent` | Dataclass for headlines/texts/CTA/link |
| `VisualAnalysis` | Dataclass for visual analysis results |
| `PerformanceMetrics` | Dataclass for ad performance metrics |
| `CreativeAnalysisResult` | Complete analysis output schema |

#### Helper Functions

| Function | Purpose |
|----------|---------|
| `_detect_creative_type()` | Detect image/video/carousel from metadata |
| `_extract_creative_content()` | Extract headlines, body, CTA, link URL |
| `_fetch_creative_metadata()` | Fetch creative data from Meta API |
| `_fetch_performance_metrics()` | Fetch ad insights with time range |

#### MCP Tools

| Tool | Description |
|------|-------------|
| `get_creative_type(ad_id)` | Detect creative type with basic metadata |
| `get_creative_content(ad_id)` | Extract all text content from creative |

#### Tested With Real API

- Video ad: Correctly detected as VIDEO, extracted 9 headlines, 8 body texts
- Image ad: Correctly detected as IMAGE, extracted content from asset_feed_spec

---

### Step 2: Image Analysis ✅

**Completed:** 2026-01-23

Added image analysis functionality with performance metrics and account benchmarks.

#### Helper Functions Added

| Function | Purpose |
|----------|---------|
| `_parse_performance_metrics()` | Convert raw API metrics to PerformanceMetrics dataclass |
| `_fetch_image_analysis()` | Extract image URLs, dimensions, and hash from creative |
| `_calculate_benchmarks()` | Fetch account-level avg/percentile metrics |
| `_compare_to_benchmarks()` | Compare creative metrics to account benchmarks |

#### MCP Tools Added

| Tool | Description |
|------|-------------|
| `analyze_image_creative(ad_id)` | Full image analysis with metrics and benchmarks |
| `get_account_benchmarks(account_id)` | Get CTR/CPC/CPM benchmarks for account |

#### Features

- **Image Analysis:** Extracts dimensions (width/height/aspect_ratio), image hash, URLs
- **Performance Metrics:** Impressions, clicks, CTR, spend, CPC, CPM, reach, frequency
- **Benchmark Comparison:** Compare to account avg, determine performance tier (top/middle/bottom)
- **Analysis Levels:** FULL (with dimensions), THUMBNAIL_ONLY, METADATA_ONLY

#### Tested With Real API

- Image ad (1080x1080, 1:1): Retrieved dimensions, hash, 2 image URLs
- Performance metrics: 5,326 impressions, 2.23% CTR
- Analysis level: FULL

---

### Step 3: Video Processing Module ✅

**Completed:** 2026-01-23

Created standalone video processing module with ffmpeg/tesseract integration.

#### File Created

| File | Purpose |
|------|---------|
| `meta_ads_mcp/core/video_processing.py` | Video download, frame extraction, OCR (~550 lines) |

#### Components Implemented

| Component | Description |
|-----------|-------------|
| `VideoConfig` | Configuration dataclass (max_frames, intervals, thresholds) |
| `ExtractedFrame` | Frame metadata (path, timestamp, scene_change) |
| `SubtitleRegion` | OCR result (text, confidence, timestamp) |
| `VideoMetadata` | Video info (duration, dimensions, fps, codec) |
| `VideoProcessingResult` | Combined processing output |
| `VideoProcessingContext` | Async context manager for temp file cleanup |

#### Functions Implemented

| Function | Purpose |
|----------|---------|
| `check_ffmpeg_available()` | Verify ffmpeg installation |
| `check_tesseract_available()` | Verify tesseract installation |
| `download_video()` | Download video from Meta API |
| `get_video_metadata_ffprobe()` | Get detailed metadata with ffprobe |
| `extract_frames()` | Hybrid scene + interval extraction |
| `detect_subtitles()` | Tesseract OCR on frames |
| `detect_subtitles_batch()` | Parallel OCR on multiple frames |
| `process_video()` | High-level orchestration function |

#### System Requirements

- FFmpeg 8.0.1 (available)
- Tesseract 5.5.2 (available)

---

### Step 4: Video Analysis Integration ✅

**Completed:** 2026-01-23

Integrated video processing into creative analysis with retention metrics.

#### Functions Added to creative_analysis.py

| Function | Purpose |
|----------|---------|
| `_fetch_video_retention_metrics()` | Fetch play curve, thruplay, completion |
| `_identify_dropoff_points()` | Find significant viewer dropoffs |

#### MCP Tools Added

| Tool | Description |
|------|-------------|
| `analyze_video_creative(ad_id)` | Full video analysis with retention metrics |

#### Features

- **Video Retention:** play_curve, p25/50/75/95/100 watched, thruplay
- **Dropoff Analysis:** Identifies significant viewer dropoffs (>10% threshold)
- **Early Dropoff Detection:** Flags videos losing >30% by 25% mark
- **Optional Frame Extraction:** extract_frames=True enables ffmpeg processing
- **Optional OCR:** extract_subtitles=True enables tesseract processing

#### Tested With Real API

- Video ad: 26,628 plays, 11.2% thruplay rate
- Retention: 25%=40%, 50%=20%, 75%=14%
- Dropoffs: 2 significant (60% drop at 25%, 20% drop at 50%)
- Early dropoff: True (>30% loss by 25% mark)

---

### Step 5: Main Tools & Insights ✅

**Completed:** 2026-01-23

Added unified analysis entry point, batch analysis, and AI insights generation.

#### MCP Tools Added

| Tool | Description |
|------|-------------|
| `analyze_creative(ad_id)` | Unified entry point - auto-detects type and routes |
| `analyze_account_creatives(account_id)` | Batch analysis with top/bottom performers |
| `get_creative_insights(ad_id)` | AI-generated strengths, weaknesses, recommendations |

#### Features

- **Unified Analysis:** Single tool detects image/video and routes appropriately
- **Batch Analysis:** Analyze multiple creatives, identify top/bottom performers
- **Summary Statistics:** Total spend, impressions, clicks, CTR breakdown by type
- **AI Insights:** Rule-based analysis with actionable recommendations

#### Insights Engine

| Category | Analysis |
|----------|----------|
| CTR Performance | Compare to account average, flag above/below |
| CPC Efficiency | Lower is better, flag expensive clicks |
| Video Thruplay | Flag low (<5%) or high (>15%) rates |
| Early Dropoff | Flag >30% viewer loss by 25% mark |
| Mid-Video Retention | Flag good (>30% at 50%) retention |

#### Tested With Real API

- Video ad CTR: +13.6% above account average (strength)
- Early dropoff detected: Significant viewer loss in first 25% (weakness)
- Recommendation: "Lead with outcome/benefit, not a question" (high priority)

---

## Git Commits (Multi-Tenant)

| Commit | Description |
|--------|-------------|
| `e43abe7` | Add multi-tenant credentials documentation to CLAUDE.md |
| `9237627` | Consolidate error handling: merge errors.py into retry.py |
| `87a1c03` | Add multi-credential architecture for multi-tenant ad account management |
| `83869ff` | Fix critical stability issues from code audit |
