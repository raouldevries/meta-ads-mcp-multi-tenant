# Image Creative Analysis Workflow

## Overview

This workflow analyzes image ad creatives through visual composition, color psychology, subject analysis, and platform optimization.

---

## Phase 1: Data Collection

### Step 1.1: Fetch Image Data

```python
get_ad_image(
    ad_id="...",
    account_name="...",
    download=True
)
```

### Step 1.2: Required Data Points

| Data | Source | Purpose |
|------|--------|---------|
| Image URL | Ad creative | Visual analysis |
| Dimensions | Image metadata | Platform optimization |
| Ad copy | Ad metadata | Headline, text, CTA |
| Performance | Insights API | CTR, CPM, CPC, spend |
| Benchmarks | Account insights | Comparison baseline |

---

## Phase 2: Visual Composition Analysis

### 2.1 Visual Hierarchy

Document what the eye sees in order:

```
1st: [Element] - e.g., "Person's face"
2nd: [Element] - e.g., "Product in hand"
3rd: [Element] - e.g., "Headline text"
4th: [Element] - e.g., "CTA button"
```

| Element | What to Analyze |
|---------|-----------------|
| Primary focal point | What does eye see FIRST? |
| Secondary elements | What does eye see NEXT? |
| Visual flow | How does eye move through image? |
| Clutter level | How many competing elements? (>3 = too cluttered) |

### 2.2 Composition Techniques

| Technique | Check |
|-----------|-------|
| Rule of Thirds | Is subject at intersection points? |
| Center Composition | Is subject centered? (works for products) |
| Leading Lines | Do lines guide eye to focal point? |
| Framing | Is subject framed by other elements? |
| Symmetry | Is composition balanced? |
| Negative Space | Is there breathing room? |

**Composition Score:**
- Strong (3+ techniques): 0.8-1.0
- Moderate (1-2 techniques): 0.5-0.7
- Weak (cluttered, no clear technique): 0.0-0.4

### 2.3 Color Psychology

| Color | Association | Best For |
|-------|-------------|----------|
| Red | Urgency, energy, passion | Sales, food, fitness |
| Orange | Enthusiasm, affordability | CTAs, youth brands |
| Yellow | Optimism, attention | Highlights, warnings |
| Green | Health, nature, growth | Wellness, finance, eco |
| Blue | Trust, calm, professionalism | Tech, finance, healthcare |
| Purple | Luxury, creativity | Premium, beauty |
| Pink | Feminine, playful | Beauty, fashion, lifestyle |
| Black | Sophistication, luxury | Premium, fashion, tech |
| White | Clean, minimal, modern | Tech, healthcare |

**Color Checklist:**
- [ ] Colors match brand identity?
- [ ] Sufficient contrast for readability?
- [ ] Colors evoke right emotion?
- [ ] Consistent with target audience?

### 2.4 Contrast & Readability

| Element | Score (1-10) |
|---------|--------------|
| Text-background contrast | |
| Subject-background separation | |
| CTA visibility | |
| Thumbnail readability (100x100px) | |

---

## Phase 3: Subject Analysis

### 3.1 Person Analysis (CRITICAL)

Faces are the highest-engagement element (+38% engagement).

| Attribute | Options | Impact |
|-----------|---------|--------|
| Face visible | yes/no | Faces increase engagement 38% |
| Eye contact | direct/away/at product | Direct = highest engagement |
| Expression | smiling/neutral/serious | Smiling = +10-15% CTR |
| Authenticity | real/stock/AI | Real > Stock > AI |
| Demographic match | matches target / mismatch | Must match audience |

**Face Positioning:**

| Position | Best For |
|----------|----------|
| Center | Direct response, testimonials |
| Rule of thirds | Lifestyle, aspirational |
| Looking at product | Product focus ads |
| Looking at CTA | Directional cue |

### 3.2 Product Analysis

| Attribute | Options |
|-----------|---------|
| Visibility | prominent / visible / subtle / hidden |
| Context | in use / isolated / lifestyle / packaging |
| Angle | front / 3/4 / side / top-down |
| Scale reference | clear / unclear / none |

### 3.3 Text Overlay Analysis

**Facebook guideline: <20% text coverage**
**Optimal: 5-15% for feed ads**

| Text Element | Check |
|--------------|-------|
| Headline | Position? Readable at thumbnail? |
| Subheadline | Present? Clear? |
| Price/offer | Visible? Compelling? |
| CTA text | Stands out? |

---

## Phase 4: Platform-Specific Analysis

### 4.1 Placement Dimensions

| Placement | Ratio | Dimensions |
|-----------|-------|------------|
| Feed (Square) | 1:1 | 1080×1080 |
| Feed (Portrait) | 4:5 | 1080×1350 |
| Feed (Landscape) | 1.91:1 | 1200×628 |
| Stories/Reels | 9:16 | 1080×1920 |
| Right Column | 1.91:1 | 1200×628 |

### 4.2 Safe Zone Analysis

```
Stories/Reels Safe Zone:
┌────────────────────┐
│ ▓▓▓ TOP 14% ▓▓▓▓▓▓ │ ← Profile pic, username
│                    │
│    SAFE ZONE       │ ← Key content here
│    (72% of height) │
│                    │
│ ▓▓▓ BOTTOM 14% ▓▓▓ │ ← CTA button, reactions
└────────────────────┘
```

**Checklist:**
- [ ] Key message in safe zone?
- [ ] Face/product not cut off?
- [ ] CTA not hidden by platform UI?

### 4.3 Thumbnail Test

| Size | Key Elements Visible? | Text Readable? |
|------|----------------------|----------------|
| 200×200 | | |
| 100×100 | | |
| 50×50 | | |

---

## Phase 5: Performance Correlation

### 5.1 Metrics vs Benchmarks

| Metric | Ad Value | Account Avg | Status |
|--------|----------|-------------|--------|
| CTR | % | % | above/below |
| CPC | € | € | above/below |
| CPM | € | € | above/below |
| Frequency | | | |

### 5.2 Visual Element → Performance

| Visual Element | Likely Impact |
|----------------|---------------|
| Face with eye contact | +CTR |
| High contrast CTA | +CTR |
| Cluttered composition | -CTR |
| Stock photo feel | -CTR |
| Text too small | -CTR |

---

## Phase 6: A/B Testing Recommendations

### Single Variable Testing (ONE at a time)

**Person Variants:**
| Test | When to Try |
|------|-------------|
| With person vs without | If no person currently |
| Direct eye contact vs looking at product | If person present |
| Smiling vs neutral | If not smiling |
| Real person vs illustrated | If using stock |

**Composition Variants:**
| Test | When to Try |
|------|-------------|
| Close-up vs full scene | If wide shot |
| Product in use vs isolated | If product alone |
| Lifestyle vs studio | If studio shot |
| Minimal vs detailed background | If busy background |

**Text Variants:**
| Test | When to Try |
|------|-------------|
| With overlay vs clean | Always worth testing |
| Headline top vs bottom | If headline present |
| Benefit vs feature focused | Always |
| With price vs without | If price not shown |

---

## Phase 7: Generate Insights

### Strengths (Find At Least 2)
- Above-benchmark metrics
- Strong visual hierarchy
- Effective color psychology
- Clear focal point
- High-quality image
- Authentic feel
- Platform-optimized dimensions

### Weaknesses (Be Specific)
- Below-benchmark metrics
- Cluttered composition
- Poor contrast/readability
- Stock photo feel
- Missing key elements
- Wrong dimensions
- Text too small

### Recommendation Format

```
RECOMMENDATION: [Title]
Priority: High/Medium/Low
Current State: [What exists]
Problem: [Why it hurts performance]
Solution: [Specific change]
Expected Impact: [What improvement]
A/B Test: [How to validate]
```

---

## Common Patterns & Fixes

### Stock Photo Feel
- **Symptom**: Below-average CTR
- **Fix**: Use authentic imagery - real customers, UGC

### No Clear Focal Point
- **Symptom**: Low CTR, quick scroll-past
- **Fix**: Simplify composition, blur background

### Text Illegible at Thumbnail
- **Symptom**: Low CTR despite strong offer
- **Fix**: Increase text size, add solid background bar

### Missing Human Element
- **Symptom**: Lower engagement than competitors
- **Fix**: Add person using/holding product

### Wrong Aspect Ratio
- **Symptom**: Poor performance on specific placements
- **Fix**: Create placement-specific versions

---

## Quality Checklist

- [ ] Full-resolution image reviewed
- [ ] All ad copy documented
- [ ] Performance metrics collected
- [ ] Primary focal point identified
- [ ] Visual hierarchy documented
- [ ] Composition techniques identified
- [ ] Dominant colors listed
- [ ] Contrast levels rated
- [ ] Person analysis complete (if applicable)
- [ ] Platform safe zones checked
- [ ] Thumbnail readability tested
- [ ] At least 3 recommendations
- [ ] Each recommendation has rationale
- [ ] A/B test suggestions included
