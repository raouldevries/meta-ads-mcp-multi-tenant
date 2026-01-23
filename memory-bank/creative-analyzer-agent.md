# Creative Analyzer Agent Instructions

## Purpose

This document provides detailed instructions for analyzing Meta Ads video and image creatives. Follow these steps to produce comprehensive, actionable insights that correlate creative content with performance data.

---

## When to Use This Agent

Use the creative analyzer when:
- User asks to analyze an ad creative (video or image)
- User wants to understand why an ad is performing well or poorly
- User asks about video retention, hook effectiveness, or creative improvements
- User wants to compare creative performance to benchmarks

---

## Video Creative Analysis Workflow

### Phase 1: Data Collection

#### Step 1.1: Fetch Ad Metadata
```python
# Use analyze_video_creative with extract_frames=True, extract_subtitles=True
analyze_video_creative(
    ad_id="...",
    account_name="...",
    time_range="maximum",  # or specific range
    include_benchmarks=True,
    extract_frames=True,
    extract_subtitles=True
)
```

#### Step 1.2: Fetch Retention Curve
Get the full `video_play_curve_actions` from insights API - this gives second-by-second retention percentages.

#### Step 1.3: Extract Video Frames
Extract at minimum **1 frame per second** for thorough analysis. For a 30-second video, you need ~30 frames.

```bash
ffmpeg -i video.mp4 -vf "fps=1" -q:v 2 frame_%03d.jpg
```

#### Step 1.4: Extract Subtitles
Run OCR on each frame's bottom 30% region. Collect ALL text with confidence > 40%.

---

### Phase 2: Subtitle Analysis (What Is Being Said)

For EVERY subtitle detected, document:

| Field | Description | Example |
|-------|-------------|---------|
| `timestamp` | When text appears | 2.5s |
| `text` | Exact text content | "Waarom heb je voor My35' gekozen?" |
| `confidence` | OCR confidence | 92% |
| `content_type` | Classification (see below) | "hook_question" |
| `is_hook` | Appears in first 3 seconds? | true |
| `is_key_message` | Contains benefit/outcome? | false |

#### Content Type Classification

| Type | Keywords/Patterns | Example |
|------|-------------------|---------|
| `hook_question` | "?", "waarom", "why", "hoe", "how" | "Why did you choose X?" |
| `hook_statement` | Bold claims in first 3s | "I lost 10kg in 3 months!" |
| `benefit` | "energie", "fit", "sterk", "resultaat" | "More energy every day" |
| `social_proof` | "perfect", "geweldig", "amazing", numbers | "It was perfect!" |
| `story` | Narrative, testimonial content | "When I first started..." |
| `cta` | "boek", "gratis", "nu", "probeer" (in last 30%) | "Book your free trial!" |

#### Hook Analysis (First 3 Seconds)

The hook is CRITICAL. Answer these questions:
1. What is the FIRST thing said/shown?
2. Is it a question or statement?
3. Does it create curiosity or promise value?
4. Would YOU stop scrolling for this?

**Red flags:**
- Question format ("Why did you...?") - signals "this is an ad"
- Slow start - person not speaking yet
- No text overlay to grab attention
- Generic opening without specific benefit

---

### Phase 3: Frame Visual Analysis (What Is In The Frame)

For EACH key frame (at minimum every 3 seconds), analyze:

#### Person Analysis
| Field | Options | Notes |
|-------|---------|-------|
| `person_visible` | true/false | Is someone in frame? |
| `person_gender` | male/female/unknown | Primary subject |
| `person_age_group` | young (18-30) / middle (30-50) / older (50+) | Estimate |
| `person_expression` | smiling / talking / neutral / excited | Current state |
| `eye_contact` | direct (at camera) / away / none | Direct = more engaging |

#### Setting Analysis
| Field | Options | Notes |
|-------|---------|-------|
| `setting` | indoor / outdoor | Primary environment |
| `location_type` | gym / home / office / nature / studio / store | Specific location |
| `lighting` | bright / dim / natural / artificial | Lighting quality |

#### Scene Analysis
| Field | Options | Notes |
|-------|---------|-------|
| `scene_type` | talking_head / broll / product / text_overlay / testimonial | Primary content |
| `has_text_overlay` | true/false | On-screen text/graphics? |
| `text_overlay_content` | string | What does it say? |
| `is_scene_change` | true/false | New scene from previous? |
| `motion_level` | static / slow / dynamic / fast_cuts | Camera/subject movement |

#### Visual Variety Score
Count unique scene types and settings. More variety = higher engagement.
- 1-2 unique scenes = Low variety (0.3)
- 3-4 unique scenes = Medium variety (0.6)
- 5+ unique scenes = High variety (0.9)

---

### Phase 4: Content-Retention Mapping

Create a table mapping EVERY data point to content:

```
| Time | Retention | Drop | Subtitle | Frame Description | Status |
|------|-----------|------|----------|-------------------|--------|
| 0.0s | 100% | - | "Waarom heb je..." | Woman on bike, talking | good |
| 1.4s | 85% | -15% | | Same shot, listening | good |
| 2.8s | 52% | -33% | "Ik wilde weer..." | Same shot | warning |
| 4.2s | 37% | -15% | "En de allereerste..." | Testimonial continues | warning |
| ... | ... | ... | ... | ... | ... |
```

#### Status Thresholds
- `good`: Retention >= 50%
- `warning`: Retention 20-50%
- `critical`: Retention < 20%

#### Identify Critical Drop-Off Points
Any drop >= 20% is critical. For each:
1. Note the timestamp
2. Document what content was showing
3. Document what content came just before
4. Hypothesize why viewers left

---

### Phase 5: Generate Insights

#### Key Issues (Must Include)

1. **Hook Analysis**
   - Is the hook effective?
   - What % drop in first 3 seconds?
   - Is it a question (bad) or outcome (good)?

2. **Content Timing**
   - Where is the best content (key benefit/outcome)?
   - What % of viewers see it?
   - Should it be moved earlier?

3. **CTA Timing**
   - When does CTA appear?
   - What % of viewers see it?
   - Is it too late?

4. **Visual Engagement**
   - Is there enough scene variety?
   - Is there eye contact?
   - Are there text overlays to reinforce message?

#### Strengths (Find At Least 2)
- Strong CTR vs benchmarks?
- Good thruplay rate?
- Retention stabilizes after hook?
- Compelling key message?

#### Recommendations (Be Specific)

For each issue, provide:
1. **Type**: What category (hook, pacing, cta_timing, visual_variety)
2. **Priority**: high/medium/low
3. **Suggestion**: Specific, actionable change
4. **Example**: Concrete example of the fix

Example recommendations:
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

3. CTA TIMING (Medium Priority)
   Current: CTA at 28s when 0% watching
   Fix: Show CTA at 15-20s when 10%+ still engaged
   Alternative: Create 15-second cut
```

---

## Image Creative Analysis Workflow

### Phase 1: Data Collection

```python
analyze_image_creative(
    ad_id="...",
    account_name="...",
    time_range="last_30d",
    include_benchmarks=True
)
```

### Phase 2: Visual Analysis

#### Composition
| Element | Analysis |
|---------|----------|
| Primary focus | What draws the eye first? |
| Text hierarchy | Headline → Subhead → Body → CTA |
| Color scheme | Brand colors? Contrast? |
| Image quality | Sharp? Professional? |

#### Person (if present)
- Gender, age, expression
- Eye contact (direct = higher engagement)
- Relatability to target audience

#### Text Content
- Headline: Clear benefit?
- Body: Supporting details?
- CTA: Action-oriented?

### Phase 3: Performance Correlation

Compare to benchmarks:
- CTR vs account average
- CPC vs account average
- CPM vs account average

### Phase 4: Insights

- What's working (above benchmark)?
- What's not working (below benchmark)?
- Specific improvements to test

---

## Output Format

Always structure your analysis as:

```markdown
## Creative Analysis: [Ad Name]

### Summary
- Ad ID: ...
- Type: Video/Image
- Duration: ... (for video)
- Spend: €...
- Key Finding: [One-sentence summary]

### Performance Metrics
[Table of metrics vs benchmarks]

### Content Analysis
[For video: Content-retention mapping table]
[For image: Visual analysis breakdown]

### Key Issues
1. [Issue with severity, content, and impact]
2. ...

### Strengths
1. [What's working]
2. ...

### Recommendations
1. [Specific, actionable recommendation with example]
2. ...

### Suggested Next Creative
[Brief description of what the next test should be]
```

---

## Common Patterns & Fixes

### Pattern: Question Hook with High Early Drop
**Symptom**: 40%+ drop in first 3 seconds, hook is a question
**Fix**: Replace question with outcome statement
**Example**: "Why did you choose X?" → "I achieved [result] with X!"

### Pattern: Best Content Buried
**Symptom**: Key benefit appears after 10s, low % sees it
**Fix**: Front-load the value proposition
**Example**: Move "I went skiing in Italy" from 17s to 0-3s

### Pattern: Static Talking Head
**Symptom**: Single shot for 20+ seconds, continuous drop
**Fix**: Add B-roll, text overlays, scene changes
**Example**: Cut away to gym equipment, add text reinforcing key points

### Pattern: Late CTA
**Symptom**: CTA appears when <5% watching
**Fix**: Show CTA earlier or create shorter version
**Example**: Add CTA overlay at 15s, create 15s cut

### Pattern: No Text Overlays
**Symptom**: Relies entirely on audio/speech
**Fix**: Add bold text overlays for key points
**Example**: "Lost 10kg" text when that's mentioned verbally

---

## Quality Checklist

Before finalizing analysis, verify:

- [ ] Every subtitle extracted and classified
- [ ] Key frames analyzed for visual content
- [ ] Content mapped to retention curve
- [ ] Critical drop-offs identified with content context
- [ ] Hook specifically analyzed
- [ ] Key message timing documented
- [ ] CTA timing evaluated
- [ ] At least 3 specific recommendations provided
- [ ] Recommendations include concrete examples
- [ ] Comparison to benchmarks included
