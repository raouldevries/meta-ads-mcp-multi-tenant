# Installation & Multi-Account Plan: Meta Ads Analyzer

**Created:** 2026-01-08
**Status:** Planned (not yet implemented)

## Overview
1. Push current single-account version to GitHub (stable fallback)
2. Create separate repo for multi-account version
3. Implement multi-credential manager on macOS
4. Test thoroughly to ensure backward compatibility
5. Push complete code to multi-account repo
6. Clone on Windows laptop (single pull with everything ready)

---

# Local Development Strategy

## Two Separate Project Folders

| Folder | Purpose | MCP Server Name |
|--------|---------|-----------------|
| `Meta Ads Analyzer` | Single account (UNTOUCHED) | `meta-ads-mcp` (current) |
| `Meta Ads Analyzer Multi` | Multi-account (development) | `meta-ads-mcp-multi` (new) |

## Why Two Folders?
- **Original stays intact**: Never touch working single-account code
- **Side-by-side**: Both MCP servers can run simultaneously
- **Easy fallback**: Switch between servers in Claude Desktop
- **Clean comparison**: Compare implementations easily

---

# GitHub Repository Strategy

## Two Separate Repositories

| Repository | Folder | Status |
|------------|--------|--------|
| `meta-ads-analyzer` | Meta Ads Analyzer | Push when ready |
| `meta-ads-analyzer-multi` | Meta Ads Analyzer Multi | Push after development complete |

---

# Step 0: Copy Folder and Set Up Multi-Account Environment

## 0.1 Copy the project folder (keep original intact):

```bash
cd /Users/raouldevries/Work/Apps

# Copy entire folder
cp -r "Meta Ads Analyzer" "Meta Ads Analyzer Multi"

# Navigate to new folder
cd "Meta Ads Analyzer Multi"

# Remove old git history (fresh start)
rm -rf .git
rm -rf meta-ads-mcp/.git

# Remove old venv (will create fresh one)
rm -rf meta-ads-mcp/venv
```

## 0.2 Set up fresh Python environment in Multi folder:

```bash
cd /Users/raouldevries/Work/Apps/Meta\ Ads\ Analyzer\ Multi/meta-ads-mcp

# Create new virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .
```

## 0.3 Add new MCP server to Claude Code config:

Add to `~/.claude/settings.json` or equivalent:

```json
{
  "mcpServers": {
    "meta-ads-mcp": {
      "command": "/Users/raouldevries/Work/Apps/Meta Ads Analyzer/meta-ads-mcp/venv/bin/python",
      "args": ["-m", "meta_ads_mcp"],
      "cwd": "/Users/raouldevries/Work/Apps/Meta Ads Analyzer/meta-ads-mcp"
    },
    "meta-ads-mcp-multi": {
      "command": "/Users/raouldevries/Work/Apps/Meta Ads Analyzer Multi/meta-ads-mcp/venv/bin/python",
      "args": ["-m", "meta_ads_mcp"],
      "cwd": "/Users/raouldevries/Work/Apps/Meta Ads Analyzer Multi/meta-ads-mcp"
    }
  }
}
```

## 0.4 Verify both servers work:

- Original `meta-ads-mcp`: Should work exactly as before
- New `meta-ads-mcp-multi`: Should work identically (same code for now)

---

# Step 1: Push Single-Account Version to GitHub

## On macOS (original folder - don't modify, just push):

```bash
cd /Users/raouldevries/Work/Apps/Meta\ Ads\ Analyzer

# Verify .env is in .gitignore (security check)
cat .gitignore | grep ".env"

# Check git status
git status

# If not initialized:
git init
git branch -M main

# Create repo at github.com/new named "meta-ads-analyzer", then:
git remote add origin https://github.com/YOUR_USERNAME/meta-ads-analyzer.git

# Add and commit
git add .
git commit -m "Initial commit: Meta Ads MCP server (single account)"

# Push
git push -u origin main
```

## Verify on GitHub:
- [ ] Repository created
- [ ] All files uploaded
- [ ] `.env` is NOT in the repo (check!)
- [ ] README.md visible

---

# Development Approach

## Key Constraints

| Constraint | How we satisfy it |
|------------|-------------------|
| **Single clone on Windows** | Complete all development on macOS before pushing |
| **Keep repo working** | Backward compatible changes + thorough testing |
| **Cross-platform (macOS + Windows)** | Use `pathlib` and `platform.system()` patterns |

## Development Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 0: Copy folder & set up Multi environment             │
│                                                             │
│  /Meta Ads Analyzer (UNTOUCHED - single account)            │
│         │                                                   │
│         └──► cp -r ──► /Meta Ads Analyzer Multi             │
│                        (new development folder)             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  macOS: Two MCP Servers Running Side-by-Side                │
│                                                             │
│  meta-ads-mcp        → /Meta Ads Analyzer      (untouched)  │
│  meta-ads-mcp-multi  → /Meta Ads Analyzer Multi (develop)   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Develop in /Meta Ads Analyzer Multi                        │
│                                                             │
│  1. Implement multi-credential feature                      │
│  2. Test with existing .env (backward compat)               │
│  3. Test with new credentials.json                          │
│  4. Run all tests                                           │
│  5. Push to GitHub (meta-ads-analyzer-multi)                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Push both repos to GitHub when ready                       │
│                                                             │
│  meta-ads-analyzer       ← /Meta Ads Analyzer (single)      │
│  meta-ads-analyzer-multi ← /Meta Ads Analyzer Multi         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Windows (Production Machine)                               │
│                                                             │
│  Clone meta-ads-analyzer-multi (multi-account version)      │
│  OR                                                         │
│  Clone meta-ads-analyzer (single-account fallback)          │
│                                                             │
│  1. Clone once (gets complete, tested code)                 │
│  2. Set up Python + venv                                    │
│  3. Configure credentials.json (multi) or .env (single)     │
│  4. Configure Claude Desktop                                │
│  5. Done - no further pulls needed                          │
└─────────────────────────────────────────────────────────────┘
```

## Backward Compatibility Strategy

**Current setup must keep working:**
```
User calls tool
    ↓
Has account_name param?
    → Yes: Use credentials.json (NEW)
    → No: Has credentials.json?
        → Yes: Use default account (NEW)
        → No: Use .env (CURRENT - unchanged)
```

**Verification before pushing:**
```bash
# Test 1: Current .env still works (no credentials.json)
"List my ad accounts"  # Must work exactly as before

# Test 2: New feature works
"List configured accounts"
"Get ads for company_a"
```

---

# Cross-Platform Compatibility

## Why it works on both macOS and Windows

The codebase already uses cross-platform patterns. Example from `auth.py`:

```python
def _get_token_cache_path(self) -> pathlib.Path:
    if platform.system() == "Windows":
        base_path = pathlib.Path(os.environ.get("APPDATA", ""))
    elif platform.system() == "Darwin":  # macOS
        base_path = pathlib.Path.home() / "Library" / "Application Support"
    else:  # Linux
        base_path = pathlib.Path.home() / ".config"
```

## Cross-Platform Requirements for New Code

| Requirement | How to implement |
|-------------|------------------|
| File paths | Use `pathlib.Path`, never string concatenation |
| OS detection | Use `platform.system()` |
| Config locations | Handle Windows/macOS/Linux separately |
| Environment vars | Use `os.environ` (works everywhere) |
| No hardcoded separators | Use `/` with pathlib, it auto-converts |

## Config File Locations

| Platform | credentials.json path |
|----------|----------------------|
| macOS | `~/Library/Application Support/meta-ads-mcp/credentials.json` |
| Windows | `%APPDATA%\meta-ads-mcp\credentials.json` |
| Linux | `~/.config/meta-ads-mcp/credentials.json` |

---

# Part 1: Windows Installation

## Prerequisites (Windows Laptop)

- **Python 3.10+** - Download from [python.org](https://python.org), check "Add to PATH"
- **Git** - Download from [git-scm.com](https://git-scm.com)
- **Claude Desktop** - Download from [claude.ai/download](https://claude.ai/download)

## Step 1: Clone from GitHub (after macOS development is complete)

```powershell
cd ~\Projects
git clone https://github.com/YOUR_USERNAME/meta-ads-analyzer.git
cd meta-ads-analyzer\meta-ads-mcp
```

## Step 2: Python Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e .
```

## Step 3: Create credentials.json

```powershell
# Create config directory
New-Item -Path "$env:APPDATA\meta-ads-mcp" -ItemType Directory -Force

# Create credentials file
notepad "$env:APPDATA\meta-ads-mcp\credentials.json"
```

Add your accounts (see format in Part 2 below).

## Step 4: Configure Claude Desktop

Open: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "meta-ads-mcp": {
      "command": "C:\\Users\\USERNAME\\Projects\\meta-ads-analyzer\\meta-ads-mcp\\venv\\Scripts\\python.exe",
      "args": ["-m", "meta_ads_mcp"],
      "cwd": "C:\\Users\\USERNAME\\Projects\\meta-ads-analyzer\\meta-ads-mcp"
    }
  }
}
```

---

# Part 2: Multi-Credential Manager (Code Changes)

## Goal
Support 4-10 Meta business accounts with named credentials. Claude can:
- Query different accounts by name: "Get ads for CompanyA"
- Compare data across accounts
- Switch accounts mid-conversation

## Design: Credential Configuration

### New config file: `credentials.json`
```json
{
  "default": "company_a",
  "accounts": {
    "company_a": {
      "display_name": "Company A Ads",
      "meta_app_id": "123456789",
      "meta_app_secret": "abc...",
      "meta_access_token": "EAA...",
      "meta_ad_account_id": "act_123456"
    },
    "company_b": {
      "display_name": "Company B Ads",
      "meta_app_id": "987654321",
      "meta_app_secret": "xyz...",
      "meta_access_token": "EAA...",
      "meta_ad_account_id": "act_654321"
    }
  }
}
```

## Files to Modify

### 1. `meta_ads_mcp/core/credentials.py` (NEW FILE)
Create credential manager class:
```python
class CredentialManager:
    def __init__(self):
        self.credentials = {}
        self.current_account = None
        self._load_credentials()

    def _get_credentials_path(self) -> pathlib.Path:
        # Cross-platform path handling
        if platform.system() == "Windows":
            base_path = pathlib.Path(os.environ.get("APPDATA", ""))
        elif platform.system() == "Darwin":
            base_path = pathlib.Path.home() / "Library" / "Application Support"
        else:
            base_path = pathlib.Path.home() / ".config"
        return base_path / "meta-ads-mcp" / "credentials.json"

    def list_accounts(self) -> List[str]
    def get_credential(self, account_name: str) -> Optional[dict]
    def set_current_account(self, account_name: str) -> bool
    def get_current_credential(self) -> Optional[dict]
```

### 2. `meta_ads_mcp/core/auth.py`
Modify `get_current_access_token()`:
- Add `account_name: Optional[str] = None` parameter
- If account_name provided, get token from CredentialManager
- Fall back to current behavior for backward compatibility

### 3. `meta_ads_mcp/core/api.py`
Update `meta_api_tool` decorator:
- Extract `account_name` from kwargs if present
- Pass to `get_current_access_token(account_name=...)`

### 4. New MCP Tools (add to `credentials.py`)
```python
@mcp.tool()
async def list_configured_accounts() -> str:
    """List all configured Meta Ads accounts"""

@mcp.tool()
async def switch_account(account_name: str) -> str:
    """Switch to a different configured account"""

@mcp.tool()
async def get_current_account() -> str:
    """Get the currently active account name"""
```

### 5. Update all existing tools
Add optional parameter to each tool:
```python
async def get_campaigns(
    account_id: str,
    account_name: Optional[str] = None,  # NEW
    access_token: Optional[str] = None,
    ...
)
```

## Files Changed Summary

| File | Action | Changes |
|------|--------|---------|
| `core/credentials.py` | CREATE | Credential manager, 3 new tools |
| `core/auth.py` | MODIFY | Add account_name parameter |
| `core/api.py` | MODIFY | Update decorator |
| `core/accounts.py` | MODIFY | Add account_name param |
| `core/campaigns.py` | MODIFY | Add account_name param |
| `core/adsets.py` | MODIFY | Add account_name param |
| `core/ads.py` | MODIFY | Add account_name param |
| `core/insights.py` | MODIFY | Add account_name param |
| `core/targeting.py` | MODIFY | Add account_name param |
| `core/__init__.py` | MODIFY | Export new functions |

---

# Implementation Order

## Phase 0: Copy Folder & Set Up Multi Environment (DO THIS FIRST)
- [ ] Copy "Meta Ads Analyzer" → "Meta Ads Analyzer Multi"
- [ ] Remove old .git from Multi folder
- [ ] Create fresh venv in Multi folder
- [ ] Add `meta-ads-mcp-multi` to Claude Code MCP config
- [ ] Verify both MCP servers work

## Phase 1: Develop Multi-Account Feature (in Multi folder only)
- [ ] Create `credentials.py` with CredentialManager class
- [ ] Modify auth.py and api.py decorator
- [ ] Add account_name to all tools
- [ ] Add new MCP tools (list_configured_accounts, switch_account, etc.)

## Phase 2: Test Multi-Account Feature
- [ ] Test backward compatibility (no credentials.json → uses .env)
- [ ] Test with credentials.json
- [ ] Run all existing tests
- [ ] Verify original `meta-ads-mcp` still works unchanged

## Phase 3: Push Both Repos to GitHub
- [ ] Push original folder → `meta-ads-analyzer` repo
- [ ] Push Multi folder → `meta-ads-analyzer-multi` repo
- [ ] Verify .env not exposed in either repo

## Phase 4: Deploy on Windows
- [ ] Clone chosen repo (multi or single)
- [ ] Set up Python + venv
- [ ] Configure credentials
- [ ] Configure Claude Desktop
- [ ] Test

---

# Verification Checklist

## Before Pushing (on macOS)

- [ ] Existing .env setup still works (no credentials.json present)
- [ ] `"List my ad accounts"` returns correct data
- [ ] New credentials.json is loaded correctly
- [ ] `"List configured accounts"` shows all accounts
- [ ] `"Switch to account_x"` changes active account
- [ ] `"Get ads for account_y"` queries correct account
- [ ] All existing tests pass
- [ ] No hardcoded paths (use pathlib everywhere)

## After Cloning (on Windows)

- [ ] Python venv created successfully
- [ ] `pip install -e .` completes
- [ ] credentials.json created in correct location
- [ ] Claude Desktop config is correct
- [ ] MCP server starts without errors
- [ ] `"List configured accounts"` works
- [ ] Can query different accounts

---

# Security Notes

- `credentials.json` contains secrets - add to `.gitignore`
- Each machine has its own credentials.json (not in repo)
- Each business has independent credentials
- Rotate tokens periodically per Meta's guidelines

---

# Part 3: Scalable Data Architecture (Large API Responses)

## The Problem

Met 10+ ad accounts wordt de API response te groot voor Claude om te verwerken:

| Scenario | Geschatte Response Size | Claude Desktop | Claude Code |
|----------|------------------------|----------------|-------------|
| 1 account, 50 ads | ~100 KB | ❌ Hangt | ✅ Werkt (via bestanden) |
| 5 accounts, 250 ads | ~500 KB | ❌ Hangt | ⚠️ Traag |
| 10 accounts, 500 ads | ~1+ MB | ❌ Onmogelijk | ❌ Te groot |

### Waarom dit gebeurt

```
Meta API ──(grote response)──► Claude
                                  │
                                  ▼
                            Context Window
                            ┌─────────────┐
                            │ ░░░░░░░░░░░ │ ← API data vult context
                            │ ░░░░░░░░░░░ │
                            │ ░░░░░░░░░░░ │
                            │             │ ← Geen ruimte voor analyse
                            └─────────────┘
```

**Claude Code** lost dit op door grote responses naar bestanden te schrijven en in chunks te lezen.
**Claude Desktop** heeft deze mogelijkheid niet.

---

## De Oplossing: Hiërarchische Data Architectuur

### Concept

```
┌─────────────────────────────────────────────────────────────────────────┐
│  NIVEAU 1: Portfolio Overzicht (alle accounts)                          │
│                                                                         │
│  Tool: get_portfolio_overview()                                         │
│  Response: ~5 KB (compact samenvatting)                                 │
│                                                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │Account A│ │Account B│ │Account C│ │Account D│ │Account E│  ...      │
│  │€12,340  │ │€8,120   │ │€5,890   │ │€15,200  │ │€3,450   │           │
│  │ROAS 4.2 │ │ROAS 3.8 │ │ROAS 5.1 │ │ROAS 2.9 │ │ROAS 4.5 │           │
│  └────┬────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│       │                                                                 │
│       ▼ "Vertel me meer over Account A"                                 │
└───────┼─────────────────────────────────────────────────────────────────┘
        │
┌───────┴─────────────────────────────────────────────────────────────────┐
│  NIVEAU 2: Account Deep-Dive (1 account)                                │
│                                                                         │
│  Tool: get_account_summary(account_name="company_a")                    │
│  Response: ~15-20 KB                                                    │
│                                                                         │
│  Account A - Campaigns:                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                    │
│  │Campaign 1    │ │Campaign 2    │ │Campaign 3    │ ...                │
│  │Reach         │ │Clicks        │ │Conversions   │                    │
│  │€5,230 spend  │ │€4,120 spend  │ │€2,990 spend  │                    │
│  │128K reach    │ │12K clicks    │ │340 purchases │                    │
│  └──────┬───────┘ └──────────────┘ └──────────────┘                    │
│         │                                                               │
│         ▼ "Welke ads in Campaign 1 presteren het best?"                 │
└─────────┼───────────────────────────────────────────────────────────────┘
          │
┌─────────┴───────────────────────────────────────────────────────────────┐
│  NIVEAU 3: Campaign/Ad Details                                          │
│                                                                         │
│  Tool: get_insights(account_name="company_a", campaign_id="123")        │
│  Response: ~30-50 KB (alle ads in 1 campaign)                           │
│                                                                         │
│  Campaign 1 - Alle Ads met volledige metrics:                           │
│  - Impressions, clicks, spend, CTR, CPC, CPM                            │
│  - Reach, frequency                                                     │
│  - Video completion: 25%, 50%, 75%, 100%, ThruPlay                      │
│  - Conversions, ROAS                                                    │
│  - Actions breakdown                                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Waarom dit werkt

| Niveau | Wat Claude ziet | Response Size | Claude kan analyseren? |
|--------|-----------------|---------------|------------------------|
| 1 | Alle accounts, key metrics | ~5 KB | ✅ Ja, volledig |
| 2 | Alle campaigns van 1 account | ~15-20 KB | ✅ Ja, volledig |
| 3 | Alle ads van 1 campaign | ~30-50 KB | ✅ Ja, volledig |

**Totale data geanalyseerd:** 100% (in stappen)
**Maximale response per stap:** <50 KB
**Claude vormt eigen mening:** ✅ Ja, op basis van ruwe data

---

## Nieuwe MCP Tools (te bouwen)

### Tool 1: `get_portfolio_overview`

**Doel:** Compact overzicht van alle geconfigureerde accounts

```python
@mcp_server.tool()
@meta_api_tool
async def get_portfolio_overview(
    time_range: Union[str, Dict[str, str]] = "last_30d",
    access_token: Optional[str] = None
) -> str:
    """
    Get a compact overview of all configured Meta Ads accounts.

    Returns key metrics per account: spend, reach, clicks, conversions, ROAS.
    Use this as the starting point before diving into specific accounts.

    Args:
        time_range: Time period for metrics (default: last_30d)

    Returns:
        Compact summary of all accounts (~5KB response)
    """
```

**Voorbeeld output:**
```json
{
  "period": "2025-12-09 to 2026-01-08",
  "total_accounts": 10,
  "total_spend": "€45,230.50",
  "total_reach": "2,340,000",
  "accounts": [
    {
      "name": "company_a",
      "display_name": "Company A Ads",
      "spend": "€12,340.00",
      "reach": "450,000",
      "clicks": "28,500",
      "conversions": 342,
      "roas": 4.2,
      "active_campaigns": 5,
      "active_ads": 23,
      "top_campaign": "Summer Sale 2025",
      "status": "healthy"
    },
    {
      "name": "company_b",
      "display_name": "Company B Ads",
      "spend": "€8,120.00",
      "reach": "280,000",
      "clicks": "15,200",
      "conversions": 189,
      "roas": 3.8,
      "active_campaigns": 3,
      "active_ads": 15,
      "top_campaign": "Brand Awareness",
      "status": "needs_attention"
    }
    // ... more accounts
  ],
  "insights": {
    "best_performer": "company_a",
    "highest_roas": "company_c (5.1)",
    "highest_spend": "company_d (€15,200)",
    "accounts_needing_attention": ["company_b", "company_f"]
  }
}
```

### Tool 2: `get_account_summary`

**Doel:** Gedetailleerd overzicht van 1 account met alle campaigns

```python
@mcp_server.tool()
@meta_api_tool
async def get_account_summary(
    account_name: str,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    access_token: Optional[str] = None
) -> str:
    """
    Get detailed summary of a specific account with all campaigns.

    Args:
        account_name: Name of the configured account
        time_range: Time period for metrics (default: last_30d)

    Returns:
        Account details with campaign breakdown (~15-20KB response)
    """
```

**Voorbeeld output:**
```json
{
  "account": {
    "name": "company_a",
    "display_name": "Company A Ads",
    "id": "act_123456789"
  },
  "period": "2025-12-09 to 2026-01-08",
  "totals": {
    "spend": "€12,340.00",
    "reach": "450,000",
    "impressions": "1,230,000",
    "clicks": "28,500",
    "ctr": "2.32%",
    "cpc": "€0.43",
    "conversions": 342,
    "roas": 4.2
  },
  "campaigns": [
    {
      "id": "120224179753990619",
      "name": "Summer Sale 2025",
      "objective": "OUTCOME_SALES",
      "status": "ACTIVE",
      "spend": "€5,230.00",
      "reach": "180,000",
      "clicks": "12,400",
      "conversions": 156,
      "roas": 4.8,
      "ad_sets": 3,
      "active_ads": 8,
      "best_ad": "Summer Sale - Video v2"
    },
    {
      "id": "120224179753990620",
      "name": "Brand Awareness Q1",
      "objective": "OUTCOME_AWARENESS",
      "status": "ACTIVE",
      "spend": "€3,890.00",
      "reach": "270,000",
      "impressions": "890,000",
      "frequency": 3.3,
      "video_views": 45000,
      "ad_sets": 2,
      "active_ads": 6
    }
    // ... more campaigns
  ],
  "top_performers": {
    "best_cpc": {"ad": "Retargeting - Carousel", "cpc": "€0.12"},
    "best_ctr": {"ad": "Summer Sale - Video v2", "ctr": "4.8%"},
    "best_roas": {"campaign": "Summer Sale 2025", "roas": 4.8}
  },
  "recommendations": [
    "Campaign 'Brand Awareness Q1' has high frequency (3.3) - consider expanding audience",
    "Ad set 'Cold Audience' has low CTR (0.8%) - consider new creative"
  ]
}
```

### Tool 3: `analyze_video_performance`

**Doel:** Video-specifieke analyse met completion rates

```python
@mcp_server.tool()
@meta_api_tool
async def analyze_video_performance(
    account_name: Optional[str] = None,
    campaign_id: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    min_impressions: int = 100,
    access_token: Optional[str] = None
) -> str:
    """
    Analyze video ad performance with completion rates.

    Returns all video ads with 25%, 50%, 75%, 100% completion metrics.
    Can filter by account and/or campaign.

    Args:
        account_name: Filter by account (optional)
        campaign_id: Filter by campaign (optional)
        time_range: Time period (default: last_30d)
        min_impressions: Minimum impressions to include (default: 100)

    Returns:
        Video performance analysis with completion funnel
    """
```

**Voorbeeld output:**
```json
{
  "period": "2025-12-09 to 2026-01-08",
  "filter": {
    "account": "company_a",
    "campaign": null,
    "min_impressions": 100
  },
  "summary": {
    "total_video_ads": 12,
    "total_video_views": 145000,
    "avg_completion_rate": {
      "25%": "72%",
      "50%": "45%",
      "75%": "28%",
      "100%": "18%"
    },
    "total_thruplays": 26000
  },
  "video_ads": [
    {
      "ad_name": "Video ad versie 1",
      "campaign": "Reach - Alle locaties",
      "impressions": 144952,
      "reach": 128464,
      "video_views": 14315,
      "completion": {
        "25%": 10467,
        "50%": 2648,
        "75%": 1292,
        "100%": 798
      },
      "thruplay": 8500,
      "completion_rate": {
        "25%": "73.1%",
        "50%": "18.5%",
        "75%": "9.0%",
        "100%": "5.6%"
      },
      "avg_watch_time": "8.2s",
      "performance": "above_average"
    },
    {
      "ad_name": "NYMA | Doelgroep breed | Video",
      "campaign": "Clicks | Nijmegen NYMA",
      "impressions": 53094,
      "reach": 33423,
      "video_views": 13197,
      "completion": {
        "25%": 10990,
        "50%": 5114,
        "75%": 3235,
        "100%": 1906
      },
      "thruplay": 7200,
      "completion_rate": {
        "25%": "83.3%",
        "50%": "38.8%",
        "75%": "24.5%",
        "100%": "14.4%"
      },
      "avg_watch_time": "12.1s",
      "performance": "excellent"
    }
    // ... more videos
  ],
  "insights": {
    "best_retention": "NYMA | Doelgroep breed | Video (83.3% @ 25%)",
    "best_completion": "Rotterdam Delfshaven Video (17.4% @ 100%)",
    "needs_improvement": ["Den Bosch Video v2 (low retention)"],
    "recommendation": "Videos met talking head format hebben 2x hogere completion dan product-only videos"
  }
}
```

### Tool 4: `compare_accounts`

**Doel:** Vergelijk performance tussen accounts

```python
@mcp_server.tool()
@meta_api_tool
async def compare_accounts(
    account_names: List[str],
    metrics: List[str] = ["spend", "roas", "ctr", "cpc"],
    time_range: Union[str, Dict[str, str]] = "last_30d",
    access_token: Optional[str] = None
) -> str:
    """
    Compare performance metrics between multiple accounts.

    Args:
        account_names: List of account names to compare
        metrics: Metrics to compare (default: spend, roas, ctr, cpc)
        time_range: Time period (default: last_30d)

    Returns:
        Side-by-side comparison with rankings
    """
```

### Tool 5: `get_insights` (updated)

Update de bestaande `get_insights` tool met:

```python
@mcp_server.tool()
@meta_api_tool
async def get_insights(
    object_id: str,
    account_name: Optional[str] = None,  # NEW: for multi-account
    access_token: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",  # CHANGED: safer default
    breakdown: str = "",
    level: str = "ad",
    limit: int = 25,  # CHANGED: lower default for Claude Desktop
    after: str = "",
    output_format: str = "full",  # NEW: "full" | "compact" | "csv"
    action_attribution_windows: Optional[List[str]] = None
) -> str:
    """
    Get performance insights for a campaign, ad set, ad or account.

    Args:
        object_id: ID of the campaign, ad set, ad or account
        account_name: Name of configured account (for multi-account setups)
        time_range: Time period (default: last_30d - changed from 'maximum')
        output_format: Response format:
            - "full": Complete JSON with all fields (default, best for Claude Code)
            - "compact": Reduced JSON with essential fields only
            - "csv": CSV format for maximum compression
        limit: Results per page (default: 25 - reduced for Claude Desktop compatibility)
        ...
    """
```

---

## Output Formats (voor get_insights)

### Format: `full` (default, voor Claude Code)

Huidige volledige JSON output - alle velden, geen compressie.
- **Grootte:** ~2-3 KB per ad
- **Gebruik:** Claude Code (kan grote bestanden aan)

### Format: `compact` (voor Claude Desktop)

Gereduceerde JSON met alleen essentiële velden:

```json
{
  "ad_name": "Video ad v1",
  "campaign": "Reach Campaign",
  "spend": "€120.33",
  "impr": 144952,
  "reach": 128464,
  "clicks": 1336,
  "ctr": "0.92%",
  "cpc": "€0.09",
  "conv": 45,
  "roas": 3.8,
  "video": {"p25": 10467, "p50": 2648, "p75": 1292, "p100": 798}
}
```
- **Grootte:** ~300-500 bytes per ad
- **Reductie:** ~80-85%

### Format: `csv` (maximale compressie)

```csv
ad_name,campaign,spend,impr,reach,clicks,ctr,cpc,conv,roas,p25,p50,p75,p100
Video ad v1,Reach Campaign,120.33,144952,128464,1336,0.92,0.09,45,3.8,10467,2648,1292,798
NYMA Video,Clicks Nijmegen,89.12,53094,33423,2841,5.35,0.03,28,4.2,10990,5114,3235,1906
```
- **Grootte:** ~150-200 bytes per ad
- **Reductie:** ~90-95%

---

## Implementation Priority

### Fase 1: Core Infrastructure (eerst bouwen)
1. [ ] Update `get_insights` met `output_format` parameter
2. [ ] Update `get_insights` met veiligere defaults (`last_30d`, `limit=25`)
3. [ ] Voeg video completion velden toe ✅ (DONE - 2026-01-08)

### Fase 2: Portfolio Tools (na multi-account)
4. [ ] Bouw `get_portfolio_overview`
5. [ ] Bouw `get_account_summary`
6. [ ] Bouw `compare_accounts`

### Fase 3: Specialized Analysis Tools
7. [ ] Bouw `analyze_video_performance`
8. [ ] Bouw `analyze_top_performers`
9. [ ] Bouw `get_recommendations`

---

## Workflow Voorbeelden

### Voorbeeld 1: Portfolio Check (10 accounts)

```
Gebruiker: "Hoe presteren mijn accounts deze maand?"

Claude: [roept get_portfolio_overview() aan]
        → Krijgt 5KB compact overzicht van alle 10 accounts
        → Analyseert en vormt eigen mening

Claude: "Van je 10 accounts presteert Company C het beste met een ROAS van 5.1.
         Company B en F hebben aandacht nodig - hun ROAS is onder de 3.0 gedaald.
         Totale spend deze maand: €45,230. Wil je dat ik dieper in een
         specifiek account duik?"
```

### Voorbeeld 2: Account Deep-Dive

```
Gebruiker: "Vertel me meer over Company A"

Claude: [roept get_account_summary(account_name="company_a") aan]
        → Krijgt 15KB met alle campaigns en metrics
        → Analyseert data, ziet patronen

Claude: "Company A heeft 5 actieve campaigns. Je Summer Sale campaign is de
         star performer met ROAS 4.8. Maar je Brand Awareness campaign heeft
         een hoge frequency (3.3) - je publiek ziet dezelfde ads te vaak.
         Ik zou aanraden om de doelgroep uit te breiden of nieuwe creatives
         te testen. Wil je de individuele ads zien?"
```

### Voorbeeld 3: Video Analyse

```
Gebruiker: "Welke video's presteren het best qua completion?"

Claude: [roept analyze_video_performance() aan]
        → Krijgt gestructureerde video data met completion rates
        → Vergelijkt en analyseert

Claude: "Je NYMA video heeft de beste retention: 83% kijkt 25% en 14% kijkt
         alles. Je Rotterdam Delfshaven video heeft de hoogste absolute
         completion met 1,315 complete views.

         Opvallend: video's met mensen in beeld hebben 2x hogere completion
         dan product-only video's. Overweeg meer talking-head content."
```

---

## Claude Code vs Claude Desktop: Wanneer welke?

| Gebruik | Aanbevolen Tool | Waarom |
|---------|-----------------|--------|
| Dagelijkse check | Claude Desktop + Portfolio tools | Snelle overzichten |
| Diepgaande analyse | Claude Code | Kan alle ruwe data aan |
| Ad-hoc vragen | Claude Desktop + Compact format | Snel antwoord |
| Rapportage maken | Claude Code | Volledige data nodig |
| Vergelijkingen | Claude Desktop + Compare tool | Gestructureerde output |
| Debugging/troubleshooting | Claude Code | Toegang tot alle details |

---

## Bestaande Code Wijzigingen (2026-01-08)

### Video Completion Metrics Toegevoegd

**Bestand:** `meta_ads_mcp/core/insights.py`

**Wijziging:** Video completion velden toegevoegd aan `get_insights`:

```python
# VOOR:
"fields": "account_id,account_name,...,cost_per_action_type"

# NA:
"fields": "account_id,account_name,...,cost_per_action_type,video_p25_watched_actions,video_p50_watched_actions,video_p75_watched_actions,video_p100_watched_actions,video_thruplay_watched_actions"
```

**Status:** ✅ Geïmplementeerd, werkt in Claude Code. Claude Desktop vereist herstart om wijziging op te pikken.

**Nieuwe velden beschikbaar:**
- `video_p25_watched_actions` - Aantal views tot 25%
- `video_p50_watched_actions` - Aantal views tot 50%
- `video_p75_watched_actions` - Aantal views tot 75%
- `video_p100_watched_actions` - Aantal views tot 100%
- `video_thruplay_watched_actions` - ThruPlay views (15 sec of volledige video)
