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

**Required data points:**
- Image dimensions and aspect ratio
- Full-resolution image URL
- Ad copy (headline, primary text, description)
- CTA button type
- Performance metrics (impressions, clicks, CTR, spend, CPC, CPM)
- Account benchmarks for comparison

---

### Phase 2: Visual Composition Analysis

Analyze the image using these frameworks. Every visual element matters.

#### 2.1 Focal Point & Visual Hierarchy

| Element | What to Analyze | Why It Matters |
|---------|-----------------|----------------|
| **Primary focal point** | What does the eye see FIRST? | Must be the key message or product |
| **Secondary elements** | What does the eye see NEXT? | Should support, not distract |
| **Visual flow** | How does the eye move through the image? | Should lead to CTA |
| **Clutter level** | How many competing elements? | More than 3 = too cluttered |

**Document the visual hierarchy:**
```
1st: [Element] - e.g., "Person's face"
2nd: [Element] - e.g., "Product in hand"
3rd: [Element] - e.g., "Headline text"
4th: [Element] - e.g., "CTA button"
```

#### 2.2 Composition Techniques

| Technique | Present? | Analysis |
|-----------|----------|----------|
| **Rule of Thirds** | yes/no | Is the subject placed at intersection points? |
| **Center Composition** | yes/no | Is the subject centered? (works for products, symmetry) |
| **Leading Lines** | yes/no | Do lines guide eye toward focal point? |
| **Framing** | yes/no | Is subject framed by other elements? |
| **Symmetry** | yes/no | Is composition balanced? |
| **Negative Space** | yes/no | Is there breathing room around subject? |

**Composition Score:**
- Strong composition (3+ techniques used effectively): 0.8-1.0
- Moderate composition (1-2 techniques): 0.5-0.7
- Weak composition (cluttered, no clear technique): 0.0-0.4

#### 2.3 Color Psychology Analysis

**Dominant Colors (list top 3):**

| Color | Psychological Association | Appropriate for Ad? |
|-------|---------------------------|---------------------|
| **Red** | Urgency, energy, passion, appetite | Sales, food, fitness |
| **Orange** | Enthusiasm, creativity, affordability | CTAs, youth brands |
| **Yellow** | Optimism, warmth, attention-grabbing | Highlights, warnings |
| **Green** | Health, nature, money, growth | Wellness, finance, eco |
| **Blue** | Trust, calm, professionalism, security | Tech, finance, healthcare |
| **Purple** | Luxury, creativity, wisdom | Premium, beauty, spiritual |
| **Pink** | Feminine, playful, romantic | Beauty, fashion, lifestyle |
| **Black** | Sophistication, luxury, power | Premium, fashion, tech |
| **White** | Clean, pure, minimal, modern | Tech, healthcare, minimal brands |

**Color Analysis Checklist:**
- [ ] Do colors match brand identity?
- [ ] Is there sufficient contrast for readability?
- [ ] Does the color scheme evoke the right emotion for the product?
- [ ] Are colors consistent with the target audience expectations?

#### 2.4 Contrast & Readability

| Element | Score (1-10) | Notes |
|---------|--------------|-------|
| **Text-background contrast** | | Can text be read at a glance? |
| **Subject-background separation** | | Does subject pop from background? |
| **CTA visibility** | | Does CTA stand out? |
| **Thumbnail readability** | | Is it clear at 100x100px? |

**Contrast Formula:**
- High contrast (score 8-10): Text/subject clearly visible at any size
- Medium contrast (score 5-7): Readable but requires attention
- Low contrast (score 1-4): Difficult to read, gets lost

#### 2.5 Image Quality Assessment

| Quality Factor | Assessment | Impact |
|----------------|------------|--------|
| **Resolution** | Sharp / Slightly soft / Blurry | Blurry = unprofessional |
| **Lighting** | Professional / Natural / Poor | Affects perceived quality |
| **Color accuracy** | True to life / Oversaturated / Washed out | Affects trust |
| **Noise/grain** | Clean / Slight noise / Grainy | Grainy = amateur |
| **Cropping** | Intentional / Awkward / Cut off elements | Bad crops = careless |

---

### Phase 3: Subject & Element Analysis

#### 3.1 Person Analysis (If Present)

**This is CRITICAL - faces are the highest-engagement element in ads.**

| Attribute | Value | Impact on Performance |
|-----------|-------|----------------------|
| **Face visible?** | yes/no | Faces increase engagement 38% |
| **Eye contact** | direct / away / at product | Direct = highest engagement |
| **Expression** | smiling / neutral / serious / excited | Smiling = +10-15% CTR |
| **Authenticity** | real person / stock photo / AI-generated | Real > Stock > AI |
| **Demographic match** | matches target / mismatch | Must match audience |
| **Number of people** | 1 / 2 / group | 1-2 people typically best |

**Face Positioning:**
| Position | Best For |
|----------|----------|
| Center | Direct response, testimonials |
| Rule of thirds | Lifestyle, aspirational |
| Looking at product | Product focus ads |
| Looking at CTA | Directional cue to click |

**Eye Gaze Direction:**
- **At camera**: Creates connection, best for trust/testimonials
- **At product**: Directs attention to product
- **At text/CTA**: Subtle directional cue
- **Away/distant**: Aspirational, lifestyle

#### 3.2 Product Analysis (If Present)

| Attribute | Assessment | Notes |
|-----------|------------|-------|
| **Product visibility** | prominent / visible / subtle / hidden | Should match ad objective |
| **Product context** | in use / isolated / lifestyle / packaging | In-use typically converts better |
| **Product angle** | front / 3/4 / side / top-down | 3/4 angle often most appealing |
| **Scale reference** | clear / unclear / none | Helps understand product size |
| **Multiple products** | single / few / many | Single focus typically best |

#### 3.3 Text Overlay Analysis

**Text-to-Image Ratio:**
- Facebook recommends: <20% text coverage
- Optimal: 5-15% for feed ads
- Too much text: Algorithm may reduce reach

| Text Element | Present? | Placement | Readable at Thumbnail? |
|--------------|----------|-----------|------------------------|
| **Headline** | yes/no | top/center/bottom | yes/no |
| **Subheadline** | yes/no | | yes/no |
| **Body text** | yes/no | | yes/no |
| **Price/offer** | yes/no | | yes/no |
| **CTA text** | yes/no | | yes/no |

**Text Placement Best Practices:**
- **Top placement**: First thing seen, good for hooks
- **Center placement**: Maximum visibility, can obscure subject
- **Bottom placement**: Read last, good for CTA
- **Left-aligned**: Natural reading pattern (Western audiences)
- **Text on solid bar**: Better readability than overlay on image

#### 3.4 Whitespace & Breathing Room

| Area | Whitespace Level | Assessment |
|------|------------------|------------|
| **Around subject** | cramped / adequate / spacious | |
| **Around text** | cramped / adequate / spacious | |
| **Overall density** | cluttered / balanced / minimal | |
| **Safe zones** | respected / violated | Platform UI overlap? |

**Whitespace Guidelines:**
- Minimum 10% padding from edges
- Text needs surrounding space to be readable
- Premium brands use MORE whitespace
- Discount/sale ads can be denser

---

### Phase 4: Platform-Specific Analysis

#### 4.1 Placement Dimensions

| Placement | Aspect Ratio | Dimensions | Safe Zone |
|-----------|--------------|------------|-----------|
| **Feed (Square)** | 1:1 | 1080×1080 | Full image visible |
| **Feed (Portrait)** | 4:5 | 1080×1350 | Preferred for feed |
| **Feed (Landscape)** | 1.91:1 | 1200×628 | Less prominent in feed |
| **Stories/Reels** | 9:16 | 1080×1920 | Top/bottom 14% for UI |
| **Right Column** | 1.91:1 | 1200×628 | Very small display |
| **Marketplace** | 1:1 | 1080×1080 | Product focus critical |

**Current Image Assessment:**
- Actual dimensions: [width] × [height]
- Aspect ratio: [ratio]
- Optimized for: [placements]
- May crop poorly on: [placements]

#### 4.2 Safe Zone Analysis

```
Stories/Reels Safe Zone Map:
┌────────────────────┐
│ ▓▓▓ TOP 14% ▓▓▓▓▓▓ │ ← Profile pic, username overlay
│                    │
│                    │
│    SAFE ZONE       │ ← Key content here
│    (72% of height) │
│                    │
│                    │
│ ▓▓▓ BOTTOM 14% ▓▓▓ │ ← CTA button, reactions overlay
└────────────────────┘
```

**Check:**
- [ ] Key message in safe zone?
- [ ] Face/product not cut off?
- [ ] CTA not hidden by platform UI?

#### 4.3 Thumbnail Preview Test

How does the image look at small sizes?

| Size | Key Elements Visible? | Text Readable? |
|------|----------------------|----------------|
| 200×200 | | |
| 100×100 | | |
| 50×50 | | |

**Thumbnail Optimization:**
- Primary subject must be recognizable at 100×100
- Text should be readable at 200×200 minimum
- High contrast critical for small sizes

---

### Phase 5: Performance Correlation

#### 5.1 Metrics vs Benchmarks

| Metric | Ad Value | Account Avg | Difference | Status |
|--------|----------|-------------|------------|--------|
| **CTR** | % | % | +/-% | above/below |
| **CPC** | € | € | +/-€ | above/below |
| **CPM** | € | € | +/-€ | above/below |
| **Relevance Score** | /10 | /10 | +/- | above/below |
| **Frequency** | | | | |

#### 5.2 Visual Element → Performance Correlation

Based on the visual analysis, identify likely performance drivers:

| Visual Element | Likely Impact | Evidence |
|----------------|---------------|----------|
| Face with eye contact | +CTR | Proven engagement driver |
| High contrast CTA | +CTR | Easy to see = more clicks |
| Cluttered composition | -CTR | Confusing = scroll past |
| Stock photo feel | -CTR | Low authenticity = low trust |
| Text too small | -CTR | Can't read = can't engage |

---

### Phase 6: A/B Testing Recommendations

Based on the analysis, recommend specific variants to test.

#### 6.1 Single Variable Testing Framework

**CRITICAL: Test ONE variable at a time.**

| Priority | Variable to Test | Current | Variant A | Variant B |
|----------|------------------|---------|-----------|-----------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

#### 6.2 Common Image A/B Tests

**Person Variants:**
| Test | When to Try |
|------|-------------|
| With person vs without | If current has no person |
| Direct eye contact vs looking at product | If person present |
| Smiling vs neutral expression | If person not smiling |
| Single person vs multiple | If showing group |
| Real person vs illustrated | If using stock |

**Composition Variants:**
| Test | When to Try |
|------|-------------|
| Close-up vs full scene | If current is wide shot |
| Product in use vs isolated | If showing product alone |
| Lifestyle context vs studio | If studio shot |
| Minimal vs detailed background | If busy background |

**Text Variants:**
| Test | When to Try |
|------|-------------|
| With text overlay vs clean image | Always worth testing |
| Headline at top vs bottom | If headline present |
| Benefit-focused vs feature-focused | Always |
| With price vs without price | If price not shown |
| Urgency text vs standard | For promotions |

**Color Variants:**
| Test | When to Try |
|------|-------------|
| Warm CTA vs cool CTA | If CTA not converting |
| High contrast vs subtle | If low CTR |
| Brand colors vs contrasting | If using brand colors |
| Light background vs dark | If dark currently |

#### 6.3 Testing Priority Matrix

| Impact Potential | Easy to Test | Priority |
|------------------|--------------|----------|
| High | Yes | 🔴 Test First |
| High | No | 🟡 Plan Carefully |
| Low | Yes | 🟢 Quick Win |
| Low | No | ⚪ Skip |

---

### Phase 7: Generate Insights

#### 7.1 Strengths (Find At Least 2)

Look for:
- Above-benchmark metrics
- Strong visual hierarchy
- Effective color psychology
- Clear focal point
- High-quality image
- Authentic feel
- Platform-optimized dimensions

#### 7.2 Weaknesses (Be Specific)

Look for:
- Below-benchmark metrics
- Cluttered composition
- Poor contrast/readability
- Stock photo feel
- Missing key elements (face, product, CTA)
- Wrong dimensions for placement
- Text too small for thumbnail

#### 7.3 Recommendations (Specific & Actionable)

For each recommendation, provide:

```
RECOMMENDATION: [Title]
Priority: High/Medium/Low
Current State: [What exists now]
Problem: [Why it's hurting performance]
Solution: [Specific change to make]
Expected Impact: [What improvement to expect]
A/B Test: [How to validate]
```

---

## Image Analysis Patterns & Fixes

### Pattern: Stock Photo Feel
**Symptom**: Below-average CTR, low engagement
**Visual Signs**: Perfect lighting, generic poses, watermark-like quality
**Fix**: Use authentic imagery - real customers, behind-the-scenes, UGC
**Test**: Same copy with stock vs authentic image

### Pattern: No Clear Focal Point
**Symptom**: Low CTR, quick scroll-past
**Visual Signs**: Multiple competing elements, no visual hierarchy
**Fix**: Simplify composition, use blur/darkening to de-emphasize background
**Test**: Simplified version with single focal point

### Pattern: Text Illegible at Thumbnail
**Symptom**: Low CTR despite strong offer
**Visual Signs**: Small text, low contrast, busy background behind text
**Fix**: Increase text size, add solid background bar, improve contrast
**Test**: Same message with improved text treatment

### Pattern: Missing Human Element
**Symptom**: Lower engagement than competitors
**Visual Signs**: Product-only images, no people
**Fix**: Add person using/holding/reacting to product
**Test**: Product alone vs product with person

### Pattern: Wrong Aspect Ratio
**Symptom**: Poor performance on specific placements
**Visual Signs**: Key elements cropped in feed, wasted space in Stories
**Fix**: Create placement-specific versions
**Test**: Native aspect ratio vs forced ratio

### Pattern: Weak CTA Visibility
**Symptom**: High impressions, low clicks
**Visual Signs**: CTA button blends with image, small, or poorly placed
**Fix**: Contrasting CTA color, larger size, better placement
**Test**: Subtle vs prominent CTA treatment

### Pattern: Cluttered Design
**Symptom**: Below-average metrics across the board
**Visual Signs**: >5 elements competing, no whitespace, overwhelming
**Fix**: Remove 50% of elements, increase whitespace, single message
**Test**: Current vs simplified version

### Pattern: Low Contrast
**Symptom**: Low engagement, people don't notice the ad
**Visual Signs**: Subject blends with background, muted colors, flat
**Fix**: Increase saturation, add vignette, darken/lighten background
**Test**: Original vs high-contrast version

---

## Image Analysis Quality Checklist

Before finalizing analysis, verify:

**Data Collection:**
- [ ] Full-resolution image reviewed
- [ ] All ad copy documented
- [ ] Performance metrics collected
- [ ] Benchmark data available

**Composition Analysis:**
- [ ] Primary focal point identified
- [ ] Visual hierarchy documented (1st, 2nd, 3rd...)
- [ ] Composition technique(s) identified
- [ ] Whitespace/density assessed

**Color Analysis:**
- [ ] Dominant colors listed
- [ ] Color psychology relevance assessed
- [ ] Contrast levels rated
- [ ] Brand consistency checked

**Subject Analysis:**
- [ ] Person analysis complete (if applicable)
- [ ] Product analysis complete (if applicable)
- [ ] Text overlay analysis complete
- [ ] All elements catalogued

**Platform Check:**
- [ ] Aspect ratio documented
- [ ] Safe zones checked
- [ ] Thumbnail readability tested
- [ ] Placement optimization assessed

**Performance Correlation:**
- [ ] All metrics vs benchmarks compared
- [ ] Visual elements linked to performance
- [ ] Likely drivers identified
- [ ] Likely detractors identified

**Recommendations:**
- [ ] At least 3 specific recommendations
- [ ] Each recommendation has clear rationale
- [ ] A/B test suggestions included
- [ ] Priority order assigned
- [ ] Expected impact stated

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
