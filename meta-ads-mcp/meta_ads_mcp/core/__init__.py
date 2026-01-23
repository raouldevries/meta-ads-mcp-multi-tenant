"""Core functionality for Meta Ads API MCP package."""

from .server import mcp_server
from .retry import (
    with_retry,
    RetryConfig,
    MetaApiError,
    parse_meta_error,
    retry_with_backoff
)
from .accounts import get_ad_accounts, get_account_info
from .campaigns import get_campaigns, get_campaign_details, create_campaign
from .adsets import get_adsets, get_adset_details, update_adset
from .ads import get_ads, get_ad_details, get_ad_creatives, get_ad_image, update_ad
from .insights import get_insights
from . import authentication  # Import module to register conditional auth tools
from .server import login_cli, main
from .auth import login
from . import ads_library  # Import module to register conditional tools
from .budget_schedules import create_budget_schedule
from .targeting import search_interests, get_interest_suggestions, estimate_audience_size, search_behaviors, search_demographics, search_geo_locations
from . import reports  # Import module to register conditional tools
from . import duplication  # Import module to register conditional duplication tools
from .openai_deep_research import search, fetch  # OpenAI MCP Deep Research tools

# New modules for extended Meta API coverage
from . import audiences  # Custom Audiences, Saved Audiences, Lookalike Audiences
from . import pixels  # Meta Pixel management, custom conversions
from . import leads  # Lead forms and lead retrieval (requires leads_retrieval permission)
from . import analysis  # Analysis tools optimized for Claude context window

# Multi-tenant credential management
from . import account_tools  # list_configured_accounts, switch_account, etc.

# Creative analysis
from . import creative_analysis  # get_creative_type, get_creative_content, analyze_creative

__all__ = [
    'mcp_server',
    # Retry logic
    'with_retry',
    'RetryConfig',
    'MetaApiError',
    'parse_meta_error',
    'retry_with_backoff',
    # Account tools
    'get_ad_accounts',
    'get_account_info',
    'get_campaigns',
    'get_campaign_details',
    'create_campaign',
    'get_adsets',
    'get_adset_details',
    'update_adset',
    'get_ads',
    'get_ad_details',
    'get_ad_creatives',
    'get_ad_image',
    'update_ad',
    'get_insights',
    # Note: 'get_login_link' is registered conditionally by the authentication module
    'login_cli',
    'login',
    'main',
    'create_budget_schedule',
    'search_interests',
    'get_interest_suggestions',
    'estimate_audience_size',
    'search_behaviors',
    'search_demographics',
    'search_geo_locations',
    'search',  # OpenAI MCP Deep Research search tool
    'fetch',   # OpenAI MCP Deep Research fetch tool
] 