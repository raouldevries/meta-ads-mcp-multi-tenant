# Video Creative Analysis Workflow

## Overview

This workflow analyzes video ad creatives by correlating visual content and subtitles with viewer retention data.

---

## Phase 1: Data Collection

### Step 1.1: Fetch Video Data

```python
analyze_video_creative(
    ad_id="...",
    account_name="...",
    time_range="maximum",
    include_benchmarks=True,
    extract_frames=True,
    extract_subtitles=True
)
```

### Step 1.2: Required Data Points

| Data | Source | Purpose |
|------|--------|---------|
| Video duration | Ad metadata | Baseline for analysis |
| Retention curve | `video_play_curve_actions` | Second-by-second retention |
| Frames | ffmpeg extraction | Visual content analysis |
| Subtitles | OCR on frames | Content analysis |
| Performance metrics | Insights API | CTR, CPM, CPC, spend |

### Step 1.3: Frame Extraction

Extract **minimum 1 frame per second**:

```bash
ffmpeg -i video.mp4 -vf "fps=1" -q:v 2 frame_%03d.jpg
```

### Step 1.4: Subtitle Extraction

Run OCR on bottom 30% of each frame. Collect text with confidence > 40%.

---

## Phase 2: Subtitle Analysis

### Classify Every Subtitle

| Field | Description | Example |
|-------|-------------|---------|
| `timestamp` | When text appears | 2.5s |
| `text` | Exact text content | "Waarom heb je voor My35' gekozen?" |
| `confidence` | OCR confidence | 92% |
| `content_type` | Classification | "hook_question" |
| `is_hook` | In first 3 seconds? | true |
| `is_key_message` | Contains benefit? | false |

### Content Type Classification

| Type | Keywords/Patterns | Example |
|------|-------------------|---------|
| `hook_question` | "?", "waarom", "why", "hoe" | "Why did you choose X?" |
| `hook_statement` | Bold claims in first 3s | "I lost 10kg in 3 months!" |
| `benefit` | "energie", "fit", "resultaat" | "More energy every day" |
| `social_proof` | "perfect", "amazing", numbers | "It was perfect!" |
| `story` | Narrative content | "When I first started..." |
| `cta` | "boek", "gratis", "nu" (in last 30%) | "Book your free trial!" |

### Hook Analysis (First 3 Seconds)

**Critical questions:**
1. What is the FIRST thing said/shown?
2. Is it a question or statement?
3. Does it create curiosity or promise value?
4. Would YOU stop scrolling?

**Red flags:**
- Question format ("Why did you...?") - signals "this is an ad"
- Slow start - person not speaking yet
- No text overlay to grab attention
- Generic opening without specific benefit

---

## Phase 3: Visual Frame Analysis

### For Each Key Frame (every 3 seconds minimum)

**Person Analysis:**

| Field | Options |
|-------|---------|
| `person_visible` | true/false |
| `person_gender` | male/female/unknown |
| `person_age_group` | young (18-30) / middle (30-50) / older (50+) |
| `person_expression` | smiling / talking / neutral / excited |
| `eye_contact` | direct (at camera) / away / none |

**Setting Analysis:**

| Field | Options |
|-------|---------|
| `setting` | indoor / outdoor |
| `location_type` | gym / home / office / nature / studio |
| `lighting` | bright / dim / natural / artificial |

**Scene Analysis:**

| Field | Options |
|-------|---------|
| `scene_type` | talking_head / broll / product / text_overlay |
| `has_text_overlay` | true/false |
| `is_scene_change` | true/false |
| `motion_level` | static / slow / dynamic / fast_cuts |

### Visual Variety Score

| Unique Scenes | Variety Level | Score |
|---------------|---------------|-------|
| 1-2 | Low | 0.3 |
| 3-4 | Medium | 0.6 |
| 5+ | High | 0.9 |

---

## Phase 4: Content-Retention Mapping

Create a table mapping EVERY data point:

```
| Time | Retention | Drop | Subtitle | Frame Description | Status |
|------|-----------|------|----------|-------------------|--------|
| 0.0s | 100% | - | "Waarom heb je..." | Woman on bike | good |
| 1.4s | 85% | -15% | | Same shot | good |
| 2.8s | 52% | -33% | "Ik wilde weer..." | Same shot | warning |
| 4.2s | 37% | -15% | "En de allereerste..." | Continues | warning |
```

### Status Thresholds

| Status | Retention |
|--------|-----------|
| `good` | >= 50% |
| `warning` | 20-50% |
| `critical` | < 20% |

### Critical Drop-Off Points

Any drop >= 20% is critical. For each:
1. Note the timestamp
2. Document what content was showing
3. Document what content came just before
4. Hypothesize why viewers left

---

## Phase 5: Generate Insights

### Required Analysis Points

**1. Hook Analysis**
- Is the hook effective?
- What % drop in first 3 seconds?
- Is it a question (bad) or outcome (good)?

**2. Content Timing**
- Where is the best content?
- What % of viewers see it?
- Should it be moved earlier?

**3. CTA Timing**
- When does CTA appear?
- What % of viewers see it?
- Is it too late?

**4. Visual Engagement**
- Is there enough scene variety?
- Is there eye contact?
- Are there text overlays?

### Strengths (Find At Least 2)

- Strong CTR vs benchmarks?
- Good thruplay rate?
- Retention stabilizes after hook?
- Compelling key message?

### Recommendations Format

```
1. HOOK IMPROVEMENT (High Priority)
   Current: "Waarom heb je voor My35' gekozen?"
   Problem: Question format signals "this is an ad"
   Fix: Lead with the outcome instead
   New hook: "Ik ben gaan skiën in Italië!" + gym B-roll

2. CONTENT REORDER (High Priority)
   Current: Key benefit (skiing) appears at 17s (only 15% see it)
   Fix: Move to first 3-5 seconds
   Structure: Outcome → Brief context → Social proof → CTA
```

---

## Common Patterns & Fixes

### Question Hook with High Early Drop
- **Symptom**: 40%+ drop in first 3 seconds
- **Fix**: Replace question with outcome statement
- **Example**: "Why did you choose X?" → "I achieved [result] with X!"

### Best Content Buried
- **Symptom**: Key benefit appears after 10s, low % sees it
- **Fix**: Front-load the value proposition
- **Example**: Move "skiing in Italy" from 17s to 0-3s

### Static Talking Head
- **Symptom**: Single shot for 20+ seconds
- **Fix**: Add B-roll, text overlays, scene changes

### Late CTA
- **Symptom**: CTA appears when <5% watching
- **Fix**: Show CTA earlier or create shorter version

---

## Quality Checklist

Before finalizing:
- [ ] Every subtitle extracted and classified
- [ ] Key frames analyzed for visual content
- [ ] Content mapped to retention curve
- [ ] Critical drop-offs identified with context
- [ ] Hook specifically analyzed
- [ ] Key message timing documented
- [ ] CTA timing evaluated
- [ ] At least 3 specific recommendations
- [ ] Recommendations include concrete examples
- [ ] Comparison to benchmarks included
