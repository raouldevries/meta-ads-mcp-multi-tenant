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

## Creative Analysis Agent ✅

**Plan Reference:** `memory-bank/creative-analysis-plan.md`
**Status:** Complete

### Steps Overview

| Step | Description | Status |
|------|-------------|--------|
| Step 1 | Core Infrastructure | ✅ |
| Step 2 | Image Analysis | ✅ |
| Step 3 | Video Processing Module | ✅ |
| Step 4 | Video Analysis Integration | ✅ |
| Step 5 | Main Tools & Insights | ✅ |
| Step 6 | Testing | ✅ |
| Step 7 | Documentation & Integration | ✅ |

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

### Step 6: Testing ✅

**Completed:** 2026-01-23

Created comprehensive test suites for creative analysis and video processing.

#### Test Files Created

| File | Tests | Coverage |
|------|-------|----------|
| `tests/test_creative_analysis.py` | 55 | Exceptions, enums, dataclasses, helpers, E2E |
| `tests/test_video_processing.py` | 27 | Config, dataclasses, context manager, FFmpeg parsing |

#### Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| Exceptions | 5 | Error classes, inheritance, serialization |
| Enums | 3 | CreativeType, AnalysisLevel values |
| Dataclasses | 3 | CreativeDimensions, Content, Metrics |
| Type Detection | 9 | Video, image, carousel detection |
| Content Extraction | 11 | Headlines, body, CTA, URLs |
| Metrics Parsing | 4 | Performance metrics parsing |
| Benchmark Comparison | 5 | CTR/CPC comparison, tiers |
| Dropoff Analysis | 5 | Identify dropoffs, significance |
| AI Insights | 6 | Strength/weakness generation |
| Video Config | 3 | Configuration dataclass |
| Video Dataclasses | 5 | Frame, subtitle, metadata |
| Dependency Checks | 4 | FFmpeg, tesseract availability |
| Context Manager | 8 | Temp directory management |
| FFmpeg Parsing | 5 | showinfo output parsing |
| E2E Tests | 4 | Real API integration |

#### Test Results

- **Unit Tests:** 78 passed
- **E2E Tests:** 4 passed
- **Total:** 82 passed in 7.0s

---

### Step 7: Documentation & Integration ✅

**Completed:** 2026-01-23

Updated README.md with creative analysis documentation and system requirements.

#### Documentation Added

| Section | Description |
|---------|-------------|
| Features | Added "Creative Analysis" bullet point |
| Table of Contents | Added links to new sections |
| Video Analysis System Requirements | Installation instructions for ffmpeg/tesseract |
| Creative Analysis Tools | Documentation for 8 new MCP tools (#30-37) |

#### Integration Verified

| Check | Status |
|-------|--------|
| `creative_analysis` imported in `__init__.py` | ✅ Line 36 |
| `creative_analysis` imported in `server.py` (HTTP) | ✅ Line 461 |
| No Python dependencies needed | ✅ Uses subprocess for ffmpeg/tesseract |
| All 78 unit tests pass | ✅ |

---

## Creative Analysis Implementation Summary

**Files Created:**
- `meta_ads_mcp/core/creative_analysis.py` (~1700 lines)
- `meta_ads_mcp/core/video_processing.py` (~550 lines)
- `tests/test_creative_analysis.py` (~600 lines, 55 tests)
- `tests/test_video_processing.py` (~300 lines, 27 tests)

**MCP Tools Added (8 total):**
1. `get_creative_type` - Detect image/video/carousel
2. `get_creative_content` - Extract headlines, body, CTA
3. `analyze_image_creative` - Image analysis with benchmarks
4. `analyze_video_creative` - Video retention analysis
5. `analyze_creative` - Unified entry point
6. `analyze_account_creatives` - Batch analysis
7. `get_creative_insights` - AI-generated insights
8. `get_account_benchmarks` - Account benchmarks

---

## Step 8: Library Video Matching ✅

**Plan Reference:** `memory-bank/creative-analysis-plan.md` (Step 8)
**Status:** Complete
**Completed:** 2026-01-23

### Overview

Added indirect video analysis capability that matches ad account library videos to running ads using name and duration patterns. This enables video content analysis combined with ad performance metrics even when direct video access requires Page permissions that aren't available.

### Use Cases

- Page-owned videos in ads return error #10 (permission denied)
- Token only has `ads_read` permission (no `pages_read_engagement`)
- Ad account has videos in media library (`/advideos` endpoint)

### File Created

| File | Purpose |
|------|---------|
| `meta_ads_mcp/core/library_video_matcher.py` | Library video matching module (~850 lines) |
| `tests/test_library_video_matcher.py` | Unit tests (45 tests) |

### Data Structures Implemented

| Component | Description |
|-----------|-------------|
| `MatchMethod` | Enum: NAME_EXACT, NAME_KEYWORD, DURATION_ONLY, COMBINED |
| `LibraryVideo` | Dataclass for videos from /advideos endpoint |
| `VideoAdInfo` | Dataclass for video ads with performance |
| `VideoMatch` | Matching result with confidence score |
| `MatchingConfig` | Configuration for matching algorithm |
| `MatchSummary` | Summary statistics for matching operation |

### Functions Implemented

| Function | Purpose |
|----------|---------|
| `fetch_library_videos()` | Fetch videos from /advideos endpoint with pagination |
| `fetch_video_ads_with_performance()` | Fetch video ads with nested insights |
| `extract_keywords()` | Extract pattern keywords from text |
| `match_by_name_keywords()` | Match videos to ads by shared keywords |
| `aggregate_ad_performance()` | Aggregate metrics across matched ads |
| `calculate_match_summary()` | Calculate summary statistics |

### MCP Tools Added (3 total)

| Tool | Description |
|------|-------------|
| `match_library_videos_to_ads` | Match library videos to running ads by name patterns |
| `analyze_matched_video` | Full analysis of matched video with performance |
| `analyze_all_matched_videos` | Batch analysis of all matched videos |

### Default Keyword Patterns

| Pattern | Regex | Description |
|---------|-------|-------------|
| `twijfel` | `r"twijfel"` | Doubt/hesitation theme |
| `geen_tijd` | `r"geen.?tijd\|probleem.*tijd"` | No time objection |
| `geen_zin` | `r"geen.?zin"` | No motivation objection |
| `review` | `r"review\|testimonial\|vrouwelijk\|lid"` | Member testimonial |
| `sportschool_past` | `r"sportschool.*past\|bij.*past"` | Finding right gym |
| `wist_je` | `r"wist.?je"` | Did you know hook |
| `carnaval` | `r"carnaval"` | Seasonal/carnival |
| `video_num` | `r"video.?\s*(\d+)"` | Numbered video reference |

### Test Results

| File | Tests | Status |
|------|-------|--------|
| `tests/test_library_video_matcher.py` | 45 | ✅ All passed |

### Integration Verified

| Check | Status |
|-------|--------|
| `library_video_matcher` imported in `__init__.py` | ✅ Line 37 |
| All import dependencies resolved | ✅ |
| All 45 unit tests pass | ✅ |

---

## Step 8.6: Fallback Integration ✅

**Status:** Complete
**Completed:** 2026-01-23

### Overview

Integrated library video matching as an automatic fallback in `analyze_video_creative()`. When direct video access fails with permission error (error #10), the system automatically tries to match a library video and uses it for analysis.

### Functions Added to creative_analysis.py

| Function | Purpose |
|----------|---------|
| `_try_library_match()` | Find matching library video by keyword patterns |
| `_analyze_with_library_fallback()` | Download and analyze library video |
| `_is_permission_error()` | Detect permission errors (code 10) |

### How It Works

1. `analyze_video_creative()` attempts to process video via `process_video()`
2. If permission error detected, calls `_try_library_match()` with ad name
3. Extracts keywords from ad name (twijfel, review, geen_tijd, etc.)
4. Matches against library video titles
5. If match found with confidence >= 0.5, downloads library video
6. Runs frame extraction and OCR on library video
7. Returns analysis with `analysis_level: "library_match"`

### Response Fields Added

```json
{
  "video_analysis": {
    "source": "library_fallback",
    "library_video_id": "123456789",
    "library_video_title": "Video 3 - Review lid.mov",
    "match_confidence": 0.85,
    "matched_keywords": ["review"]
  }
}
```

### Files Modified

| File | Changes |
|------|---------|
| `meta_ads_mcp/core/creative_analysis.py` | Added 3 helper functions, fallback logic |
| `meta_ads_mcp/core/video_processing.py` | Added `download_video_from_url()` |

### Tests

- 123 tests pass (creative_analysis + video_processing + library_video_matcher)
- Pyright: 0 errors in library_video_matcher.py

---

## Step 9: Video Analysis Methodology & Agent Instructions ✅

**Status:** Complete
**Completed:** 2026-01-23

### Overview

Added comprehensive video analysis methodology to enable detailed content-to-retention correlation analysis. The methodology documents how to extract subtitles, analyze frame visuals, and generate actionable insights.

### Methodology Documentation

Added to `creative_analysis.py` (lines 73-209):

1. **Subtitle Extraction** - Extract EVERY subtitle, classify as hook/benefit/social_proof/cta
2. **Frame Visual Analysis** - Person (gender, age, expression, eye contact), setting, scene type
3. **Performance Correlation** - Map content to retention curve, identify critical dropoffs
4. **Insights Generation** - Key issues, strengths, specific recommendations

### Data Structures Added

| Component | Description |
|-----------|-------------|
| `FrameVisualAnalysis` | Dataclass for frame analysis (person, setting, scene, motion) |
| `SubtitleSegment` | Dataclass for classified subtitles (content_type, is_hook, is_key_message) |
| `ContentRetentionMapping` | Maps content to retention % at each timestamp |
| `VideoCreativeAnalysis` | Complete video analysis result with all components |
| `VIDEO_ANALYSIS_CONFIG` | Configuration dict (hook_window, dropoff_threshold, etc.) |

### Helper Functions Added

| Function | Purpose |
|----------|---------|
| `_classify_subtitle_content()` | Classify text as hook/benefit/cta/question/social_proof |
| `_extract_subtitles_detailed()` | Process subtitles with classification |
| `_create_content_retention_mapping()` | Map content to retention curve |
| `_identify_critical_dropoff_content()` | Find what content causes viewer dropoffs |
| `_get_dropoff_recommendation()` | Generate specific fix recommendations |
| `_generate_video_insights_detailed()` | Create comprehensive insights |
| `_estimate_retention_at_time()` | Estimate retention at any timestamp |

### Agent Instructions Created

| File | Purpose |
|------|---------|
| `memory-bank/creative-analyzer-agent.md` | Comprehensive agent instructions (~300 lines) |
| `CLAUDE.md` update | Quick reference section for creative analysis |

### Agent Instructions Content

The `creative-analyzer-agent.md` covers:
- When to use the creative analyzer
- Video analysis workflow (5 phases)
- Subtitle extraction with content classification
- Frame visual analysis (person, setting, scene)
- Content-retention mapping
- Image analysis workflow
- Output format template
- Common patterns & fixes
- Quality checklist

### Tests

- All 51 creative_analysis tests pass
- Import verification successful

---

## Git Commits (Multi-Tenant)

| Commit | Description |
|--------|-------------|
| `27a0959` | Add library video matching with fallback integration (Step 8) |
| `e43abe7` | Add multi-tenant credentials documentation to CLAUDE.md |
| `9237627` | Consolidate error handling: merge errors.py into retry.py |
| `87a1c03` | Add multi-credential architecture for multi-tenant ad account management |
| `83869ff` | Fix critical stability issues from code audit |
