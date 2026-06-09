# Code Simplification Plan: Meta Ads MCP Server

**Project:** meta-ads-mcp (Python MCP Server for Meta Advertising API)
**Created:** 2026-01-09
**Status:** Active

---

## Clarifications (User Decisions)

| Setting | Decision |
|---------|----------|
| Complexity scoring | Weighted formula: `Σ(indent_level × count)` normalized to 1-10 scale |
| Public functions | MCP tools (`@mcp.tool()`) + any non-underscore functions |
| Conflict priority | Readability first - clarity over cleverness |
| Checkpoints | Full stop - wait for explicit "proceed" |
| Pre-check | All tests must pass before Phase 2 |
| Commits | One commit per file |

---

## Project Configuration

```yaml
repository: /Users/raouldevries/Work/Apps/Meta Ads Analyzer/meta-ads-mcp
language: Python 3.11+
framework: FastMCP
test_command: cd meta-ads-mcp && source venv/bin/activate && pytest tests/ -v
core_modules:
  - meta_ads_mcp/core/api.py
  - meta_ads_mcp/core/insights.py
  - meta_ads_mcp/core/campaigns.py
  - meta_ads_mcp/core/ads.py
  - meta_ads_mcp/core/adsets.py
  - meta_ads_mcp/core/targeting.py
  - meta_ads_mcp/core/accounts.py
  - meta_ads_mcp/core/auth.py
  - meta_ads_mcp/core/pagination.py
  - meta_ads_mcp/core/retry.py
```

---

## Violation Detection Criteria

### Severity 1: Critical (Must Fix)
- [ ] Missing type hints on public functions
- [ ] Bare `except:` or `except Exception:` without re-raise
- [ ] Mutable default arguments (`def func(items=[])`)
- [ ] Hardcoded credentials or secrets
- [ ] Unused imports

### Severity 2: High (Should Fix)
- [ ] Nested conditionals > 3 levels deep
- [ ] Functions > 50 lines
- [ ] Duplicate code blocks > 10 lines
- [ ] Missing docstrings on MCP tools
- [ ] Inconsistent error handling patterns

### Severity 3: Medium (Consider)
- [ ] String formatting with `.format()` instead of f-strings
- [ ] Manual dict building instead of comprehensions
- [ ] Overly verbose boolean logic
- [ ] Unnecessary variable assignments
- [ ] Comments that duplicate code

### Severity 4: Low (Optional)
- [ ] Import order not following convention
- [ ] Inconsistent quote style
- [ ] Line length > 100 chars
- [ ] Missing trailing commas in multi-line structures

---

## Python Standards for This Project

### Import Organization

```python
# 1. Standard library (alphabetical)
import json
import os
from typing import Any, Optional

# 2. Third-party (alphabetical)
import httpx
from fastmcp import FastMCP

# 3. Local imports (alphabetical)
from .api import MetaAdsApi
from .auth import get_access_token
from .retry import with_retry
```

### MCP Tool Pattern

All tools must follow this structure:

```python
@mcp.tool()
async def tool_name(
    required_param: str,
    optional_param: Optional[str] = None,
    access_token: Optional[str] = None
) -> str:
    """
    Brief description of the tool.

    Args:
        required_param: What this parameter does
        optional_param: Optional parameter description
        access_token: Meta API access token (optional - uses cached if not provided)

    Returns:
        JSON string with result data
    """
    token = access_token or await get_access_token()
    api = MetaAdsApi(token)

    result = await api.method(required_param)
    return json.dumps(result, indent=2)
```

### Error Handling Pattern

```python
# Use MetaApiError for API errors
from .api import MetaApiError

try:
    result = await api.call()
except MetaApiError as e:
    if e.status_code == 401:
        # Handle auth error specifically
        raise MetaApiError("Token expired", status_code=401)
    raise  # Re-raise other API errors

# Never silently swallow errors
# Avoid: except Exception: pass
```

### Async Patterns

```python
# Use async context managers for HTTP clients
async with httpx.AsyncClient() as client:
    response = await client.get(url)

# Use asyncio.gather for parallel operations
results = await asyncio.gather(
    api.get_campaigns(account_id),
    api.get_adsets(account_id),
    api.get_ads(account_id)
)
```

---

## Execution Phases

### Phase 1: Audit & Prioritize

**Commands to run:**

```bash
cd meta-ads-mcp && source venv/bin/activate

# Find files with most recent changes
git log --oneline --name-only -50 | grep "\.py$" | sort | uniq -c | sort -rn | head -20

# Count lines per module
wc -l meta_ads_mcp/core/*.py | sort -rn

# Find complex functions (high indentation)
grep -n "^        " meta_ads_mcp/core/*.py | cut -d: -f1 | uniq -c | sort -rn | head -10
```

**Priority Score Formula:**
```
Score = (Recent Changes × 2) + (Line Count / 100) + (Complexity × 3)
```

**Output: Priority List Table**

| Rank | File | Changes | Lines | Complexity | Score | Status |
|------|------|---------|-------|------------|-------|--------|
| 1 | api.py | ? | ? | ? | ? | Pending |
| 2 | insights.py | ? | ? | ? | ? | Pending |
| ... | ... | ... | ... | ... | ... | ... |

**CHECKPOINT**: Present priority list → wait for user approval before proceeding.

---

### Phase 2: Per-File Simplification

For each file in priority order:

**Step 1: Document Current State**
```markdown
## File: [filename]
- Lines: [count]
- Functions: [count]
- MCP Tools: [count]
- Test Coverage: [file exists? tests pass?]
```

**Step 2: Identify Violations**
- Check against Severity 1-4 criteria
- List specific line numbers

**Step 3: Apply Fixes**
- Fix Severity 1 issues first
- Preserve all functionality
- Run tests after each significant change

**Step 4: Commit**
```bash
git add [file]
git commit -m "Simplify [module]: [brief description]

- [Change 1]
- [Change 2]

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

**CHECKPOINT**: After every 3 files, report progress and ask to continue.

---

### Phase 3: Cross-Module Cleanup

**Find duplicates:**
```bash
# Look for similar function signatures
grep -h "^async def\|^def" meta_ads_mcp/core/*.py | sort | uniq -d
```

**Consolidation candidates:**

| Pattern | Found In | Action |
|---------|----------|--------|
| Token resolution | accounts, campaigns, ads | Already in auth.py |
| JSON serialization | multiple | Use common helper |
| Error response format | multiple | Standardize structure |

**CHECKPOINT**: Report consolidation plan → confirm before applying.

---

### Phase 4: Validate & Report

**Validation commands:**
```bash
# Full test suite
pytest tests/ -v

# Type checking (if mypy available)
mypy meta_ads_mcp/ --ignore-missing-imports

# Live API test
python -c "from meta_ads_mcp.core import mcp; print('Import OK')"
```

**Final Summary Template:**

```markdown
## Code Simplification Summary

### Files Modified
| File | Before (lines) | After (lines) | Change |
|------|---------------|---------------|--------|
| api.py | 250 | 235 | -15 |
| ... | ... | ... | ... |

### Violations Fixed
- Severity 1: [count]
- Severity 2: [count]
- Severity 3: [count]

### Tests
- Before: [X] passing
- After: [Y] passing
- New failures: [none/list]

### Commits
1. [hash] - [message]
2. [hash] - [message]
```

---

## Common Simplifications for This Project

### 1. Parameter Building

```python
# Before
params = {}
if limit:
    params["limit"] = limit
if fields:
    params["fields"] = fields
if time_range:
    params["time_range"] = time_range

# After
params = {k: v for k, v in {
    "limit": limit,
    "fields": fields,
    "time_range": time_range
}.items() if v is not None}
```

### 2. Response Formatting

```python
# Before
result = {"data": data}
if error:
    result["error"] = error
return json.dumps(result)

# After
return json.dumps({
    "data": data,
    **({"error": error} if error else {})
}, indent=2)
```

### 3. Early Returns

```python
# Before
def process(data):
    if data:
        if data.get("valid"):
            if data.get("items"):
                return process_items(data["items"])
    return None

# After
def process(data):
    if not data:
        return None
    if not data.get("valid"):
        return None
    if not data.get("items"):
        return None
    return process_items(data["items"])
```

---

## Anti-Patterns to Avoid

1. **Over-abstraction**: Don't create helpers for one-time operations
2. **Nested ternaries**: Use if/elif/else for readability
3. **Dense one-liners**: Split complex comprehensions into steps
4. **Silent error swallowing**: Always handle or re-raise
5. **Premature optimization**: Clarity over cleverness

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `pytest tests/ -v` | Run all tests |
| `pytest tests/test_api.py -v` | Run specific test file |
| `git diff --stat` | See changes summary |
| `git log --oneline -10` | Recent commits |

| Convention | Example |
|------------|---------|
| Budget values | Cents (10000 = $100) |
| Account IDs | `act_XXXXXXXXX` prefix |
| Objectives | `OUTCOME_TRAFFIC`, `OUTCOME_SALES` |
| Token param | `access_token: Optional[str] = None` |
