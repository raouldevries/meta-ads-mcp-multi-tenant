# Unified Creative Analysis Agent - Implementation Plan

## Overview

Build a unified MCP agent that analyzes both image and video ad creatives, combining visual analysis with performance metrics to generate actionable insights.

**Key Design Decision**: Single agent with specialized workflows (not two separate agents) because:
- Same entry point: user provides `ad_id`, agent detects type
- 80% shared analysis (people, branding, text, setting)
- Enables cross-format portfolio analysis
- Simpler user experience

---

## Architecture

```
analyze_creative(ad_id)
    │
    ├── _detect_creative_type()
    │       ├── VIDEO → _analyze_video_workflow()
    │       │           ├── download_video()
    │       │           │     ├── SUCCESS → Full analysis
    │       │           │     └── FAIL (Page permissions) → _try_library_match()
    │       │           │                                     ├── Match found → Analyze library video
    │       │           │                                     └── No match → Metadata-only
    │       │           ├── extract_frames() [ffmpeg]
    │       │           ├── detect_subtitles() [tesseract OCR]
    │       │           ├── analyze_frames() [Claude vision]
    │       │           └── fetch_retention_metrics()
    │       │
    │       └── IMAGE → _analyze_image_workflow()
    │                   ├── download_image()
    │                   ├── analyze_visual_elements() [Claude vision]
    │                   └── fetch_performance_metrics()
    │
    └── generate_unified_report()


analyze_library_videos(account_id)  [NEW - Indirect Analysis]
    │
    ├── _fetch_library_videos()
    │       └── GET /{account_id}/advideos?fields=id,title,length,source
    │
    ├── _fetch_video_ads_with_performance()
    │       └── GET /{account_id}/ads?fields=name,creative,insights
    │
    ├── _match_library_to_ads()
    │       ├── _extract_name_patterns()
    │       ├── _match_by_name_keywords()
    │       └── _match_by_duration()
    │
    ├── For each matched video:
    │       ├── download_video() [from library - no Page permissions needed]
    │       ├── extract_frames() [ffmpeg]
    │       ├── detect_subtitles() [tesseract OCR]
    │       └── _aggregate_ad_performance()
    │
    └── generate_combined_report()
```

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `meta_ads_mcp/core/creative_analysis.py` | **CREATE** | Main module with MCP tools |
| `meta_ads_mcp/core/video_processing.py` | **CREATE** | Video download, frame extraction, OCR |
| `meta_ads_mcp/core/library_video_matcher.py` | **CREATE** | Library video to ad matching (Step 8) |
| `meta_ads_mcp/core/server.py` | **MODIFY** | Import new modules for tool registration |
| `pyproject.toml` | **MODIFY** | Add dependencies (pytesseract, opencv-python-headless) |
| `Dockerfile` | **MODIFY** | Add ffmpeg and tesseract-ocr to apt-get install |
| `tests/test_creative_analysis.py` | **CREATE** | Unit and integration tests |
| `tests/test_library_video_matcher.py` | **CREATE** | Tests for library matching (Step 8) |
| `tests/conftest.py` | **MODIFY** | Add mock fixtures |

---

## Implementation Workflow

Follow this process for **each step** in the implementation:

### Phase 1: Implement the Step
Complete all code changes described in the step checklist.

### Phase 2: Audit & Fix Errors
Run the validation suite and fix any issues:

```bash
cd meta-ads-mcp
source .venv/bin/activate

# Type checking (pyright-lsp)
pyright meta_ads_mcp/

# Run unit tests
python -m pytest tests/ -v

# Run specific tests for new modules
python -m pytest tests/test_creative_analysis.py -v
```

Use skills from `memory-bank/skills/` as needed:
- `test-runner` - For running and debugging tests
- `debug-mcp` - For troubleshooting server/auth issues
- `code-simplifier` - For code quality review

### Phase 3: Update Progress
Document completion in `memory-bank/progress.md`:

```markdown
## Step X: [Step Name]
**Status:** Completed
**Date:** YYYY-MM-DD

### Completed
- [x] Task 1
- [x] Task 2

### Notes
- Any issues encountered and how they were resolved
- Decisions made during implementation
```

### Phase 4: Request Approval
Ask user for confirmation before proceeding to the next step:
- Summarize what was implemented
- Show test results
- Highlight any deviations from the plan
- Wait for explicit approval before starting next step

### Plugins Used During Implementation

| Plugin | When to Use |
|--------|-------------|
| `pyright-lsp` | Type checking after each file change - critical for async code |
| `code-review` | Before completing each step - review subprocess patterns |
| `commit-commands` | `/commit` after each step completion |
| `security-guidance` | When handling video URLs/downloads |

### Skills Used During Implementation

| Skill | When to Use |
|-------|-------------|
| `test-runner` | After implementing each module |
| `debug-mcp` | When encountering server/API issues |
| `code-simplifier` | Before finalizing code in each step |

### Additional Validation for This Plan

| Check | When | Why |
|-------|------|-----|
| `ffprobe` validation | Step 3 - before processing videos | Catch corrupt/invalid videos early |
| Subprocess timeout testing | Steps 3.3, 3.4 | Verify async process kill works correctly |
| Fallback path testing | Step 4.1 | Ensure all 3 analysis levels (full/thumbnail/metadata) work |
| Feature flag testing | Step 7.4 | Verify disabled features don't cause errors |

---

## Implementation Steps

### Step 1: Core Infrastructure

#### Step 1.1: Create `creative_analysis.py` skeleton
- [ ] Import dependencies (mcp, api, credentials, utils)
- [ ] Define custom exceptions (`CreativeAnalysisError`, `VideoProcessingError`)
- [ ] Define output schemas as dataclasses/TypedDicts
- [ ] Stub out main tool functions

#### Step 1.2: Implement `_detect_creative_type()`
- [ ] Fetch creative metadata via `/{ad_id}?fields=creative{object_story_spec,asset_feed_spec}`
- [ ] Check for `video_data` in `object_story_spec` → VIDEO
- [ ] Check for `child_attachments` → CAROUSEL
- [ ] Default → IMAGE
- [ ] Return `(creative_type: str, creative_data: dict)`

#### Step 1.3: Implement `_extract_creative_content()`
- [ ] Extract headlines from `asset_feed_spec.titles` or `object_story_spec.link_data.name`
- [ ] Extract body text from `asset_feed_spec.bodies` or `object_story_spec.link_data.message`
- [ ] Extract CTA from `asset_feed_spec.call_to_action_types`
- [ ] Extract link URL from `asset_feed_spec.link_urls` or `object_story_spec.link_data.link`

---

### Step 2: Image Analysis

#### Step 2.1: Implement `_fetch_image_analysis()`
- [ ] Reuse logic from `get_ad_image()` in `ads.py`
- [ ] Use `extract_creative_image_urls()` from `utils.py`
- [ ] Download highest quality image available
- [ ] Return `{image_hash, dimensions, url, thumbnail_url}`

#### Step 2.2: Implement `_fetch_performance_metrics()`
- [ ] Call `/{ad_id}/insights` with fields: `impressions,clicks,ctr,spend,cpc,cpm,reach,frequency`
- [ ] Support `time_range` parameter (preset or custom dict)
- [ ] Parse actions/conversions if available
- [ ] Return unified metrics dict

#### Step 2.3: Implement `_calculate_benchmarks()`
- [ ] Fetch account-level insights for comparison
- [ ] Calculate avg/p25/p50/p75 for CTR, CPC, CPM
- [ ] Optionally filter by creative_type for fair comparison

---

### Step 3: Video Processing Module

#### Step 3.1: Create `video_processing.py`
- [ ] Define `VideoConfig` dataclass (max_frames, interval, scene_threshold)
- [ ] Define `ExtractedFrame` dataclass (path, timestamp, is_scene_change)
- [ ] Define `SubtitleRegion` dataclass (text, confidence, timestamp)

#### Step 3.2: Implement `download_video()`
```python
async def download_video(video_id: str, access_token: str) -> Optional[bytes]:
    # 1. Fetch video source URL from /{account_id}/advideos?fields=source,length
    # 2. Download video using httpx with streaming
    # 3. Return video bytes or None on failure
```

#### Step 3.3: Implement `extract_frames()`
```python
async def extract_frames(video_path: str, config: VideoConfig) -> List[ExtractedFrame]:
    # Use asyncio.create_subprocess_exec for non-blocking execution
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", "select='gt(scene,0.3)+isnan(prev_selected_t)*gte(t-prev_selected_t,2)',showinfo",
        "-vsync", "vfr", "-q:v", "2", f"{output_dir}/frame_%03d.jpg"
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=config.extraction_timeout  # default 60s
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise VideoProcessingError("Frame extraction timed out")
```
- [ ] Use `asyncio.create_subprocess_exec` (not subprocess.run)
- [ ] Add configurable timeout (default 60s) with process kill on timeout
- [ ] Handle `asyncio.CancelledError` to clean up child processes
- [ ] Calculate optimal frame count based on duration
- [ ] Parse ffmpeg showinfo output for timestamps
- [ ] Return list of `ExtractedFrame` objects

#### Step 3.4: Implement `detect_subtitles()`
```python
async def detect_subtitles(frame_path: str, timestamp: float, timeout: float = 10.0) -> List[SubtitleRegion]:
    # 1. Crop bottom 25% of frame (subtitle region) using PIL
    # 2. Preprocess: grayscale, adaptive threshold, denoise

    # 3. Run tesseract asynchronously with timeout
    proc = await asyncio.create_subprocess_exec(
        "tesseract", cropped_path, "stdout", "--psm", "6", "-c", "tessedit_create_tsv=1",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return []  # Graceful degradation: return empty on timeout

    # 4. Parse TSV output, filter by confidence > 60%
    # 5. Return SubtitleRegion objects
```
- [ ] Use `asyncio.create_subprocess_exec` for tesseract
- [ ] Add 10s timeout per frame (OCR should be fast)
- [ ] Gracefully return empty list on timeout (don't fail entire analysis)

#### Step 3.5: Implement `VideoProcessingContext`
- [ ] Context manager for temp file handling
- [ ] Create temp directory on enter
- [ ] Clean up all files on exit
- [ ] Register with atexit for safety

---

### Step 4: Video Analysis Integration

#### Step 4.1: Implement `_analyze_video_workflow()`

**Fallback Hierarchy** (critical for graceful degradation):
```
┌─ Try: Download video source
│   ├─ SUCCESS → Full analysis (frames, OCR, retention)
│   └─ FAIL → Try: Fetch thumbnail
│             ├─ SUCCESS → Thumbnail-only analysis
│             │            Set: "analysis_level": "thumbnail_only"
│             │            Skip: frame extraction, OCR, retention correlation
│             └─ FAIL → Return limited response
│                       Set: "analysis_level": "metadata_only"
│                       Include: ad copy, CTA, performance metrics only
```

- [ ] Implement fallback hierarchy with explicit `analysis_level` in response
- [ ] Check feature flag `META_ADS_VIDEO_ANALYSIS_ENABLED` before attempting download
- [ ] Download video (with fallback to thumbnail)
- [ ] Validate video (ffprobe check) - skip if thumbnail-only
- [ ] Extract frames - skip if thumbnail-only or disabled
- [ ] Run OCR on frames - skip if `META_ADS_OCR_ENABLED=false`
- [ ] Detect scene changes
- [ ] Return comprehensive video analysis dict with `analysis_level` field

#### Step 4.2: Implement `_fetch_video_retention_metrics()`
- [ ] Fetch `video_play_actions`, `video_p25/50/75/95/100_watched_actions`
- [ ] Fetch `video_thruplay_watched_actions`, `video_avg_time_watched_actions`
- [ ] Fetch `video_play_curve_actions` (retention curve)
- [ ] Calculate watch completion rate

#### Step 4.3: Implement `_correlate_content_to_retention()`
- [ ] Map retention curve to video timestamps
- [ ] Find significant drop-off points (>5% decrease)
- [ ] Correlate drop-offs with content (subtitle, scene change)
- [ ] Generate insights about retention patterns

---

### Step 5: Main Tools & Insights

#### Step 5.1: Implement `analyze_creative()` tool
```python
@mcp_server.tool()
@meta_api_tool
async def analyze_creative(
    ad_id: str,
    access_token: Optional[str] = None,
    account_name: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    include_recommendations: bool = True,
    compare_to_benchmark: bool = True
) -> str:
```

#### Step 5.2: Implement `analyze_account_creatives()` tool
```python
@mcp_server.tool()
@meta_api_tool
async def analyze_account_creatives(
    account_id: str,
    access_token: Optional[str] = None,
    account_name: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    limit: int = 20,
    min_spend: float = 1.0,
    creative_type_filter: Optional[str] = None
) -> str:
```

#### Step 5.3: Implement `_generate_ai_insights()`
- [ ] Rule-based initial implementation
- [ ] Identify strengths (above-benchmark metrics)
- [ ] Identify weaknesses (below-benchmark metrics)
- [ ] Generate recommendations based on patterns
- [ ] For video: correlate content with retention

---

### Step 6: Testing

#### Step 6.1: Unit tests (`test_creative_analysis.py`)
- [ ] Test `_detect_creative_type()` with image/video/carousel fixtures
- [ ] Test `download_video()` with mocked API
- [ ] Test `extract_frames()` with mocked ffmpeg subprocess
- [ ] Test `detect_subtitles()` with mocked tesseract
- [ ] Test error handling for each function

#### Step 6.2: Integration tests
- [ ] Test full image workflow with mocked API
- [ ] Test full video workflow with mocked API + ffmpeg + tesseract
- [ ] Test graceful degradation scenarios:
  - [ ] Video download fails → falls back to thumbnail analysis
  - [ ] Thumbnail unavailable → falls back to metadata-only
  - [ ] OCR times out → continues without subtitles
  - [ ] ffmpeg times out → returns partial analysis
  - [ ] Feature flags disabled → skips heavy operations

#### Step 6.3: Add fixtures to `conftest.py`
- [ ] `mock_ffmpeg_success` / `mock_ffmpeg_failure`
- [ ] `mock_tesseract_output` / `mock_tesseract_empty`
- [ ] `mock_creative_with_video` / `mock_creative_with_image`
- [ ] `sample_frame_bytes` / `sample_video_frames`

---

### Step 7: Documentation & Integration

#### Step 7.1: Update `server.py`
- [ ] Add import: `from . import creative_analysis`
- [ ] Verify tools are registered

#### Step 7.2: Update `pyproject.toml` and `Dockerfile`

**pyproject.toml:**
```toml
dependencies = [
    # ... existing ...
    "pytesseract>=0.3.10",
    "opencv-python-headless>=4.8.0",
]
```

**Dockerfile** (critical for production):
```dockerfile
# Update apt-get install line to include ffmpeg and tesseract
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc ffmpeg tesseract-ocr && \
    rm -rf /var/lib/apt/lists/*
```
- [ ] Update `pyproject.toml` with new dependencies
- [ ] Update `Dockerfile` to install ffmpeg and tesseract-ocr
- [ ] Update `requirements.txt` if used separately from pyproject.toml

#### Step 7.3: Document system requirements
- ffmpeg >= 4.0
- tesseract-ocr >= 4.0
- Installation commands for macOS/Linux/Windows

#### Step 7.4: Add Feature Flags

Environment variables for controlling heavy operations:

| Variable | Default | Description |
|----------|---------|-------------|
| `META_ADS_VIDEO_ANALYSIS_ENABLED` | `true` | Enable/disable video download and frame extraction |
| `META_ADS_OCR_ENABLED` | `true` | Enable/disable OCR subtitle detection |
| `META_ADS_MAX_VIDEO_DURATION_SEC` | `300` | Skip videos longer than this (5 min default) |
| `META_ADS_MAX_VIDEO_SIZE_MB` | `100` | Skip videos larger than this |
| `META_ADS_FRAME_EXTRACTION_TIMEOUT` | `60` | Timeout for ffmpeg in seconds |

```python
# In video_processing.py
from os import environ

VIDEO_ANALYSIS_ENABLED = environ.get("META_ADS_VIDEO_ANALYSIS_ENABLED", "true").lower() == "true"
OCR_ENABLED = environ.get("META_ADS_OCR_ENABLED", "true").lower() == "true"
MAX_VIDEO_DURATION = int(environ.get("META_ADS_MAX_VIDEO_DURATION_SEC", "300"))
MAX_VIDEO_SIZE_MB = int(environ.get("META_ADS_MAX_VIDEO_SIZE_MB", "100"))
FRAME_EXTRACTION_TIMEOUT = int(environ.get("META_ADS_FRAME_EXTRACTION_TIMEOUT", "60"))
```

- [ ] Add feature flag parsing in `video_processing.py`
- [ ] Check flags before heavy operations
- [ ] Document flags in README.md

---

### Step 8: Library Video Matching (Indirect Analysis)

**Purpose:** When direct video access requires Page permissions that aren't available, this fallback approach matches ad account library videos to running ads using name and duration patterns, enabling video content analysis combined with ad performance metrics.

**When to Use:**
- Page-owned videos in ads return error #10 (permission denied)
- Token only has `ads_read` permission (no `pages_read_engagement`)
- Ad account has videos in media library (`/advideos` endpoint)

#### Step 8.1: Create `library_video_matcher.py` module

##### Step 8.1.1: Define data structures
- [ ] Create `LibraryVideo` dataclass:
  ```python
  @dataclass
  class LibraryVideo:
      id: str
      title: str
      duration: float  # seconds
      source_url: Optional[str]
      created_time: Optional[str]
      is_cropped_variant: bool  # True if "cropped_" or "Auto_Cropped_" in title
  ```

##### Step 8.1.2: Define matching result structures
- [ ] Create `VideoMatch` dataclass:
  ```python
  @dataclass
  class VideoMatch:
      library_video: LibraryVideo
      matched_ads: List[Dict]  # ads using this video (by pattern match)
      match_confidence: float  # 0.0-1.0 based on name/duration match quality
      match_method: str  # "name_exact", "name_keyword", "duration_only"
      aggregated_performance: Dict  # combined metrics from all matched ads
  ```

##### Step 8.1.3: Define matching configuration
- [ ] Create `MatchingConfig` dataclass:
  ```python
  @dataclass
  class MatchingConfig:
      name_patterns: List[Tuple[str, str]]  # (pattern_name, regex)
      duration_tolerance_seconds: float = 1.0  # match within ±1s
      min_confidence_threshold: float = 0.5
      prefer_original_over_cropped: bool = True
  ```

#### Step 8.2: Implement library video fetching

##### Step 8.2.1: Implement `_fetch_library_videos()`
- [ ] Call `GET /{account_id}/advideos`
- [ ] Request fields: `id,title,length,source,created_time`
- [ ] Handle pagination (limit=50, iterate with cursor)
- [ ] Filter out videos without source URLs
- [ ] Mark cropped variants (`is_cropped_variant` flag)
- [ ] Return `List[LibraryVideo]`

##### Step 8.2.2: Implement `_fetch_video_ads_with_performance()`
- [ ] Call `GET /{account_id}/ads` with:
  ```python
  fields = "id,name,creative{asset_feed_spec,object_story_spec},insights.date_preset({time_range}){impressions,clicks,spend,ctr,cpc,reach,frequency,actions}"
  filtering = '[{"field":"effective_status","operator":"IN","value":["ACTIVE","PAUSED"]}]'
  ```
- [ ] Extract video IDs from `asset_feed_spec.videos`
- [ ] Parse insights data into performance dict
- [ ] Return list of ads with video references and performance

#### Step 8.3: Implement pattern matching logic

##### Step 8.3.1: Implement `_extract_name_patterns()`
- [ ] Define common keyword extraction patterns:
  ```python
  KEYWORD_PATTERNS = [
      ("twijfel", r"twijfel", "doubt/hesitation theme"),
      ("geen_tijd", r"geen.?tijd|probleem.*tijd", "no time objection"),
      ("geen_zin", r"geen.?zin", "no motivation objection"),
      ("review", r"review|testimonial|vrouwelijk|lid", "member testimonial"),
      ("sportschool_past", r"sportschool.*past|bij.*past", "finding right gym"),
      ("wist_je", r"wist.?je", "did you know hook"),
      ("carnaval", r"carnaval", "seasonal/carnival"),
      ("video_N", r"video.?(\d+)", "numbered video reference"),
  ]
  ```
- [ ] Extract keywords from library video titles
- [ ] Extract keywords from ad names
- [ ] Return keyword mappings for both sources

##### Step 8.3.2: Implement `_match_by_name_keywords()`
- [ ] For each library video:
  - [ ] Extract keywords from title using regex patterns
  - [ ] Find ads with matching keywords in name
  - [ ] Calculate match confidence based on:
    - Exact keyword match: 1.0
    - Partial keyword match: 0.7
    - Multiple keywords match: boost by 0.1 per additional match
- [ ] Prefer original videos over cropped variants (same content)
- [ ] Return matches with confidence scores

##### Step 8.3.3: Implement `_match_by_duration()`
- [ ] For unmatched library videos:
  - [ ] Group by duration (within tolerance)
  - [ ] Compare with known ad video durations (if available from thumbnails)
- [ ] Use as secondary signal to boost confidence
- [ ] Return duration-based match suggestions

##### Step 8.3.4: Implement `_resolve_best_matches()`
- [ ] Combine name and duration matches
- [ ] For each ad, select best matching library video:
  - [ ] Highest confidence score wins
  - [ ] Prefer original over cropped variants
  - [ ] Break ties by: exact match > keyword match > duration match
- [ ] Filter out matches below `min_confidence_threshold`
- [ ] Return final `List[VideoMatch]`

#### Step 8.4: Implement performance aggregation

##### Step 8.4.1: Implement `_aggregate_ad_performance()`
- [ ] For each `VideoMatch`:
  - [ ] Sum impressions, clicks, spend across all matched ads
  - [ ] Calculate weighted average CTR: `total_clicks / total_impressions * 100`
  - [ ] Sum reach (note: may have overlap between ads)
  - [ ] Calculate average frequency
  - [ ] Calculate CPC: `total_spend / total_clicks`
- [ ] Handle edge cases (zero impressions, zero clicks)
- [ ] Return aggregated metrics dict

##### Step 8.4.2: Implement `_calculate_match_summary()`
- [ ] Count total library videos
- [ ] Count matched vs unmatched videos
- [ ] Calculate total spend across matched videos
- [ ] Identify top performers by CTR and spend
- [ ] Return summary statistics

#### Step 8.5: Implement MCP tools

##### Step 8.5.1: Implement `match_library_videos_to_ads()` tool
```python
@mcp_server.tool()
@meta_api_tool
async def match_library_videos_to_ads(
    account_id: str,
    access_token: Optional[str] = None,
    account_name: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    min_confidence: float = 0.5,
    include_unmatched: bool = False
) -> str:
    """
    Match ad account library videos to running ads using name/duration patterns.

    Use this when direct video access requires Page permissions.
    Returns library videos with their matched ad performance data.

    Args:
        account_id: Ad account ID (act_XXX)
        time_range: Performance data time range
        min_confidence: Minimum match confidence (0.0-1.0)
        include_unmatched: Include library videos with no ad matches

    Returns:
        JSON with matched videos, performance data, and match confidence
    """
```

##### Step 8.5.2: Implement `analyze_matched_video()` tool
```python
@mcp_server.tool()
@meta_api_tool
async def analyze_matched_video(
    library_video_id: str,
    account_id: str,
    access_token: Optional[str] = None,
    account_name: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    extract_frames: bool = True,
    extract_subtitles: bool = True
) -> str:
    """
    Analyze a library video and combine with matched ad performance.

    Downloads video from library (no Page permissions needed),
    extracts frames and text, then combines with ad performance data.

    Args:
        library_video_id: Video ID from advideos library
        account_id: Ad account ID for performance data
        time_range: Performance data time range
        extract_frames: Enable frame extraction (requires ffmpeg)
        extract_subtitles: Enable OCR text detection (requires tesseract)

    Returns:
        Complete analysis with video content + ad performance
    """
```

##### Step 8.5.3: Implement `analyze_all_matched_videos()` tool
```python
@mcp_server.tool()
@meta_api_tool
async def analyze_all_matched_videos(
    account_id: str,
    access_token: Optional[str] = None,
    account_name: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    limit: int = 10,
    sort_by: str = "spend"  # "spend", "ctr", "impressions"
) -> str:
    """
    Analyze all matched library videos for an account.

    Matches library videos to ads, then analyzes top performers.

    Args:
        account_id: Ad account ID
        time_range: Performance data time range
        limit: Max videos to analyze (sorted by sort_by)
        sort_by: Sort matched videos by this metric before limiting

    Returns:
        Batch analysis with all matched videos and insights
    """
```

#### Step 8.6: Implement fallback integration

##### Step 8.6.1: Update `_analyze_video_workflow()` with library fallback
- [ ] After video download fails with permission error:
  ```python
  try:
      video_bytes = await download_video(video_id, access_token)
  except PermissionError as e:
      if "error code 10" in str(e).lower():
          # Try library match fallback
          match = await _try_library_match(ad_id, account_id, access_token)
          if match:
              return await _analyze_library_video_with_ad_performance(
                  match.library_video,
                  match.aggregated_performance
              )
      raise
  ```
- [ ] Set `analysis_level: "library_match"` in response
- [ ] Include `match_confidence` in response metadata

##### Step 8.6.2: Implement `_try_library_match()`
- [ ] Extract video name/keywords from ad creative
- [ ] Fetch library videos for account
- [ ] Run matching algorithm
- [ ] Return best match or None

##### Step 8.6.3: Implement `_analyze_library_video_with_ad_performance()`
- [ ] Download library video (uses `source` URL, no Page permission needed)
- [ ] Run standard video analysis (frames, OCR)
- [ ] Merge with provided ad performance data
- [ ] Generate insights based on combined data
- [ ] Return unified analysis result

#### Step 8.7: Testing for library matching

##### Step 8.7.1: Unit tests for matching logic
- [ ] Test `_extract_name_patterns()` with various title formats
- [ ] Test `_match_by_name_keywords()` with exact/partial/no matches
- [ ] Test `_match_by_duration()` with tolerance edge cases
- [ ] Test `_resolve_best_matches()` with conflicting matches
- [ ] Test confidence score calculations

##### Step 8.7.2: Integration tests for library matching
- [ ] Test `match_library_videos_to_ads()` with mocked API responses
- [ ] Test fallback path in `_analyze_video_workflow()`
- [ ] Test `analyze_matched_video()` end-to-end with mocked video

##### Step 8.7.3: Add test fixtures
- [ ] `mock_library_videos` - Sample advideos response
- [ ] `mock_video_ads_with_insights` - Ads with performance data
- [ ] `mock_matched_result` - Expected matching output

---

## Output Schema

### Single Creative Analysis
```json
{
  "ad_id": "string",
  "creative_type": "image|video",
  "analysis_level": "full|thumbnail_only|metadata_only|library_match",
  "visual_analysis": {
    "dimensions": {"width": 1080, "height": 1080, "aspect_ratio": "1:1"},
    "thumbnail_url": "string",
    "video_duration_seconds": 30.5,
    "frames_analyzed": 8
  },
  "content": {
    "headlines": ["string"],
    "primary_texts": ["string"],
    "call_to_action": "LEARN_MORE",
    "detected_text": [{"text": "string", "timestamp": 5.0, "confidence": 0.95}]
  },
  "performance_metrics": {
    "time_range": "last_30d",
    "impressions": 30551,
    "clicks": 1611,
    "ctr": 5.27,
    "spend": 233.23,
    "video_metrics": {
      "avg_watch_time_seconds": 5,
      "watch_completion_rate": 0.11,
      "retention_curve": [100, 82, 57, 44, ...],
      "drop_off_points": [{"timestamp": 3.0, "drop_percent": 56}]
    }
  },
  "benchmark_comparison": {
    "ctr_vs_avg": "+15.2%",
    "performance_tier": "top"
  },
  "ai_insights": {
    "strengths": ["Strong CTR above benchmark"],
    "weaknesses": ["56% drop in first 3 seconds"],
    "recommendations": [
      {"type": "hook", "priority": "high", "suggestion": "Lead with outcome, not question"}
    ]
  }
}
```

### Library Video Matching Result (Step 8)
```json
{
  "match_summary": {
    "total_library_videos": 29,
    "matched_videos": 3,
    "unmatched_videos": 26,
    "total_matched_spend": 182.95,
    "analysis_timestamp": "2026-01-23T21:00:00Z"
  },
  "matched_videos": [
    {
      "library_video": {
        "id": "2329104084169972",
        "title": "Video 2 - Twijfel jij nog_ .mov",
        "duration_seconds": 9.449,
        "source_url": "https://...",
        "is_cropped_variant": false,
        "created_time": "2025-12-04T10:49:29+0000"
      },
      "match_info": {
        "confidence": 0.95,
        "method": "name_keyword",
        "matched_keywords": ["twijfel"],
        "matched_ad_count": 2
      },
      "matched_ads": [
        {
          "ad_id": "120237318342120381",
          "ad_name": "RM | Video twijfel",
          "status": "ACTIVE"
        }
      ],
      "aggregated_performance": {
        "time_range": "last_30d",
        "impressions": 6481,
        "clicks": 351,
        "ctr": 5.42,
        "spend": 80.77,
        "cpc": 0.23,
        "reach": 2891,
        "frequency": 2.2
      },
      "content_analysis": {
        "frames_extracted": 5,
        "detected_text": [
          {"timestamp": 0, "text": "Twijfel jij nog?"},
          {"timestamp": 4, "text": "Probeer nu gratis"}
        ],
        "video_metadata": {
          "resolution": "720x1280",
          "fps": 30,
          "codec": "h264"
        }
      },
      "ai_insights": {
        "strengths": ["High CTR (5.42%)", "Strong hook question"],
        "weaknesses": ["Short duration may limit message"],
        "recommendations": [
          {"priority": "medium", "suggestion": "Test longer version with more detail"}
        ]
      }
    }
  ],
  "unmatched_videos": [
    {
      "id": "911299351584186",
      "title": "Auto_Cropped_AR_4_X_5_DCO_Video 8 l Roermond.mov",
      "duration_seconds": 19.266,
      "reason": "No matching ad name patterns found"
    }
  ],
  "performance_ranking": {
    "by_spend": ["twijfel", "review", "geen_tijd"],
    "by_ctr": ["twijfel", "review", "geen_tijd"],
    "top_performer": {
      "pattern": "twijfel",
      "library_video_id": "2329104084169972",
      "spend": 80.77,
      "ctr": 5.42
    }
  }
}
```

### Analyzed Matched Video Result (Step 8)
```json
{
  "analysis_type": "library_match",
  "library_video_id": "2622203244807897",
  "video_details": {
    "title": "Video 3 - Review lid.mov",
    "duration_seconds": 23.2,
    "resolution": "720x1280",
    "format": "h264",
    "file_size_kb": 3234.7,
    "created_time": "2025-12-04T10:49:29+0000"
  },
  "content_analysis": {
    "frames_extracted": 12,
    "frame_interval_seconds": 2,
    "detected_text_by_timestamp": {
      "0-4": ["Fitness Fun inBalans", "persoonlijke begeleiding"],
      "6-10": ["Milon", "je hebt meer"],
      "12-20": ["iREACT", "Milon equipment"],
      "22": ["Boek gratis Proefles"]
    },
    "content_structure": {
      "opening": "Brand intro with tagline",
      "middle": "Member testimonial with equipment shots",
      "closing": "Call to action - free trial"
    }
  },
  "matched_ad_performance": {
    "matched_ads": ["RM | Video vrouwelijk lid", "RM | Video vrouwelijk lid"],
    "match_confidence": 0.85,
    "time_range": "last_30d",
    "impressions": 3599,
    "reach": 1492,
    "clicks": 179,
    "ctr": 4.97,
    "spend": 55.56,
    "cpc": 0.31,
    "frequency": 2.4
  },
  "ai_insights": {
    "strengths": [
      "Strong CTR (4.97%) above 3% benchmark",
      "Efficient CPC (€0.31)",
      "Vertical format optimized for mobile",
      "Clear CTA at end",
      "Testimonial format builds trust"
    ],
    "weaknesses": [
      "Duration (23s) on longer side",
      "CTA appears only at end (22s mark)"
    ],
    "recommendations": [
      {"priority": "high", "suggestion": "Test 15s version with faster pacing"},
      {"priority": "medium", "suggestion": "Add subtitles for sound-off viewing"},
      {"priority": "medium", "suggestion": "Move CTA earlier (10-15s mark)"},
      {"priority": "low", "suggestion": "A/B test different opening hooks"}
    ]
  }
}
```

---

## Verification Plan

### Manual Testing
1. Run `analyze_creative()` on known image ad → verify structure
2. Run `analyze_creative()` on known video ad → verify video metrics
3. Run `analyze_account_creatives()` → verify batch analysis
4. Test with invalid ad_id → verify error handling
5. Run `match_library_videos_to_ads()` → verify matching works (Step 8)
6. Run `analyze_matched_video()` → verify combined analysis (Step 8)
7. Test library fallback when Page permission denied → verify graceful fallback (Step 8)

### Automated Testing
```bash
# Run unit tests (excludes e2e)
python -m pytest tests/test_creative_analysis.py -v

# Run library matching tests (Step 8)
python -m pytest tests/test_library_video_matcher.py -v

# Run with coverage
python -m pytest tests/test_creative_analysis.py tests/test_library_video_matcher.py -v --cov=meta_ads_mcp.core

# Run e2e tests (requires running server)
python -m pytest tests/test_creative_analysis.py -v -m e2e
```

### Integration Verification
1. Start MCP server: `python -m meta_ads_mcp`
2. Use Claude Code to call `analyze_creative(ad_id="120237318342120381")`
3. Verify response includes visual analysis, metrics, and insights
4. Test HTML dashboard generation with analysis output
5. Test `match_library_videos_to_ads(account_id="act_238370534780205")` (Step 8)
6. Verify library matching returns correct video-to-ad associations (Step 8)
7. Test `analyze_matched_video(library_video_id="2622203244807897")` (Step 8)

---

## Dependencies

### Python Packages (add to pyproject.toml)
- `pytesseract>=0.3.10` - Tesseract OCR wrapper
- `opencv-python-headless>=4.8.0` - Image preprocessing (headless for server)

### System Requirements
- **ffmpeg** >= 4.0 - Video processing
- **tesseract-ocr** >= 4.0 - OCR engine

### Installation
```bash
# macOS
brew install ffmpeg tesseract

# Ubuntu/Debian
sudo apt-get install ffmpeg tesseract-ocr

# Verify
ffmpeg -version
tesseract --version
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| ffmpeg/tesseract not installed | Graceful fallback with clear error message |
| Video download timeout | 60s timeout, retry with exponential backoff |
| OCR produces garbage | Confidence threshold (60%), language detection |
| Large videos (>5min) | Max duration limit, frame count caps |
| API rate limits | Existing rate limiter handles this |
| Temp file cleanup | Context manager + atexit handler |
| **Page permission denied (error #10)** | Fall back to library video matching (Step 8) |
| **No library videos match ads** | Return metadata-only analysis, suggest manual matching |
| **False positive matches** | Confidence threshold (0.5), prefer exact matches over partial |
| **Multiple videos match same ad** | Prefer original over cropped, highest confidence wins |
| **Library videos not in library** | Handle empty advideos gracefully, return clear message |
| **Name patterns don't match** | Extensible pattern config, duration fallback matching |

---

## Success Criteria

- [ ] `analyze_creative()` works for both image and video ads
- [ ] Video analysis includes subtitle extraction and retention correlation
- [ ] Image analysis includes visual element detection
- [ ] Both include performance metrics and benchmarks
- [ ] AI insights generated for all creatives
- [ ] Unit test coverage > 80%
- [ ] E2E tests pass against running server
- [ ] Documentation complete with system requirements
- [ ] **Library video matching works when Page permissions unavailable (Step 8)**
- [ ] **`match_library_videos_to_ads()` returns accurate matches with confidence scores (Step 8)**
- [ ] **`analyze_matched_video()` combines video content with ad performance (Step 8)**
- [ ] **Fallback from direct video access to library matching is seamless (Step 8)**
- [ ] **Matching handles cropped/original variants correctly (Step 8)**

---

## Future Enhancements (Post-MVP)

### Brand Knowledge Base Integration

Add a per-account/brand knowledge base that provides context for more relevant creative analysis and recommendations.

**Knowledge Base Schema:**
```json
{
  "brand_id": "my35_echt",
  "brand_name": "My35 Fitness",
  "target_audience": {
    "demographics": {
      "age_range": "25-45",
      "gender": "mixed",
      "income_level": "middle-class"
    },
    "psychographics": {
      "interests": ["fitness", "health", "weight loss", "lifestyle"],
      "pain_points": ["lack of time", "motivation", "gym intimidation"],
      "goals": ["lose weight", "build strength", "feel confident"]
    }
  },
  "business_model": {
    "type": "subscription_gym",
    "pricing_tier": "budget-friendly",
    "unique_selling_points": ["24/7 access", "no contract", "personal training included"],
    "conversion_goal": "trial_signup"
  },
  "tone_of_voice": {
    "style": "motivational, friendly, inclusive",
    "language": "casual, encouraging",
    "avoid": ["aggressive sales tactics", "body shaming", "unrealistic promises"]
  },
  "visual_style": {
    "colors": ["orange", "black", "white"],
    "imagery": ["real members", "diverse body types", "gym interior", "before/after"],
    "avoid": ["stock photos", "overly muscular models only", "cluttered layouts"]
  },
  "competitors": ["Basic-Fit", "Fit For Free", "Anytime Fitness"],
  "seasonal_focus": {
    "jan-mar": "new year resolutions",
    "apr-jun": "summer body prep",
    "sep-oct": "back to routine"
  }
}
```

**How It Enhances Analysis:**

| Current (Without KB) | Enhanced (With KB) |
|---------------------|-------------------|
| "Image shows gym interior" | "Image aligns with brand guideline: show real gym environment" |
| "CTR is 5.2%" | "CTR is 5.2% - strong for budget-friendly gym segment (benchmark: 3.8%)" |
| "Video has 56% drop at 3s" | "56% drop at 3s - hook doesn't address target pain point 'gym intimidation'" |
| "Recommend: add CTA" | "Recommend: add 'Start Free Trial' CTA aligned with conversion goal" |

**Implementation Approach:**
1. Create `meta_ads_mcp/core/brand_knowledge.py` module
2. Store knowledge base as JSON files in config directory (per account)
3. Add `get_brand_context()` helper that loads KB for current account
4. Enhance `_generate_ai_insights()` to use brand context for recommendations
5. Add MCP tool: `update_brand_knowledge()` for managing KB

**Storage Location:**
```
~/.config/meta-ads-mcp/
├── credentials.json
└── brand_knowledge/
    ├── my35_echt.json
    ├── my35_roermond.json
    └── my35_blerick.json
```

This is planned for a future iteration after the core creative analysis is stable.
