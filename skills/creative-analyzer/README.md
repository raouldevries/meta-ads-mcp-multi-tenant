# Meta Ads MCP - Complete Architecture Guide

This document explains how the Meta Ads MCP application works, including the relationship between MCP servers, skills, and the agent.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                              USER                                           │
│                    "Analyze ad 120239386324810661"                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         CLAUDE CODE (Agent)                                 │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        Agent Loop                                    │   │
│   │                                                                      │   │
│   │  1. Receive user request                                            │   │
│   │  2. Load relevant skill (creative-analyzer)                         │   │
│   │  3. Call MCP tools to fetch data                                    │   │
│   │  4. Apply skill expertise to analyze                                │   │
│   │  5. Generate output (insights + optional HTML report)               │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                               │
                    │                               │
         ┌──────────▼──────────┐       ┌───────────▼───────────┐
         │                     │       │                       │
         │    MCP SERVER       │       │       SKILLS          │
         │   (Connectivity)    │       │     (Expertise)       │
         │                     │       │                       │
         │  meta-ads-mcp/      │       │  skills/creative-     │
         │                     │       │  analyzer/            │
         └──────────┬──────────┘       └───────────────────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │                     │
         │   META GRAPH API    │
         │                     │
         │  • Ad Accounts      │
         │  • Campaigns        │
         │  • Ad Creatives     │
         │  • Performance Data │
         │  • Video Metrics    │
         │                     │
         └─────────────────────┘
```

---

## What is MCP?

**Model Context Protocol (MCP)** is a standard for connecting AI agents to external tools and data sources.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   MCP = The USB-C of AI                                                    │
│                                                                            │
│   Just like USB-C provides a universal port for connecting devices,       │
│   MCP provides a universal protocol for connecting AI to tools.           │
│                                                                            │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐            │
│   │ Claude  │     │ Claude  │     │ Other   │     │ Other   │            │
│   │ Desktop │     │  Code   │     │  Agent  │     │  Agent  │            │
│   └────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘            │
│        │               │               │               │                  │
│        └───────────────┴───────────────┴───────────────┘                  │
│                                │                                          │
│                         ┌──────▼──────┐                                   │
│                         │     MCP     │                                   │
│                         │  Protocol   │                                   │
│                         └──────┬──────┘                                   │
│                                │                                          │
│        ┌───────────────┬───────┴───────┬───────────────┐                  │
│        │               │               │               │                  │
│   ┌────▼────┐     ┌────▼────┐     ┌────▼────┐     ┌────▼────┐            │
│   │  Meta   │     │ Google  │     │ Notion  │     │  File   │            │
│   │  Ads    │     │ Drive   │     │   API   │     │ System  │            │
│   └─────────┘     └─────────┘     └─────────┘     └─────────┘            │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## MCP Server vs Skill

| Aspect | MCP Server | Skill |
|--------|------------|-------|
| **What it is** | Code that connects to external APIs | Documentation with procedural knowledge |
| **Provides** | **Connectivity** - ability to fetch data | **Expertise** - knowledge of HOW to use that data |
| **Format** | Python/TypeScript code with tool decorators | Markdown files + optional scripts |
| **Lives in** | `meta-ads-mcp/` package | `skills/` folder |
| **Example** | `get_ads()` tool returns ad data | "Analyze the hook in first 3 seconds" |

### Analogy: Doctor's Office

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   MCP Server = Medical Equipment                                           │
│   • MRI machine (fetches brain scans)                                     │
│   • Blood pressure monitor (fetches vitals)                               │
│   • Lab equipment (fetches test results)                                  │
│                                                                            │
│   Skill = Medical Training                                                 │
│   • How to interpret an MRI scan                                          │
│   • What blood pressure numbers mean                                      │
│   • When to order which tests                                             │
│                                                                            │
│   Neither is useful alone. Together = effective diagnosis.                │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## This Application's Components

### 1. MCP Server (`meta-ads-mcp/`)

The MCP server provides tools to interact with Meta's Advertising API:

```
meta-ads-mcp/
├── meta_ads_mcp/
│   └── core/
│       ├── server.py           # MCP server entry point
│       ├── auth.py             # Token management
│       ├── accounts.py         # get_ad_accounts()
│       ├── campaigns.py        # get_campaigns(), create_campaign()
│       ├── adsets.py           # get_adsets(), create_adset()
│       ├── ads.py              # get_ads(), get_ad_image()
│       ├── insights.py         # get_insights(), get_video_insights()
│       ├── targeting.py        # search_interests(), get_behaviors()
│       ├── creative_analysis.py # analyze_video_creative()
│       └── credentials.py      # Multi-tenant credential management
└── pyproject.toml
```

**Key Tools:**

| Tool | Purpose |
|------|---------|
| `get_ad_accounts()` | List all accessible ad accounts |
| `get_campaigns()` | Fetch campaigns with optional spend filter |
| `get_ads()` | Fetch ads with performance metrics |
| `get_ad_image()` | Download ad creative images |
| `analyze_video_creative()` | Full video analysis with frames/subtitles |
| `get_video_insights()` | Retention curves, watch metrics |

### 2. Skills (`skills/`)

Skills provide the expertise layer:

```
skills/
└── creative-analyzer/
    ├── skill.md                # Entry point + metadata
    ├── README.md               # This file
    ├── workflows/
    │   ├── video-analysis.md   # Step-by-step video analysis
    │   └── image-analysis.md   # Step-by-step image analysis
    ├── scripts/
    │   └── generate_report.py  # HTML report generator
    └── templates/
        └── report.html         # Report template
```

### 3. Reports (`reports/`)

Generated analysis outputs:

```
reports/
├── image_analysis_elst_120239386324810661.html
├── video_creative_analysis.html
├── cpl_dashboard.html
└── ...
```

---

## Multi-Tenant Credentials System

The app supports multiple ad accounts across different businesses:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│                         credentials.json                                   │
│                                                                            │
│   {                                                                        │
│     "version": 2,                                                          │
│     "api_keys": {                                                          │
│       "business_a": { "access_token": "EAAxxxxxxx..." },                  │
│       "business_b": { "access_token": "EAAyyyyyyy..." }                   │
│     },                                                                     │
│     "accounts": {                                                          │
│       "client_alpha": {                                                    │
│         "display_name": "Client Alpha",                                   │
│         "ad_account_id": "act_111111",                                    │
│         "api_key": "business_a"          ◄─── Uses business_a's token    │
│       },                                                                   │
│       "client_beta": {                                                     │
│         "display_name": "Client Beta",                                    │
│         "ad_account_id": "act_222222",                                    │
│         "api_key": "business_a"          ◄─── Same token (same portfolio)│
│       },                                                                   │
│       "client_gamma": {                                                    │
│         "display_name": "Client Gamma",                                   │
│         "ad_account_id": "act_333333",                                    │
│         "api_key": "business_b"          ◄─── Different business         │
│       }                                                                    │
│     }                                                                      │
│   }                                                                        │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

Credentials file location:
• macOS:   ~/Library/Application Support/meta-ads-mcp/credentials.json
• Windows: %APPDATA%\meta-ads-mcp\credentials.json
• Linux:   ~/.config/meta-ads-mcp/credentials.json
```

---

## Request Flow Example

When a user asks: **"Analyze the Elst video ad"**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: User Request                                                        │
│                                                                             │
│   User: "Analyze the Elst video ad in the Nijmegen account"                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Skill Activation                                                    │
│                                                                             │
│   Claude detects: "analyze" + "ad" → triggers creative-analyzer skill      │
│   Loads: skills/creative-analyzer/skill.md                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: MCP Tool Calls                                                      │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ get_ads(account_name="nijmegen", search="Elst")                     │   │
│   │    └──► Returns ad_id: 120237318342120381                           │   │
│   │                                                                      │   │
│   │ analyze_video_creative(                                              │   │
│   │     ad_id="120237318342120381",                                     │   │
│   │     extract_frames=True,                                             │   │
│   │     extract_subtitles=True                                           │   │
│   │ )                                                                    │   │
│   │    └──► Returns video metrics, frames, subtitles                    │   │
│   │                                                                      │   │
│   │ get_video_insights(ad_id="120237318342120381")                      │   │
│   │    └──► Returns retention curve [100, 85, 52, 37, ...]              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Apply Skill Expertise                                               │
│                                                                             │
│   Using workflows/video-analysis.md, Claude:                                │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ Phase 1: Data Collection                                             │   │
│   │   • Parse video metadata                                             │   │
│   │   • Extract frame timestamps                                         │   │
│   │   • Collect subtitle text                                            │   │
│   │                                                                      │   │
│   │ Phase 2: Subtitle Analysis                                           │   │
│   │   • Classify each subtitle (hook, benefit, cta)                     │   │
│   │   • Identify hook in first 3 seconds                                │   │
│   │   • Map content to timestamps                                        │   │
│   │                                                                      │   │
│   │ Phase 3: Visual Analysis                                             │   │
│   │   • Person visible? Gender? Age?                                    │   │
│   │   • Eye contact with camera?                                        │   │
│   │   • Scene changes? Visual variety?                                  │   │
│   │                                                                      │   │
│   │ Phase 4: Content-Retention Mapping                                   │   │
│   │   • Match retention % to content at each second                     │   │
│   │   • Identify critical drop-off points                               │   │
│   │   • Correlate content with viewer behavior                          │   │
│   │                                                                      │   │
│   │ Phase 5: Generate Insights                                           │   │
│   │   • Issues: Hook is a question (high drop)                          │   │
│   │   • Strengths: High CTR, good visual variety                        │   │
│   │   • Recommendations: Lead with outcome, earlier CTA                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Output                                                              │
│                                                                             │
│   • Markdown analysis in chat                                               │
│   • Optional: HTML report saved to reports/                                │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Key Finding: 52% drop in first 3 seconds due to question hook      │   │
│   │                                                                      │   │
│   │  Recommendation: Replace "Waarom heb je voor My35' gekozen?"        │   │
│   │  with outcome: "Ik ben gaan skiën in Italië!"                       │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Video Analysis Deep Dive

The video analysis workflow correlates content with viewer retention:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   RETENTION CURVE + CONTENT MAPPING                                        │
│                                                                            │
│   100% ┤█                                                                  │
│        │█                                                                  │
│    85% ┤█░░                                                                │
│        │█░░                                                                │
│    52% ┤█░░░░░░                     "Why did you choose...?"              │
│        │█░░░░░░                     (Question = signal this is an ad)     │
│    37% ┤█░░░░░░░░                                                          │
│        │█░░░░░░░░                                                          │
│    22% ┤█░░░░░░░░░░░░                                                      │
│        │█░░░░░░░░░░░░                                                      │
│    15% ┤█░░░░░░░░░░░░░░░░░         "I went skiing in Italy!"              │
│        │█░░░░░░░░░░░░░░░░░         (Best content - only 15% see it)       │
│    10% ┤█░░░░░░░░░░░░░░░░░░░░░░                                            │
│        │█░░░░░░░░░░░░░░░░░░░░░░                                            │
│     0% ┼─────────────────────────────────────────────────────────          │
│        0s   3s   6s   9s   12s  15s  18s  21s  24s  27s  30s              │
│                                                                            │
│   INSIGHT: Move "skiing in Italy" to first 3 seconds!                     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Image Analysis Deep Dive

The image analysis workflow examines visual composition:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   VISUAL HIERARCHY ANALYSIS                                                │
│                                                                            │
│   ┌──────────────────────────────────┐                                    │
│   │  1st ─► Two people (trainer+client)                                   │
│   │  2nd ─► My35 logo                                                     │
│   │  3rd ─► "35 MINUTEN" headline                                         │
│   │  4th ─► Social proof (8.7 stars)                                      │
│   │  5th ─► "Elst" location badge                                         │
│   └──────────────────────────────────┘                                    │
│                                                                            │
│   COMPOSITION CHECK                                                        │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │ ☑ Rule of Thirds    ☑ Leading Lines    ☑ Framing                 │  │
│   │ ☐ Negative Space    ☑ High Contrast    ☑ Clear Focal Point       │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   TARGET AUDIENCE MATCH                                                    │
│   ┌────────────────────────────────────────────────────────────────────┐  │
│   │ Target: Women 50+                                                   │  │
│   │ Image:  Young male ~30s        ◄─── MISMATCH!                      │  │
│   │                                                                     │  │
│   │ Impact: Audience can't see themselves in ad → lower CTR            │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Running the Application

### 1. Start the MCP Server

```bash
cd meta-ads-mcp
source venv/bin/activate
python -m meta_ads_mcp
```

### 2. Configure Claude Desktop (optional)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "python",
      "args": ["-m", "meta_ads_mcp"],
      "cwd": "/path/to/meta-ads-mcp"
    }
  }
}
```

### 3. Use with Claude Code

Claude Code automatically detects and uses the MCP server. Just ask:

```
"Analyze the video ad for Nijmegen account"
"Why is this ad performing poorly?"
"Show me the retention curve for ad 123456789"
```

---

## Summary

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   META ADS MCP = MCP Server + Skills                                       │
│                                                                            │
│   ┌─────────────────────┐         ┌─────────────────────┐                 │
│   │    MCP SERVER       │    +    │       SKILLS        │                 │
│   │                     │         │                     │                 │
│   │  Provides the       │         │  Provides the       │                 │
│   │  ABILITY to fetch   │         │  KNOWLEDGE of how   │                 │
│   │  data from Meta     │         │  to analyze that    │                 │
│   │                     │         │  data effectively   │                 │
│   │  (connectivity)     │         │  (expertise)        │                 │
│   └─────────────────────┘         └─────────────────────┘                 │
│                                                                            │
│                              ═══════                                       │
│                                                                            │
│                   EFFECTIVE AD CREATIVE ANALYSIS                           │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```
