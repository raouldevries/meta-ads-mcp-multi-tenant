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
```

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `meta_ads_mcp/core/creative_analysis.py` | **CREATE** | Main module with MCP tools |
| `meta_ads_mcp/core/video_processing.py` | **CREATE** | Video download, frame extraction, OCR |
| `meta_ads_mcp/core/server.py` | **MODIFY** | Import new modules for tool registration |
| `pyproject.toml` | **MODIFY** | Add dependencies (pytesseract, opencv-python-headless) |
| `Dockerfile` | **MODIFY** | Add ffmpeg and tesseract-ocr to apt-get install |
| `tests/test_creative_analysis.py` | **CREATE** | Unit and integration tests |
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

## Output Schema

### Single Creative Analysis
```json
{
  "ad_id": "string",
  "creative_type": "image|video",
  "analysis_level": "full|thumbnail_only|metadata_only",
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

---

## Verification Plan

### Manual Testing
1. Run `analyze_creative()` on known image ad → verify structure
2. Run `analyze_creative()` on known video ad → verify video metrics
3. Run `analyze_account_creatives()` → verify batch analysis
4. Test with invalid ad_id → verify error handling

### Automated Testing
```bash
# Run unit tests (excludes e2e)
python -m pytest tests/test_creative_analysis.py -v

# Run with coverage
python -m pytest tests/test_creative_analysis.py -v --cov=meta_ads_mcp.core.creative_analysis

# Run e2e tests (requires running server)
python -m pytest tests/test_creative_analysis.py -v -m e2e
```

### Integration Verification
1. Start MCP server: `python -m meta_ads_mcp`
2. Use Claude Code to call `analyze_creative(ad_id="120237318342120381")`
3. Verify response includes visual analysis, metrics, and insights
4. Test HTML dashboard generation with analysis output

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
