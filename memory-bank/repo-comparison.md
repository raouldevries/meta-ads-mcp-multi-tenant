# Repo Comparison: Meta Ads MCP vs brijr/meta-mcp

This note compares your local repo (`meta-ads-mcp/`) with the GitHub repo `brijr/meta-mcp` (cloned to `meta-mcp-compare/` for analysis). Focus is on feature parity, tool coverage, and possible improvements while pursuing the same goal.

## High-level differences
- Stack/packaging: Python + FastMCP (yours) vs TypeScript + MCP SDK (theirs). Theirs ships as an npm package and defaults to stdio.
- Auth posture: Yours emphasizes Pipeboard login + local OAuth callback. Theirs exposes OAuth/token tools and an AuthManager.
- API lifecycle: Theirs has built-in rate limiting, retry/backoff, and pagination helpers; yours has strong error handling but no global backoff layer.

## Tool coverage: they have that you don’t
- OAuth utilities: token exchange/refresh/validation tools.
- Diagnostics/help: health check, capabilities, AI guidance, quick fixes, API reference, error codes.
- Audience creation/maintenance: create/update/delete custom audiences, lookalikes, audience insights.
- Creative workflow helpers: validations, best practices, A/B test setup, creative performance, upload-from-URL.
- Analytics helpers: performance comparison, attribution data, export.
- Resource endpoints: campaign/insight/audience resources.

## Tool coverage: you have that they don’t
- Lead gen tooling: lead forms, leads, quality score.
- Pixels & conversions: pixels, offline conversions, custom conversions.
- Ads Library search.
- Campaign/ad/adset duplication tools.
- Targeting search utilities (interests, demographics, geo).
- Ad preview + creative previews + image save/upload utilities.
- Streamable HTTP server mode + auth middleware.
- OpenAI deep research tools.

## Notable parity gaps
- Campaign lifecycle: they expose pause/resume/delete tools; you likely rely on update status but don’t expose explicit tools.
- Audience mgmt: you can list audiences but not create/update/delete/lookalikes.
- Creative guidance: you can preview and create creatives, but you don’t have their validation/troubleshooting/A/B helpers.
- Export & attribution: you have insights variants, but they add compare/export/attribution tools.

## Implementation differences worth noting
- Rate limiting/backoff: theirs uses a global rate limiter + retry/backoff; you handle errors but don’t retry globally.
- Pagination: theirs has helpers for multi-page results; you expose cursor in some endpoints but not all.
- API versioning: yours hardcodes v22.0; theirs adds v23 compliance tooling.

## Improvement ideas (based on their repo)
1. Add centralized retry/backoff + rate-limit handling (e.g., respect `Retry-After`).
2. Add pagination helpers so list tools can optionally fetch all pages.
3. Add diagnostic tools: `health_check`, `get_capabilities`, and a short AI guidance tool.
4. Add token utilities: `get_token_info`, `validate_token`, and a long-lived refresh helper.
6. Add creative validation/best-practices helpers and optional A/B test wrappers.
7. Add export helpers (CSV/JSON) for insights or fold into reports.
8. Make API version configurable via env and document it.

## Suggested analytics helpers (for ads, campaigns, creatives)
- `compare_entities`: Compare ads/campaigns/ad sets by IDs over a time range; return a compact table plus deltas for key metrics (spend, impressions, clicks, CTR, CPC, CPA, ROAS).
- `compare_creatives`: Compare creatives or ads by IDs; return headlines, descriptions, primary text, and top metrics for quick review.did
- `list_creative_assets`: Retrieve image/video URLs, dimensions, and status for all creatives tied to a campaign/ad set/ad.

## Token/context reduction patterns in brijr/meta-mcp
- Summary-first responses: analytics tools return aggregated metrics + rankings instead of raw row dumps.
- Narrow defaults: `get_insights` defaults to small limits and short time ranges to keep payloads small.
- Pre-aggregated resources: dashboards and trend endpoints return compact summaries instead of full datasets.
- Hard caps: comparison endpoints limit the number of objects compared in one call.
- Explicit pagination: helpers make it easy to fetch pages without loading everything at once.
- Creative analysis summary: bulk creative analysis returns stats and recommendations, not full creative objects.
- Guidance + diagnostics: built-in guidance and health/capabilities reduce trial-and-error calls.
- Export is heavy: `export_insights` can return large CSV/JSON payloads and should be used sparingly with LLMs.
## Extensive analytics helpers patch list (full-stack perspective)
This is an implementation roadmap for adding Claude-friendly analytics helpers to `meta-ads-mcp` without changing the core architecture.

### 1) Core helper tools (MCP)
- Add `compare_entities` tool:
  - Inputs: `entity_type` (campaign/adset/ad), `entity_ids` (list), `date_preset` or `time_range`, `fields` (optional), `breakdowns` (optional), `limit` (optional).
  - Output: per-entity summary metrics + rankings + deltas.
  - Implementation: fetch insights per ID (or use batch), run an aggregation reducer, compute deltas/rankings server-side.
- Add `get_campaign_performance` tool:
  - Inputs: `campaign_id`, `date_preset` or `time_range`.
  - Output: campaign metadata + summary metrics + daily breakdown.
  - Implementation: wrapper over `get_insights` with a fixed field set and summary reducer.
- Add `get_attribution_summary` tool:
  - Inputs: `object_id`, `date_preset` or `time_range`.
  - Output: conversions by attribution window + cost per conversion.
  - Implementation: request `actions`, `cost_per_action_type`, and `action_attribution_windows` breakdown.
- Add `export_insights` tool:
  - Inputs: `object_id`, `level`, `format` (csv/json), `fields`, `date_preset` or `time_range`.
  - Output: metadata + data payload (CSV/JSON).
  - Implementation: call insights once with `limit` and serialize.

### 2) Creative analytics helpers
- Add `compare_creatives` tool:
  - Inputs: `creative_ids` or `ad_ids`, `date_preset`/`time_range`.
  - Output: headline/primary_text/description + key metrics (CTR, CPC, CPA, ROAS).
  - Implementation: map creatives to ads, call insights at ad level, join creative text fields.
- Add `list_creative_assets` tool:
  - Inputs: `campaign_id` or `adset_id` or `ad_id`.
  - Output: image/video hashes, URLs, dimensions, status.
  - Implementation: traverse ads → creatives → assets, surface only critical fields.
- Add `analyze_account_creatives` tool:
  - Output: summary counts, avg lengths, CTA distribution, optimization recommendations.
  - Implementation: compute statistical summary, no raw creative dump.

### 3) Data reduction + response shaping
- Standardize compact response schemas:
  - Use `summary`, `rankings`, `query_parameters`, `data_size`, `total_count`.
  - Return raw rows only when explicitly requested.
- Default limits:
  - `get_insights` default `limit=25`, `date_preset=last_7d`.
  - `compare_entities` limit to 5–10 entities unless explicitly overridden.
- Add `fields` presets:
  - `basic`, `efficiency`, `revenue` preset arrays to avoid verbose user input.

### 4) Pagination & batching support
- Add a pagination helper in Python:
  - `collect_all_pages(fetch_fn, limit, max_pages, max_items)` generator + caps.
  - Optional tool param `fetch_all`.
- Add batch request helper (optional):
  - Combine multiple insights calls into a single batch to reduce round trips.

### 5) Rate limiting + retry/backoff
- Centralize backoff in `make_api_request`:
  - Detect 429/4xx limit codes.
  - Respect `Retry-After`.
  - Use exponential backoff with jitter.
- Add soft throttling to bulk helper calls.

### 6) Diagnostics + guidance
- Add `health_check`, `get_capabilities`, and `get_ai_guidance` tools:
  - Health: token validity + sample API call.
  - Capabilities: list tools, default presets, supported fields.
  - Guidance: explain common analytics workflows for Claude.

### 7) Testing + fixtures
- Add unit tests for reducers (summary/ranking/delta).
- Add integration smoke tests for `compare_entities`, `export_insights`.
- Add golden snapshots for JSON outputs to keep response shapes stable.

### 8) Docs + prompt hygiene
- Document helper tools in `README.md`.
- Add a short “Analytics workflows” section in `memory-bank`.
- Provide example prompts and expected outputs to guide Claude behavior.

## Monitoring basics for public use (no Sentry)
- Structured logs: JSON logs with tool name, request id, duration, account id, and error codes.
- Health checks: a `health_check` tool that validates auth + makes a cheap API call.
- Metrics: track per-tool counts, error rates, and avg latency; log periodic summaries.
- Log rotation: rotate file logs if not using stdout-only logging.
- Lightweight ops: a simple script/cron that pings health and alerts on failure.

---

## Additional Comparison Aspects (Added Jan 8, 2026)

### Type Safety & Validation
| Aspect | meta-ads-mcp (Python) | meta-mcp-compare (TypeScript) |
|--------|----------------------|------------------------------|
| Type System | Python type hints (partial) | Full TypeScript strict mode |
| Runtime Validation | Manual field validation | Zod schemas on all tool inputs |
| Schema Export | None | MCP-compatible JSON schemas |
| IDE Support | Basic autocomplete | Full IntelliSense + type inference |

**Why this matters**: Zod validation catches invalid inputs before API calls, reducing wasted requests and improving error messages.

### MCP Resources (Dynamic Data Access)
| Feature | meta-ads-mcp | meta-mcp-compare |
|---------|-------------|------------------|
| Resource Templates | ❌ Not implemented | ✅ URI-templated resources |
| Campaign Resources | - | `campaign://{id}`, `campaign://{id}/insights` |
| Audience Resources | - | `audience://{id}`, `audience://{id}/targeting` |
| Insight Resources | - | `insights://{account}/summary` |

**Why this matters**: MCP Resources enable AI assistants to request contextual data without explicit tool calls.

### Security Considerations
| Aspect | meta-ads-mcp | meta-mcp-compare |
|--------|-------------|------------------|
| Token Masking | ✅ Masked in logs | ✅ Only first 20 chars shown |
| Non-root Docker | ❌ Not specified | ✅ UID 1001 nodejs user |
| CSRF Protection | ❌ Not implemented | ✅ State parameter in OAuth |
| Input Sanitization | Manual | Zod schema enforcement |
| Credential Storage | File-based cache | Environment only (stateless) |

**Why this matters**: Security posture affects production deployment confidence.

### Deployment & Setup Complexity
| Aspect | meta-ads-mcp | meta-mcp-compare |
|--------|-------------|------------------|
| Primary Install | `pip install -e .` + venv | `npx` or `npm install` |
| Docker Support | Not provided | Multi-stage Dockerfile |
| Vercel Deployment | Not supported | Built-in adapter |
| Health Checks | ❌ | ✅ Every 30s in Docker |
| IDE Integration | Claude Desktop only | Claude Desktop + Cursor |

**Why this matters**: Easier setup reduces friction for new users.

### Testing Coverage
| Metric | meta-ads-mcp | meta-mcp-compare |
|--------|-------------|------------------|
| Test Framework | pytest | Jest |
| Test Files | 36 files (~13,648 lines) | Fewer but coverage enforced |
| Coverage Thresholds | Not enforced | 80% branches/functions/lines |
| E2E Tests | ✅ `@pytest.mark.e2e` | Manual via scripts |
| Regression Tests | ✅ Comprehensive | Basic |

### Async Job Support
| Feature | meta-ads-mcp | meta-mcp-compare |
|---------|-------------|------------------|
| Async Insights Jobs | ✅ `get_async_job_status`, `get_async_job_results` | ❌ |
| Large Export Handling | ✅ Async polling | Pagination only |

**Why this matters**: Enterprise accounts with millions of data points need async jobs.

### License & Commercial Use
| Aspect | meta-ads-mcp | meta-mcp-compare |
|--------|-------------|------------------|
| License | BUSL-1.1 | MIT |
| Commercial Use | Restricted | Unrestricted |

### Code Metrics
| Metric | meta-ads-mcp | meta-mcp-compare |
|--------|-------------|------------------|
| Core LOC | ~8,300 lines | ~11,560 lines |
| Tool Count | 63+ tools | 65+ tools |
| Graph API Version | v22.0 | v23.0 |

---

## Expert Assessment of Improvement Suggestions

### Priority Tier 1: Essential
| Suggestion | Assessment |
|------------|------------|
| Centralized retry/backoff | ✅ ESSENTIAL - Meta rate limits are aggressive |
| Health check tool | ✅ ESSENTIAL - 30 min to implement, saves hours |
| API v23.0 upgrade | ✅ ESSENTIAL - v22.0 deprecation coming |
| Pagination helpers | ✅ ESSENTIAL - Large accounts need this |

### Priority Tier 2: High Value
| Suggestion | Assessment |
|------------|------------|
| Token validation tools | ✅ RECOMMENDED - Prevents cryptic auth errors |
| Compare entities helper | ✅ RECOMMENDED - A/B testing is core to ads |
| Default limits + presets | ✅ RECOMMENDED - Prevents context overflow |
| Get capabilities tool | ✅ RECOMMENDED - Self-documenting API |

### Priority Tier 3: Nice-to-Have
| Suggestion | Assessment |
|------------|------------|
| Audience create/update/delete | ⚠️ SITUATIONAL - Increases permission requirements |
| Creative validation helpers | ⚠️ SITUATIONAL - Meta validates on submit anyway |
| Export to CSV/JSON | ⚠️ SITUATIONAL - LLMs don't need CSV |
| MCP Resource templates | ⚠️ SITUATIONAL - Adds complexity |

### Skip or Defer
| Suggestion | Assessment |
|------------|------------|
| Account-level rate limiter | ⚠️ OVER-ENGINEERED - Global backoff sufficient |
| AI guidance tool | ❌ SKIP - Let Claude handle guidance |
| Full Zod migration | ❌ SKIP - Pydantic achieves same in Python |

---

## Summary Recommendation

### Use meta-ads-mcp when you need:
- Lead generation workflows (unique)
- Pixel/conversion tracking
- Async jobs for large accounts
- HTTP transport mode
- Modular extensibility

### Use meta-mcp-compare when you need:
- TypeScript environment
- Cloud deployment (Vercel/Docker)
- Built-in rate limiting
- Quick npm install
- Audience write operations

### Hybrid Approach
Use **meta-ads-mcp as primary** and port over:
1. **Immediately**: Retry/backoff, health check, pagination helpers
2. **If needed**: Token validation, compare_entities helper
3. **Skip**: Audience writes, MCP Resources, cloud deployment
