# Facebook Marketing API - Insights Documentation

> Complete documentation: 11 pages

## Table of Contents

- [Insights API](#insights-api)
- [Breakdowns](#breakdowns)
- [Action Breakdowns](#action-breakdowns)
- [Limits & Best Practices](#limits-and-best-practices)
- [Tracking and Conversion Specs](#tracking-and-conversion-specs)
- [Marketing Mix Modeling](#marketing-mix-modeling)
- [Conversion Lift Measurement](#conversion-lift-measurement)
- [Split Testing](#split-testing)
- [Ad Volume](#ad-volume)
- [App Events API](#app-events-api)
- [Error Codes](#error-codes)

---

<a id="insights-api"></a>

## Insights API

> **Source:** [https://developers.facebook.com/docs/marketing-api/insights](https://developers.facebook.com/docs/marketing-api/insights)

# Insights API

Provides a single, consistent interface to retrieve ad statistics.

- [Breakdowns](https://developers.facebook.com/docs/marketing-api/insights/breakdowns) - Group results
- [Action Breakdowns](https://developers.facebook.com/docs/marketing-api/insights/action-breakdowns) - Understanding the response from action breakdowns.
- [Async Jobs](https://developers.facebook.com/docs/marketing-api/insights/async) - For requests with large results, use asynchronous jobs
- [Limits and Best Practices](https://developers.facebook.com/docs/marketing-api/insights/best-practices/) - Call limits, filtering and best practices.

Before you can get data on your ad's performance, you should set up your ads to track the metrics you are interested in. For that, you can use [URL Tags](https://developers.facebook.com/docs/reference/ads-api/adcreative), [Meta Pixel](https://developers.facebook.com/docs/marketing-api/audiences-api/pixel), and the [Conversions API](https://developers.facebook.com/docs/marketing-api/conversions-api).

## Before you begin

You will need:

- The `ads_read` permission.
- An [app](https://developers.facebook.com/apps/). See [Meta App Development](https://developers.facebook.com/docs/development) for more information.

[#](#)

## Campaign Statistics

To get the statistics of a campaign's last 7 day performance:

```
curl -G \
 -d "date_preset=last_7d" \
 -d "access_token=ACCESS_TOKEN" \
 "https://graph.facebook.com/API_VERSION/AD_CAMPAIGN_ID/insights"
```

To learn more, see the [Ad Insights Reference](https://developers.facebook.com/docs/marketing-api/insights).

[#](#)

## Making Calls

The Insights API is available as an edge on any ads object.

| API Method |
| ---------------------------- |
| act_<AD_ACCOUNT_ID>/insights |
| <CAMPAIGN_ID>/insights |
| <ADSET_ID>/insights |
| <AD_ID>/insights |

### Request

You can request specific fields with a comma-separated list in the `fields` parameters. For example:

```
v24.0
```

### Response

```
{
 "data": [
 {
 "impressions": "2466376",
 "date_start": "2009-03-28",
 "date_stop": "2016-04-01"
 }
 ],
 "paging": {
 "cursors": {
 "before": "MAZDZD",
 "after": "MAZDZD"
 }
 }
}
```

[#](#)

## Levels

Aggregate results at a defined object level. This automatically deduplicates data.

### Request

For example, get a campaign's insights on ad level.

```
v24.0
```

### Response

```
{
 "data": [
 {
 "impressions": "9708",
 "ad_id": "6142546123068",
 "date_start": "2009-03-28",
 "date_stop": "2016-04-01"
 },
 {
 "impressions": "18841",
 "ad_id": "6142546117828",
 "date_start": "2009-03-28",
 "date_stop": "2016-04-01"
 }
 ],
 "paging": {
 "cursors": {
 "before": "MAZDZD",
 "after": "MQZDZD"
 }
 }
}
```

If you don't have access to all ad objects at the requested level, the insights call returns no data. For example, while requesting insights with `level` set to `ad`, if you don't have access to one or more ad objects under the ad account, this API call will return a permission error.

[#](#)

## Attribution windows

The **conversion attribution window** provides timeframes that define when we attribute an event to an ad on a Meta app. For background information, see [Meta Business Help Center, About attribution windows](https://www.facebook.com/business/help/2198119873776795). We measure the actions that occur when a conversion event occurs and look back in time 1-day and 7-days. To view actions attributed to different attribution windows, make a request to `/{ad-account-id}/insights`. If you do not provide `action_attribution_windows` we use `7d_click` and provide it under `value`.

For example specify `action_attribution_windows` and 'value' is fixed at `7d_click` attribution window. Make a request to `act_10151816772662695/insights?action_attribution_windows=['1d_click','1d_view']` and get this result:

```
"spend": 2352.45,
"actions": [
{
"action_type": "link_click",
"value": 6608,
"1d_view": 86,
"1d_click": 6510
},
"cost_per_action_type": [
{
"action_type": "link_click",
"value": 0.35600030266344,
"1d_view": 27.354069767442,
"1d_click": 0.36135944700461
},

// if attribution window is _not_ specified in query. And note that the number under 'value' key is the same even if attribution window is specified.
// act_10151816772662695/insights
"spend": 2352.45,
"actions": [
{
"action_type": "link_click",
"value": 6608
},
"cost_per_action_type": [
{
"action_type": "link_click",
"value": 0.35600030266344
},
```

[#](#)

## Field Expansion

Request fields at the node level and by fields specified in [field expansion](https://developers.facebook.com/docs/graph-api/using-graph-api/).

### Request

```
v24.0
```

### Response

```
{
 "id": "6042542123268",
 "name": "My Website Clicks Ad",
 "insights": {
 "data": [
 {
 "impressions": "9708",
 "date_start": "2016-03-06",
 "date_stop": "2016-04-01"
 }
 ],
 "paging": {
 "cursors": {
 "before": "MAZDZD",
 "after": "MAZDZD"
 }
 }
 }
}
```

[#](#)

## Sorting

Sort results by providing the `sort` parameter with `{fieldname}_descending` or `{fieldname}_ascending`:

### Request

```
v24.0
```

### Response

```
{
 "data": [
 {
 "reach": 10742,
 "date_start": "2009-03-28",
 "date_stop": "2016-04-01"
 },
 {
 "reach": 5630,
 "date_start": "2009-03-28",
 "date_stop": "2016-04-03"
 },
 {
 "reach": 3231,
 "date_start": "2009-03-28",
 "date_stop": "2016-04-02"
 },
 {
 "reach": 936,
 "date_start": "2009-03-29",
 "date_stop": "2016-04-02"
 }
 ],
 "paging": {
 "cursors": {
 "before": "MAZDZD",
 "after": "MQZDZD"
 }
 }
}
```

[#](#)

## Ads Labels

Stats for all labels whose names are identical. Aggregated into a single value at an ad object level. See the [Ads Labels Reference](https://developers.facebook.com/docs/marketing-api/reference/ad-label) for more information.

### Request

```
v24.0
```

### Response

```
{
 "data": [
 {
 "unique_clicks": 74,
 "cpm": 0.81081081081081,
 "total_actions": 49,
 "date_start": "2015-03-01",
 "date_stop": "2015-03-31",
 },
 ],
 "paging": {
 "cursors": {
 "before": "MA==",
 "after": "MA==",
 }
 }
}
```

[#](#)

## Clicks definition

To better understand the click metrics that Meta offers today, please read the definitions and usage of each below:

- **Link Clicks, `actions:link_click`** - The number of clicks on ad links to select destinations or experiences, on or off Meta-owned properties. See [Ads Help Center, Link Clicks](https://www.facebook.com/business/help/659185130844708)
- **Clicks (All), `clicks`** - The metric counts multiple types of clicks on your ad, including certain types of interactions with the ad container, links to other destinations, and links to expanded ad experiences. See [Ads Help Center, Clicks(All)](https://www.facebook.com/business/help/787506997938504)

[#](#)

## Deleted and Archived Objects

Ad units may be `DELETED` or `ARCHIVED`. The stats of deleted or archived objects appear when you query their parents. This means if you query `impressions` at the ad set level, results include `impressions` from all ads in the set it, regardless of whether the the ads are in a deleted or archived state. See also, [Storing and Retrieving Ad Objects Best Practice](https://developers.facebook.com/docs/marketing-api/best-practices/storing_adobjects).

However, if you query using filtering, status filtering will be applied by default to return only Active objects. As a result, the total stats of the parent node may be greater than the stats of its children.

You can get the stats of `ARCHIVED` objects from their parent nodes though, by providing an extra `filtering` parameter.

### Request

To get the stats of all `ARCHIVED` ads in an ad account listed one by one:

```
v24.0
```

### Response

Note that only archived objects are returned in this response.

```
{
 "data": [
 {
 "impressions": "1741",
 "date_start": "2016-03-11",
 "date_stop": "2016-03-12"
 }
 ],
 "paging": {
 "cursors": {
 "before": "MAZDZD",
 "after": "MAZDZD"
 }
 }
}
```

### Deleted Objects Insights

You can query insights on deleted objects if you have their IDs or by using the `ad.effective_status` filter.

### Request

For example, if you have the ad set ID:

```
v24.0
```

In this example, we query with `ad.effective_status`:

```
POST https://graph.facebook.com/<VERSION>/act_ID/insights?access_token=token&appsecret_proof=proof&fields=ad_id,impressions&date_preset=lifetime&level=ad&filtering=[{"field":"ad.effective_status","operator":"IN","value":["DELETED"]}]
```

### Response

```
{
 "id": "6042147342661",
 "name": "My Like Campaign",
 "status": "DELETED",
 "insights": {
 "data": [
 {
 "impressions": "1741",
 "date_start": "2016-03-11",
 "date_stop": "2016-03-12"
 }
 ],
 "paging": {
 "cursors": {
 "before": "MAZDZD",
 "after": "MAZDZD"
 }
 }
 }
}
```

[#](#)

## Troubleshooting

### Timeouts

The most common issues causing failure at this endpoint are too many requests and time outs:

- On `/GET` or synchronous requests, you can get out-of-memory or timeout errors.
- On `/POST` or asynchronous requests, you can possibly get timeout errors. For asynchronous requests, it can take up to an hour to complete a request including retry attempts. For example if you make a query that tries to fetch large volume of data for many ad level objects.

#### Recommendations

- There is no explicit limit for when a query will fail. When it times out, try to break down the query into smaller queries by putting in filters like date range.
- Unique metrics are time consuming to compute. Try to query unique metrics in a separate call to improve performance of non-unique metrics.

### Rate Limiting

The Meta Insights API utilizes rate limiting to ensure an optimal reporting experience for all of our partners. For more information and suggestions, see our Insights API [Limits & Best Practices](https://developers.facebook.com/docs/marketing-api/insights/best-practices/).

### Discrepancy with Ads Manager

Beginning June 10, 2025, to reduce discrepancies with Meta Ads Manager, `use_unified_attribution_setting` and `action_report_time parameters` will be disregarded and API responses will mimic Ads Manager settings:

- Attributed `value`s will be based on Ad-Set-level attribution settings (similar to `use_unified_attribution_setting=true`), and inline/on-ad actions will be included in `1d_click` or `1d_view` attribution window data. After this change, standalone `inline` attribution window data will no longer be returned.
- Actions will be reported using `action_report_time=mixed`: on-Meta actions (like Link Clicks) will use impression-based reporting time; whereas off-Meta actions (like Web Purchases) will leverage conversion-based reporting time.

The default behavior of the API is different from the default behavior in Ads Manager. If you would like to observe the same behavior as in Ads Manager, please set the field `use_unified_attribution_setting` to true.

[#](#)

## Learn More

- [Ad Account Insights](https://developers.facebook.com/docs/marketing-api/reference/ad-account/insights)
- [Ad Campaign Insights](https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group/insights)
- [Ad Set Insights](https://developers.facebook.com/docs/marketing-api/reference/ad-campaign/insights)
- [Ad Insights](https://developers.facebook.com/docs/marketing-api/reference/adgroup/insights/)

Any endpoints not in the above list are not covered in this API. If you plan to include reports from Meta in your solution, see [Meta Platform Terms](https://developers.facebook.com/terms) and [Developer Policies for Marketing API](https://developers.facebook.com/devpolicy/).

[#](#)

[#](#)


---

<a id="breakdowns"></a>

## Breakdowns

> **Source:** [https://developers.facebook.com/docs/marketing-api/insights/breakdowns](https://developers.facebook.com/docs/marketing-api/insights/breakdowns)

[Marketing API](https://developers.facebook.com/docs/marketing-api)

- [Overview](https://developers.facebook.com/docs/marketing-api/overview)
- [Get Started](https://developers.facebook.com/docs/marketing-api/get-started)
- [Ad Creative](https://developers.facebook.com/docs/marketing-api/creative)
- [Bidding](https://developers.facebook.com/docs/marketing-api/bidding)
- [Ad Rules Engine](https://developers.facebook.com/docs/marketing-api/ad-rules)
- [Audiences](https://developers.facebook.com/docs/marketing-api/audiences)
- [Insights API](https://developers.facebook.com/docs/marketing-api/insights)

 - [Breakdowns](https://developers.facebook.com/docs/marketing-api/insights/breakdowns)
 - [Limits & Best Practices](https://developers.facebook.com/docs/marketing-api/insights/best-practices)
 - [Tracking and Conversion Specs](https://developers.facebook.com/docs/marketing-api/tracking-specs)
 - [Marketing Mix Modeling](https://developers.facebook.com/docs/marketing-api/insights/marketing-mix-modeling)
 - [Conversion Lift Measurement](https://developers.facebook.com/docs/marketing-api/guides/lift-studies)
 - [Split Testing](https://developers.facebook.com/docs/marketing-api/guides/split-testing)
 - [Ad Volume](https://developers.facebook.com/docs/marketing-api/insights-api/ads-volume)
 - [App Events API](https://developers.facebook.com/docs/marketing-api/app-event-api)
 - [Error Codes](https://developers.facebook.com/docs/marketing-api/insights/error-codes)
- [Brand Safety and Suitability](https://developers.facebook.com/docs/marketing-api/brand-safety-and-suitability)
- [Best Practices](https://developers.facebook.com/docs/marketing-api/best-practices)
- [Troubleshooting](https://developers.facebook.com/docs/marketing-api/troubleshooting)
- [API Reference](https://developers.facebook.com/docs/marketing-api/reference)
- [Changelog](https://developers.facebook.com/docs/marketing-api/marketing-api-changelog)

On This Page

[Insights API Breakdowns](#insights-api-breakdowns)

[Limitations](#limitations)

[Unavailable fields](#unavailable-fields)

[Restrictions for Off-Meta Action Metrics](#restrictions-for-off-meta-action-metrics)

[Action Metrics](#action-metrics)

[Generic Breakdowns](#genericbreakdowns)

[Hourly Breakdowns](#hourlybreakdowns)

[Action Breakdown](#actionsbreakdown)

[Total Count in actions](#total-count-in-actions)

[Combining Breakdowns](#combiningbreakdowns)

[Limitations](#combining-limitations)

# Insights API Breakdowns

You can group the Insights API results into different sets using breakdowns.

The Insights API can return several metrics that are estimated, in development, or both. Insights breakdown values are estimated. For more information, see [Insights API, Estimated and Deprecated Metrics](https://developers.facebook.com/docs/marketing-api/insights/estimated-in-development).

## Limitations

### Unavailable fields

The following fields cannot be requested when specifying a breakdown:

- `app_store_clicks`
- `newsfeed_avg_position`
- `newsfeed_clicks`
- `relevance_score`
- `newsfeed_impressions`

### Restrictions for Off-Meta Action Metrics

The following breakdowns will no longer be available for off-Meta action metrics.

#### Type 1

- `region`
- `dma`
- `hourly_stats_aggregated_by_audience_time_zone`
- `hourly_stats_aggregated_by_advertiser_time_zone`

#### Type 2

- `action_device`
- `action_destination`
- `action_target_id`
- `product_id`
- `action_carousel_card_id/action_carousel_card_name`
- `action_canvas_component_name`

**Rules related to queries containing above breakdowns:**

- **Type 1** — The Insights API will not return unsupported offsite metrics (e.g., actions metric with Type 1 breakdowns).
- **Type 2** — Offsite web metrics will continue to be returned from the API, however will not contain the breakdown value.
 The mobile metrics will not be returned anymore when queried with these breakdowns.

**Note:** The breakdowns listed above will still be supported for on-Meta metrics such as impressions, link clicks, etc. The changes will also not impact historical data prior to April 27, 2021; breakdowns for historical data will continue to be available.

### Action Metrics

Metrics will not be available under the following scenarios:

- When there is an attempted aggregation across multiple attribution settings
- When requested with impacted breakdowns (this restriction only applies for off-Meta & action types).

**Note:** Metrics will be available if querying with `action_attribution_windows=1d_click,7d_click,1d_view,incrementality` (not including the default window).

[#](#)

## Generic Breakdowns

The following breakdowns are available.

| Breakdown | Description |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| action_device | The device on which the conversion event you're tracking occurred. For example, \"Desktop\" if someone converted on a desktop computer. |
| action_canvas_component_name | Name of a component within a Canvas ad. |
| action_carousel_card_id | The ID of the specific carousel card that people engaged with when they saw your ad. |
| action_carousel_card_name | The specific carousel card that people engaged with when they saw your ad. The cards are identified by their headlines. |
| action_destination | The destination where people go after clicking on your ad. This could be your Facebook Page, an external URL for your conversion pixel or an app configured with the software development kit (SDK). |
| action_reaction | The number of reactions on your ads or boosted posts. The reactions button on an ad allows people to share different reactions on its content: Like, Love, Haha, Wow, Sad or Angry. |
| action_target_id | The ID of destination where people go after clicking on your ad. This could be your Facebook Page, an external URL for your conversion pixel or an app configured with the software development kit (SDK). |
| action_type | The kind of actions taken on your ad, Page, app or event after your ad was served to someone, even if they didn't click on it. Action types include Page likes, app installs, conversions, event responses, and more. |
| action_video_sound | The sound status (on/off) when someone plays your video ad. |
| action_video_type | Video metrics breakdown. |
| ad_format_asset | The ID of the ad format asset involved in impression, click, or action |
| age | The age range of the people you've reached. |
| app_id | The ID of the application associated with the ad account or campaign requested. The application information, including its ID, is viewable in theApp Dashboard.This breakdown is only supported by thetotal_postbacksfield. |
| body_asset | The ID of the body asset involved in impression, click, or action. |
| call_to_action_asset | The ID of the call to action asset involved in impression, click, or action. |
| country | The country where the people you've reached are located. This is based on information, such as a person's hometown, their current city, and the geographical location where they tend to be when they visit Meta. |
| description_asset | The ID of the description asset involved in impression, click, or action. |
| device_platform | The type of device, mobile or desktop, used by people when they viewed or clicked on an ad, as shown in ads reporting. |
| dma | The Designated Market Area (DMA) regions are the 210 geographic areas in the United States in which local television viewing is measured by The Nielsen Company. |
| frequency_value | The number of times an ad in your Reach and Frequency campaign was served to each Accounts Center account. |
| gender | Gender of people you've reached. People who don't list their gender are shown as 'not specified'. |
| hourly_stats_aggregated_by_advertiser_time_zone | Hourly breakdown aggregated by the time ads were delivered in the advertiser's time zone. For example, if your ads are scheduled to run from 9 AM to 11 AM, but they reach audiences in multiple time zones, they may deliver from 9 AM to 1 PM in the advertiser's time zone. Stats will be aggregated into four groups 9 AM - 10 AM, 10 AM - 11 AM, 11 AM - 12 PM, and 12 PM - 1 PM. |
| hourly_stats_aggregated_by_audience_time_zone | Hourly breakdown aggregated by the time ads were delivered in the audiences' time zone. For example, if your ads are scheduled to run from 9:00 am to 11:00 am, but they reach audiences in multiple time zones, they may deliver from 9:00 am to 1:00 pm in the advertiser's time zone. Stats are aggregated into 2 groups: 9:00 am to 10:00 am and 10:00 am to 11:00 am. |
| image_asset | The ID of the image asset involved in impression, click, or action. |
| impression_device | The device where your last ad was served to someone on Meta. For example \"iPhone\" if someone viewed your ad on an iPhone. |
| is_conversion_id_modeled | A boolean flag that indicates whether theconversion_bitsare modeled. A0indicatesconversion_bitsaren't modeled, and a1indicates thatconversion_bitsare modeled.This breakdown is only supported by thetotal_postbacks_detailedfield. |
| link_url_asset | The ID of the URL asset involved in impression, click or action. |
| place_page_id | The ID of the place page involved in impression or click.Account-level insights andpage_place_idare not compatible with each other, so they cannot be queried together. |
| platform_position | Where your ad was shown within a platform, for example on Facebook desktop Feed, or Instagram Mobile Feed. |
| product_id | The ID of the product involved in impression, click, or action. |
| publisher_platform | Which platform your ad was shown, for example on Facebook, Instagram, or Audience Network. |
| region | The regions where the people you've reached are located. This is based on information such as a person's hometown, their current city and the geographical location where they tend to be when they visit Facebook. |
| skan_campaign_id | The raw campaign ID received as a part of Skan postback from iOS 15+.Note:This breakdown is only supported by thetotal_postbacks_detailedfield. |
| skan_conversion_id | The assigned Conversion ID (also referred to as Priority ID) of the event and/or event bundle configured in the application’s SKAdNetwork configuration schema. The app events configuration can be viewed and adjusted in Meta Events Manager. You can learn more about configuring your app events for Apple's SKAdNetworkhere.Note:This breakdown is only supported by thetotal_postbacksfield. |
| title_asset | The ID of the title asset involved in impression, click or action. |
| user_segment_key | User segment (ex: new, existing) of Advantage+ Shopping Campaigns (ASC). Existing user is specified by the custom audience in ASC settings. |
| video_asset | The ID of the video asset involved in impression, click or action. |

**Notes**

- Filtering `app_id` and `skan_conversion_id` using the `filtering` field is currently not supported.
- The `dma` breakdown is not available for the `estimated_ad_recall_rate` metric or `video_thruplay_watched_actions` metric.
- The `dma` breakdown employs a sampling methodology to compute unique metrics like reach. In instances where there are a large number of DMA regions with comparatively low volumes, they might not be represented in the sample or could be scaled up to a power of 2. Therefore, it's advisable to query the corresponding impressions as well for enhanced accuracy.
- `frequency_value` is used with `reach` only. For example, how frequently a unique user saw an ad.
- By design, `image_asset` and `video_asset` breakdowns are not available at the ad account level for assets used in [Dynamic Creative](https://developers.facebook.com/docs/marketing-api/asset-feed).
- [Ad actions](https://developers.facebook.com/docs/marketing-api/reference/ads-action-stats/) `video_p25_watched_actions`, `video_p50_watched_actions`, `video_p75_watched_actions`, `video_p95_watched_actions`, and `video_p100_watched_actions` do not support `region` breakdown.
- All Dynamic Creative asset breakdowns only support a limited set of metrics:

| Dynamic Creative Breakdowns | Supported metrics for Dynamic Creative Breakdowns |
| ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| ad_format_assetbody_assetcall_to_action_assetdescription_assetimage_assetlink_url_assettitle_assetvideo_asset | impressionsclicksspendreachactionsaction_values |

The following call groups the results by `age` and `gender`.

cURL

```
curl -G \
 -d "breakdowns=age,gender" \
 -d "fields=impressions" \
 -d "access_token=<ACCESS_TOKEN>" \
 "https://graph.facebook.com/<API_VERSION>/<AD_CAMPAIGN_ID>/insights"
```

Show Response

[#](#)

## Hourly Breakdowns

Hourly stats are now an available breakdown using the following breakdowns:

- `hourly_stats_aggregated_by_advertiser_time_zone`
- `hourly_stats_aggregated_by_audience_time_zone`

See [Combining Breakdowns](#combiningbreakdowns) for limits on number of breakdowns you may request with the hourly breakdown. Hourly breakdowns do not support unique fields, which are any fields prepended with `unique_*`, `reach` or `frequency`. `reach` and `frequency` fields will return 0 when hourly breakdowns are in use.

cURL

```
curl -G \
-d "fields=impressions" \
-d "breakdowns=hourly_stats_aggregated_by_audience_time_zone" \
-d "access_token=<ACCESS_TOKEN>" \
"https://graph.facebook.com/<API_VERSION>/<AD_CAMPAIGN_ID>/insights"
```

Show Response

[#](#)

## Action Breakdown

Group results in the `actions` field. You can use the following breakdowns for `action_breakdowns`:

The following are the possible breakdowns that can be supplied into the `action_breakdowns` field.

- `action_device`
- `conversion_destination`
- `matched_persona_id`
- `matched_persona_name`
- `signal_source_bucket`
- `standard_event_content_type`
- `action_canvas_component_name`
- `action_carousel_card_id`
- `action_carousel_card_name`
- `action_destination`
- `action_reaction`
- `action_target_id`
- `action_type`
- `action_video_sound`
- `action_video_type`
- `is_business_ai_assisted`

If `action_breakdowns` parameter is not specified, `action_type` is implicitly added as the `action_breakdowns`.

[#](#)

## Total Count in `actions`

The total count (sum) of all values returned in group results (`actions`).

This result may not equal `total_actions` since fields returned in `actions` are hierarchical and include detailed actions not counted.

```
total_actions - 33
 page_engagement - 10
 post_engagement - 10
 link_click - 2
 comment - 3
 post_reaction - 3
 like - 2
 mobile_app_install - 12
 app_custom_event - 11
 app_custom_event.fb_mobile_activate_app - 6
 app_custom_event.other - 5
```

In this example, `post_engagement` is a sum of `link_click`, `comment`, `like`, and `post_reaction`, where `post_reaction` is the count of all reactions, including likes. The `total_actions` field represents a sum of top-level actions for an object, such as `page_engagement`, `mobile_app_install`, and `app_custom_event`.

[#](#)

## Combining Breakdowns

Due to storage constraints, only some permutations of breakdowns are available. **Permutations marked with an asterisk (\*) can be joined with `action_type`, `action_target_id` and `action_destination` which is the name for `action_target_id`.**

| Permutation |
| ------------------------------------------------------------------------------------------- |
| action_converted_product_id- Under limited availability for Collaborative Ads. |
| action_type* |
| action_type, action_converted_product_id- Under limited availability for Collaborative Ads. |
| action_target_id* |
| action_device * |
| action_device, impression_device* |
| action_device, publisher_platform* |
| action_device, publisher_platform, impression_device* |
| action_device, publisher_platform, platform_position* |
| action_device, publisher_platform, platform_position, impression_device* |
| action_reaction |
| action_type, action_reaction |
| age* |
| gender* |
| age, gender* |
| app_id, skan_conversion_id |
| country* |
| region* |
| publisher_platform* |
| publisher_platform, impression_device* |
| publisher_platform, platform_position* |
| publisher_platform, platform_position, impression_device* |
| product_id* |
| hourly_stats_aggregated_by_advertiser_time_zone* |
| hourly_stats_aggregated_by_audience_time_zone* |
| action_carousel_card_id / action_carousel_card_name |
| action_carousel_card_id / action_carousel_card_name |
| action_carousel_card_id / action_carousel_card_name, impression_device |
| action_carousel_card_id / action_carousel_card_name, country |
| action_carousel_card_id / action_carousel_card_name, age |
| action_carousel_card_id / action_carousel_card_name, gender |
| action_carousel_card_id / action_carousel_card_name, age, gender |

### Limitations

- `video_*` fields cannot be requested with any hourly stats breakdowns.
- `video_avg_time_watched_actions` field cannot be requested with the region breakdown.
- `action_type` is implicitly added as the `action_breakdowns` when `action_breakdowns` parameter is not specified.

[#](#)

[#](#)

On This Page

[Insights API Breakdowns](#insights-api-breakdowns)

[Limitations](#limitations)

[Unavailable fields](#unavailable-fields)

[Restrictions for Off-Meta Action Metrics](#restrictions-for-off-meta-action-metrics)

[Action Metrics](#action-metrics)

[Generic Breakdowns](#genericbreakdowns)

[Hourly Breakdowns](#hourlybreakdowns)

[Action Breakdown](#actionsbreakdown)

[Total Count in actions](#total-count-in-actions)

[Combining Breakdowns](#combiningbreakdowns)

[Limitations](#combining-limitations)


---

<a id="action-breakdowns"></a>

## Action Breakdowns

> **Source:** [https://developers.facebook.com/docs/marketing-api/insights/action-breakdowns](https://developers.facebook.com/docs/marketing-api/insights/action-breakdowns)

[Marketing API](https://developers.facebook.com/docs/marketing-api)

- [Overview](https://developers.facebook.com/docs/marketing-api/overview)
- [Get Started](https://developers.facebook.com/docs/marketing-api/get-started)
- [Ad Creative](https://developers.facebook.com/docs/marketing-api/creative)
- [Bidding](https://developers.facebook.com/docs/marketing-api/bidding)
- [Ad Rules Engine](https://developers.facebook.com/docs/marketing-api/ad-rules)
- [Audiences](https://developers.facebook.com/docs/marketing-api/audiences)
- [Insights API](https://developers.facebook.com/docs/marketing-api/insights)

 - [Breakdowns](https://developers.facebook.com/docs/marketing-api/insights/breakdowns)
 - [Limits & Best Practices](https://developers.facebook.com/docs/marketing-api/insights/best-practices)
 - [Tracking and Conversion Specs](https://developers.facebook.com/docs/marketing-api/tracking-specs)
 - [Marketing Mix Modeling](https://developers.facebook.com/docs/marketing-api/insights/marketing-mix-modeling)
 - [Conversion Lift Measurement](https://developers.facebook.com/docs/marketing-api/guides/lift-studies)
 - [Split Testing](https://developers.facebook.com/docs/marketing-api/guides/split-testing)
 - [Ad Volume](https://developers.facebook.com/docs/marketing-api/insights-api/ads-volume)
 - [App Events API](https://developers.facebook.com/docs/marketing-api/app-event-api)
 - [Error Codes](https://developers.facebook.com/docs/marketing-api/insights/error-codes)
- [Brand Safety and Suitability](https://developers.facebook.com/docs/marketing-api/brand-safety-and-suitability)
- [Best Practices](https://developers.facebook.com/docs/marketing-api/best-practices)
- [Troubleshooting](https://developers.facebook.com/docs/marketing-api/troubleshooting)
- [API Reference](https://developers.facebook.com/docs/marketing-api/reference)
- [Changelog](https://developers.facebook.com/docs/marketing-api/marketing-api-changelog)

On This Page

[Insights API Breakdowns](#insights-api-breakdowns)

[Limitations](#limitations)

[Unavailable fields](#unavailable-fields)

[Restrictions for Off-Meta Action Metrics](#restrictions-for-off-meta-action-metrics)

[Action Metrics](#action-metrics)

[Generic Breakdowns](#genericbreakdowns)

[Hourly Breakdowns](#hourlybreakdowns)

[Action Breakdown](#actionsbreakdown)

[Total Count in actions](#total-count-in-actions)

[Combining Breakdowns](#combiningbreakdowns)

[Limitations](#combining-limitations)

# Insights API Breakdowns

You can group the Insights API results into different sets using breakdowns.

The Insights API can return several metrics that are estimated, in development, or both. Insights breakdown values are estimated. For more information, see [Insights API, Estimated and Deprecated Metrics](https://developers.facebook.com/docs/marketing-api/insights/estimated-in-development).

## Limitations

### Unavailable fields

The following fields cannot be requested when specifying a breakdown:

- `app_store_clicks`
- `newsfeed_avg_position`
- `newsfeed_clicks`
- `relevance_score`
- `newsfeed_impressions`

### Restrictions for Off-Meta Action Metrics

The following breakdowns will no longer be available for off-Meta action metrics.

#### Type 1

- `region`
- `dma`
- `hourly_stats_aggregated_by_audience_time_zone`
- `hourly_stats_aggregated_by_advertiser_time_zone`

#### Type 2

- `action_device`
- `action_destination`
- `action_target_id`
- `product_id`
- `action_carousel_card_id/action_carousel_card_name`
- `action_canvas_component_name`

**Rules related to queries containing above breakdowns:**

- **Type 1** — The Insights API will not return unsupported offsite metrics (e.g., actions metric with Type 1 breakdowns).
- **Type 2** — Offsite web metrics will continue to be returned from the API, however will not contain the breakdown value.
 The mobile metrics will not be returned anymore when queried with these breakdowns.

**Note:** The breakdowns listed above will still be supported for on-Meta metrics such as impressions, link clicks, etc. The changes will also not impact historical data prior to April 27, 2021; breakdowns for historical data will continue to be available.

### Action Metrics

Metrics will not be available under the following scenarios:

- When there is an attempted aggregation across multiple attribution settings
- When requested with impacted breakdowns (this restriction only applies for off-Meta & action types).

**Note:** Metrics will be available if querying with `action_attribution_windows=1d_click,7d_click,1d_view,incrementality` (not including the default window).

[#](#)

## Generic Breakdowns

The following breakdowns are available.

| Breakdown | Description |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| action_device | The device on which the conversion event you're tracking occurred. For example, \"Desktop\" if someone converted on a desktop computer. |
| action_canvas_component_name | Name of a component within a Canvas ad. |
| action_carousel_card_id | The ID of the specific carousel card that people engaged with when they saw your ad. |
| action_carousel_card_name | The specific carousel card that people engaged with when they saw your ad. The cards are identified by their headlines. |
| action_destination | The destination where people go after clicking on your ad. This could be your Facebook Page, an external URL for your conversion pixel or an app configured with the software development kit (SDK). |
| action_reaction | The number of reactions on your ads or boosted posts. The reactions button on an ad allows people to share different reactions on its content: Like, Love, Haha, Wow, Sad or Angry. |
| action_target_id | The ID of destination where people go after clicking on your ad. This could be your Facebook Page, an external URL for your conversion pixel or an app configured with the software development kit (SDK). |
| action_type | The kind of actions taken on your ad, Page, app or event after your ad was served to someone, even if they didn't click on it. Action types include Page likes, app installs, conversions, event responses, and more. |
| action_video_sound | The sound status (on/off) when someone plays your video ad. |
| action_video_type | Video metrics breakdown. |
| ad_format_asset | The ID of the ad format asset involved in impression, click, or action |
| age | The age range of the people you've reached. |
| app_id | The ID of the application associated with the ad account or campaign requested. The application information, including its ID, is viewable in theApp Dashboard.This breakdown is only supported by thetotal_postbacksfield. |
| body_asset | The ID of the body asset involved in impression, click, or action. |
| call_to_action_asset | The ID of the call to action asset involved in impression, click, or action. |
| country | The country where the people you've reached are located. This is based on information, such as a person's hometown, their current city, and the geographical location where they tend to be when they visit Meta. |
| description_asset | The ID of the description asset involved in impression, click, or action. |
| device_platform | The type of device, mobile or desktop, used by people when they viewed or clicked on an ad, as shown in ads reporting. |
| dma | The Designated Market Area (DMA) regions are the 210 geographic areas in the United States in which local television viewing is measured by The Nielsen Company. |
| frequency_value | The number of times an ad in your Reach and Frequency campaign was served to each Accounts Center account. |
| gender | Gender of people you've reached. People who don't list their gender are shown as 'not specified'. |
| hourly_stats_aggregated_by_advertiser_time_zone | Hourly breakdown aggregated by the time ads were delivered in the advertiser's time zone. For example, if your ads are scheduled to run from 9 AM to 11 AM, but they reach audiences in multiple time zones, they may deliver from 9 AM to 1 PM in the advertiser's time zone. Stats will be aggregated into four groups 9 AM - 10 AM, 10 AM - 11 AM, 11 AM - 12 PM, and 12 PM - 1 PM. |
| hourly_stats_aggregated_by_audience_time_zone | Hourly breakdown aggregated by the time ads were delivered in the audiences' time zone. For example, if your ads are scheduled to run from 9:00 am to 11:00 am, but they reach audiences in multiple time zones, they may deliver from 9:00 am to 1:00 pm in the advertiser's time zone. Stats are aggregated into 2 groups: 9:00 am to 10:00 am and 10:00 am to 11:00 am. |
| image_asset | The ID of the image asset involved in impression, click, or action. |
| impression_device | The device where your last ad was served to someone on Meta. For example \"iPhone\" if someone viewed your ad on an iPhone. |
| is_conversion_id_modeled | A boolean flag that indicates whether theconversion_bitsare modeled. A0indicatesconversion_bitsaren't modeled, and a1indicates thatconversion_bitsare modeled.This breakdown is only supported by thetotal_postbacks_detailedfield. |
| link_url_asset | The ID of the URL asset involved in impression, click or action. |
| place_page_id | The ID of the place page involved in impression or click.Account-level insights andpage_place_idare not compatible with each other, so they cannot be queried together. |
| platform_position | Where your ad was shown within a platform, for example on Facebook desktop Feed, or Instagram Mobile Feed. |
| product_id | The ID of the product involved in impression, click, or action. |
| publisher_platform | Which platform your ad was shown, for example on Facebook, Instagram, or Audience Network. |
| region | The regions where the people you've reached are located. This is based on information such as a person's hometown, their current city and the geographical location where they tend to be when they visit Facebook. |
| skan_campaign_id | The raw campaign ID received as a part of Skan postback from iOS 15+.Note:This breakdown is only supported by thetotal_postbacks_detailedfield. |
| skan_conversion_id | The assigned Conversion ID (also referred to as Priority ID) of the event and/or event bundle configured in the application’s SKAdNetwork configuration schema. The app events configuration can be viewed and adjusted in Meta Events Manager. You can learn more about configuring your app events for Apple's SKAdNetworkhere.Note:This breakdown is only supported by thetotal_postbacksfield. |
| title_asset | The ID of the title asset involved in impression, click or action. |
| user_segment_key | User segment (ex: new, existing) of Advantage+ Shopping Campaigns (ASC). Existing user is specified by the custom audience in ASC settings. |
| video_asset | The ID of the video asset involved in impression, click or action. |

**Notes**

- Filtering `app_id` and `skan_conversion_id` using the `filtering` field is currently not supported.
- The `dma` breakdown is not available for the `estimated_ad_recall_rate` metric or `video_thruplay_watched_actions` metric.
- The `dma` breakdown employs a sampling methodology to compute unique metrics like reach. In instances where there are a large number of DMA regions with comparatively low volumes, they might not be represented in the sample or could be scaled up to a power of 2. Therefore, it's advisable to query the corresponding impressions as well for enhanced accuracy.
- `frequency_value` is used with `reach` only. For example, how frequently a unique user saw an ad.
- By design, `image_asset` and `video_asset` breakdowns are not available at the ad account level for assets used in [Dynamic Creative](https://developers.facebook.com/docs/marketing-api/asset-feed).
- [Ad actions](https://developers.facebook.com/docs/marketing-api/reference/ads-action-stats/) `video_p25_watched_actions`, `video_p50_watched_actions`, `video_p75_watched_actions`, `video_p95_watched_actions`, and `video_p100_watched_actions` do not support `region` breakdown.
- All Dynamic Creative asset breakdowns only support a limited set of metrics:

| Dynamic Creative Breakdowns | Supported metrics for Dynamic Creative Breakdowns |
| ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| ad_format_assetbody_assetcall_to_action_assetdescription_assetimage_assetlink_url_assettitle_assetvideo_asset | impressionsclicksspendreachactionsaction_values |

The following call groups the results by `age` and `gender`.

cURL

```
curl -G \
 -d "breakdowns=age,gender" \
 -d "fields=impressions" \
 -d "access_token=<ACCESS_TOKEN>" \
 "https://graph.facebook.com/<API_VERSION>/<AD_CAMPAIGN_ID>/insights"
```

Show Response

[#](#)

## Hourly Breakdowns

Hourly stats are now an available breakdown using the following breakdowns:

- `hourly_stats_aggregated_by_advertiser_time_zone`
- `hourly_stats_aggregated_by_audience_time_zone`

See [Combining Breakdowns](#combiningbreakdowns) for limits on number of breakdowns you may request with the hourly breakdown. Hourly breakdowns do not support unique fields, which are any fields prepended with `unique_*`, `reach` or `frequency`. `reach` and `frequency` fields will return 0 when hourly breakdowns are in use.

cURL

```
curl -G \
-d "fields=impressions" \
-d "breakdowns=hourly_stats_aggregated_by_audience_time_zone" \
-d "access_token=<ACCESS_TOKEN>" \
"https://graph.facebook.com/<API_VERSION>/<AD_CAMPAIGN_ID>/insights"
```

Show Response

[#](#)

## Action Breakdown

Group results in the `actions` field. You can use the following breakdowns for `action_breakdowns`:

The following are the possible breakdowns that can be supplied into the `action_breakdowns` field.

- `action_device`
- `conversion_destination`
- `matched_persona_id`
- `matched_persona_name`
- `signal_source_bucket`
- `standard_event_content_type`
- `action_canvas_component_name`
- `action_carousel_card_id`
- `action_carousel_card_name`
- `action_destination`
- `action_reaction`
- `action_target_id`
- `action_type`
- `action_video_sound`
- `action_video_type`
- `is_business_ai_assisted`

If `action_breakdowns` parameter is not specified, `action_type` is implicitly added as the `action_breakdowns`.

[#](#)

## Total Count in `actions`

The total count (sum) of all values returned in group results (`actions`).

This result may not equal `total_actions` since fields returned in `actions` are hierarchical and include detailed actions not counted.

```
total_actions - 33
 page_engagement - 10
 post_engagement - 10
 link_click - 2
 comment - 3
 post_reaction - 3
 like - 2
 mobile_app_install - 12
 app_custom_event - 11
 app_custom_event.fb_mobile_activate_app - 6
 app_custom_event.other - 5
```

In this example, `post_engagement` is a sum of `link_click`, `comment`, `like`, and `post_reaction`, where `post_reaction` is the count of all reactions, including likes. The `total_actions` field represents a sum of top-level actions for an object, such as `page_engagement`, `mobile_app_install`, and `app_custom_event`.

[#](#)

## Combining Breakdowns

Due to storage constraints, only some permutations of breakdowns are available. **Permutations marked with an asterisk (\*) can be joined with `action_type`, `action_target_id` and `action_destination` which is the name for `action_target_id`.**

| Permutation |
| ------------------------------------------------------------------------------------------- |
| action_converted_product_id- Under limited availability for Collaborative Ads. |
| action_type* |
| action_type, action_converted_product_id- Under limited availability for Collaborative Ads. |
| action_target_id* |
| action_device * |
| action_device, impression_device* |
| action_device, publisher_platform* |
| action_device, publisher_platform, impression_device* |
| action_device, publisher_platform, platform_position* |
| action_device, publisher_platform, platform_position, impression_device* |
| action_reaction |
| action_type, action_reaction |
| age* |
| gender* |
| age, gender* |
| app_id, skan_conversion_id |
| country* |
| region* |
| publisher_platform* |
| publisher_platform, impression_device* |
| publisher_platform, platform_position* |
| publisher_platform, platform_position, impression_device* |
| product_id* |
| hourly_stats_aggregated_by_advertiser_time_zone* |
| hourly_stats_aggregated_by_audience_time_zone* |
| action_carousel_card_id / action_carousel_card_name |
| action_carousel_card_id / action_carousel_card_name |
| action_carousel_card_id / action_carousel_card_name, impression_device |
| action_carousel_card_id / action_carousel_card_name, country |
| action_carousel_card_id / action_carousel_card_name, age |
| action_carousel_card_id / action_carousel_card_name, gender |
| action_carousel_card_id / action_carousel_card_name, age, gender |

### Limitations

- `video_*` fields cannot be requested with any hourly stats breakdowns.
- `video_avg_time_watched_actions` field cannot be requested with the region breakdown.
- `action_type` is implicitly added as the `action_breakdowns` when `action_breakdowns` parameter is not specified.

[#](#)

[#](#)

On This Page

[Insights API Breakdowns](#insights-api-breakdowns)

[Limitations](#limitations)

[Unavailable fields](#unavailable-fields)

[Restrictions for Off-Meta Action Metrics](#restrictions-for-off-meta-action-metrics)

[Action Metrics](#action-metrics)

[Generic Breakdowns](#genericbreakdowns)

[Hourly Breakdowns](#hourlybreakdowns)

[Action Breakdown](#actionsbreakdown)

[Total Count in actions](#total-count-in-actions)

[Combining Breakdowns](#combiningbreakdowns)

[Limitations](#combining-limitations)


---

<a id="limits-and-best-practices"></a>

## Limits & Best Practices

> **Source:** [https://developers.facebook.com/docs/marketing-api/insights/best-practices](https://developers.facebook.com/docs/marketing-api/insights/best-practices)

[Marketing API](https://developers.facebook.com/docs/marketing-api)

- [Overview](https://developers.facebook.com/docs/marketing-api/overview)
- [Get Started](https://developers.facebook.com/docs/marketing-api/get-started)
- [Ad Creative](https://developers.facebook.com/docs/marketing-api/creative)
- [Bidding](https://developers.facebook.com/docs/marketing-api/bidding)
- [Ad Rules Engine](https://developers.facebook.com/docs/marketing-api/ad-rules)
- [Audiences](https://developers.facebook.com/docs/marketing-api/audiences)
- [Insights API](https://developers.facebook.com/docs/marketing-api/insights)

 - [Breakdowns](https://developers.facebook.com/docs/marketing-api/insights/breakdowns)
 - [Limits & Best Practices](https://developers.facebook.com/docs/marketing-api/insights/best-practices)
 - [Tracking and Conversion Specs](https://developers.facebook.com/docs/marketing-api/tracking-specs)
 - [Marketing Mix Modeling](https://developers.facebook.com/docs/marketing-api/insights/marketing-mix-modeling)
 - [Conversion Lift Measurement](https://developers.facebook.com/docs/marketing-api/guides/lift-studies)
 - [Split Testing](https://developers.facebook.com/docs/marketing-api/guides/split-testing)
 - [Ad Volume](https://developers.facebook.com/docs/marketing-api/insights-api/ads-volume)
 - [App Events API](https://developers.facebook.com/docs/marketing-api/app-event-api)
 - [Error Codes](https://developers.facebook.com/docs/marketing-api/insights/error-codes)
- [Brand Safety and Suitability](https://developers.facebook.com/docs/marketing-api/brand-safety-and-suitability)
- [Best Practices](https://developers.facebook.com/docs/marketing-api/best-practices)
- [Troubleshooting](https://developers.facebook.com/docs/marketing-api/troubleshooting)
- [API Reference](https://developers.facebook.com/docs/marketing-api/reference)
- [Changelog](https://developers.facebook.com/docs/marketing-api/marketing-api-changelog)

On This Page

[Limits and Best Practices](#limits-and-best-practices)

[Timeouts](#timeouts)

[Recommendations](#recommendations)

[Data Per Call Limits](#datapercall)

[Best Practices, Data Per Call Limits](#best-practices--data-per-call-limits)

[Insights Call Load Limits](#insightscallload)

[Global Rate Limits](#global-rate-limits)

[Rate Limits Best Practices](#rate-limits-best-practices)

[Insights API Asynchronous Jobs](#asynchronous)

[Async Job Status](#async-job-status)

[Export Reports](#export-reports)

[Discrepancy with Ads Manager](#discrepancy-with-ads-manager)

# Limits and Best Practices

Beginning June 10, 2025, to improve overall API performance, `reach` will no longer be returned for standard queries that apply `breakdowns` and use `start_date`s more than 13 months old. (Responses to such requests will omit `reach` and related fields, such as `frequency` and `cpp`.)

To apply `breakdowns` and still retrieve >13-month-old `reach` values, you can use asynchronous jobs to make up to 10 requests per Ad Account per day. Check the `x-Fb-Ads-Insights-Reach-Throttle` header to monitor how close you are to that rate-limit, and note that once the rate-limit is breached, requests will omit `reach` and related fields.

When the rate limit threshold for reach-related breakdowns is exceeded, the following error message will be returned:

```
 Reach-related metric breakdowns are unavailable due to rate limit threshold.
```

Facebook Insights API provides performance data from Facebook marketing campaigns. To protect system performance and stability, we have protective measures to equally distribute system resources among applications. All policies we describe below are subject to change.

## Timeouts

The most common issue causing failure for Ads Insights API calls is too many requests and time outs.

- `/GET` or synchronous requests can return out-of-memory or timeout errors.
- `/POST` or asynchronous requests can return timeout errors. For asynchronous requests, it can take up to an hour to complete a request including retry attempts. For example, if you make a query that tries to fetch a large volume of data for many ad level objects.

### Recommendations

- There is no explicit limit for when a query will fail. When it times out, try to break down the query into smaller queries by using filters like date range.
- Unique metrics are time consuming to compute. Try to query unique metrics in a separate call to improve performance of non-unique metrics.

[#](#)

## Data Per Call Limits

We use data-per-call limits to prevent a query from retrieving too much data beyond what the system can handle. There are 2 types of data limits:

1. By number of rows in response, and
2. By number of data points required to compute the total, such as summary row.

These limits apply to both sync and async `/insights` calls, and we return an error:

```
error_code = 100, CodeException (error subcode: 1487534)
```

### Best Practices, Data Per Call Limits

- Limit your query by limiting the date range or number of ad ids. You can also limit your query to metrics that are necessary, or break it down into multiple queries with each requesting a subset of metrics.
- Avoid account-level queries that include high cardinality breakdowns such as `action_target_id` or `product_id`, and wider date ranges like lifetime.
- Use `/insights` edge directly with lower level ad objects to retrieve granular data for that level. For example, first use the account-level query to fetch the list of lower-level object ids with `level` and `filtering` parameters. In this example, we fetch all campaigns that recorded some impressions:

```
curl -G \
-d 'access_token=<ACCESS_TOKEN>' \
-d 'level=campaign' \
-d 'filtering=[{field:"ad.impressions",operator:"GREATER_THAN",value:0}]' \
'https://graph.facebook.com/v2.7/act_<ACCOUNT_ID>/insights'
```

- We can then use `/<campaign_id>/insights` with each returned value to query and [batch the insights requests](https://developers.facebook.com/docs/marketing-api/batch-requests/v2.6#adinsights) for these campaigns in a single call:

```
v24.0
```

- Use `filtering` parameter only to retrieve insights for ad objects with data. The field value specified in `filtering` uses DOT notation to denote the fields under the object. Please note that filtering with `STARTS_WITH` and `CONTAIN` does not change the summary data. In this case, use the `IN` operator. See example of a `filtering` request:

```
v24.0
```

- Use `date_preset` if possible. Custom date ranges are less efficient to run in our system.
- Use [batch requests](https://developers.facebook.com/docs/marketing-api/batch-requests/v2.6) for multiple sync calls and async to query for large volume of data to avoid timeouts.
- Try sync calls first and then use async calls in cases where sync calls timeout
- Insights refresh every 15 minutes and do not change after 28 days of being reported

[#](#)

## Insights Call Load Limits

Ninety days from the release of v3.3 and effective for all public versions, we change the ad account level rate limit to better reflect the volume of API calls needed. We compute the rate limit quota on your Marketing API access tier and the business owning your app. see [Access and Authentication](https://developers.facebook.com/docs/marketing-api/access). This change applies to all Ads Insights API endpoints: `GET {adaccount_ID}/insights`, `GET {campaign_ID}/insights`, `GET {adset_ID}/insights`, `GET {ad_ID}/insights`, `POST {adaccount_ID}/insights`, `POST {campaign_ID}/insights`, `POST {adset_ID}/insights`, `POST {ad_ID}/insights`.

We use load limits for optimal reporting experience. We measure API calls for their rate as well as the resources they require. We allow a fixed load limit per application per second. When you exceed that limit, your requests fail.

Check the `x-fb-ads-insights-throttle` HTTP header in every API response to know how close your app is to its limit as well as to estimate how heavy a particular query may be. Insights calls are also subject to the default ad account limits shown in the `x-ad-account-usage` HTTP header. More details can be found here [Marketing API, Best Practices](https://developers.facebook.com/docs/marketing-api/best-practices/)

Once an app reaches its limit, the call gets an error response with `error_code = 4, CodedException`. You should stay well below your limit. If your app reaches its allowed limits, only a certain percentage of requests go through, depending on the query, and the rate.

We apply rate limiting to each app sending synchronous and asynchronous `/insights` calls combined. The two main parameters limits are counted against are by application, and by ad account.

Here's an example of the HTTP header with an application's accrued score as a percentage of the limits:

```
X-FB-Ads-Insights-Throttle: { "app_id_util_pct": 100, "acc_id_util_pct": 10, "ads_api_access_tier": "standard_access" }
```

The header "x-fb-ads-insights-throttle" is a JSON value containing these info:

- `app_id_util_pct` — The percentage of allocated capacity for the associated app\_id has consumed.
- `acc_id_util_pct` — The percentage of allocated capacity for the associated ad account\_id has consumed.
- `ads_api_access_tier` — Tiers allows your app to access the Marketing API. `standard_access` enables lower rate limiting.

### Global Rate Limits

During periods of elevated global load to the `/insights` endpoint, the system can throttle requests to protect the backend. This can occur in rare cases when too many queries of high complexity (large time ranges, complex metrics, and/or high number of ad object IDs) are coming at the same time. This will manifest in an error that looks like this:

```
error_code = 4, CodeException (error subcode: 1504022), error_title: Too many API requests
```

During these periods, it is advised to reduce calls, wait a short period, and query again.

### Rate Limits Best Practices

- Sending several queries at once are more likely to trigger our rate limiting. Try to spread your `/insights` queries by pacing them with wait time in your job.
- Use the rate information in the HTTP response header to moderate your calls. Add a back-off mechanism to slow down or pause your `/insights` queries when you come close to hitting 100% utility for your application, or for your ad account.
- We report ad insights data in the ad account's timezone. To retrieve insights data for the associated ad account daily, consider the time of day using the account timezone. This helps pace queries throughout the day.
- Check the `ads_api_access_tier` that allows you to access the Marketing API. By default, apps are in the `development_access` tier and `standard_access` enables lower rate limiting. To get a higher rate limit and get to the standard tier, you can apply for the "Advanced Access" to the [Ads Management Standard Access](https://developers.facebook.com/docs/marketing-api/overview/authorization) feature.

[#](#)

## Insights API Asynchronous Jobs

Fetch stats on many objects and apply filtering and sorting; we made the asynchronous workflow simpler:

#### 1. Send a `POST` request to `<AD_OBJECT>/insights` endpoint, which responds with the `id` of an [Ad Report Run](https://developers.facebook.com/docs/marketing-api/reference/ad-report-run).

```
{
 "report_run_id": 6023920149050,
}
```

Do not store the `report_run_id` for long term use, it expires after 30 days.

#### 2. Ad Report Runs contain information about this asynchronous job, such as `async_status`. Poll this field until `async_status` is `Job Completed` and `async_percent_completion` is `100`.

```
{
 "id": "6044775548468",
 "account_id": "1010035716096012",
 "time_ref": 1459788928,
 "time_completed": 1459788990,
 "async_status": "Job Completed",
 "async_percent_completion": 100
}
```

**Note:** Beginning with Marketing API v25.0, if the report fails, the corresponding error code, error message, error subcode, error user title, and error user message fields will be returned.

#### 3. Then you can query `<AD_REPORT_RUN_ID>/insights` edge to fetch the final result.

```
{
 "data": [
 {
 "impressions": "9708",
 "date_start": "2009-03-28",
 "date_stop": "2016-04-04"
 },
 {
 "impressions": "18841",
 "date_start": "2009-03-28",
 "date_stop": "2016-04-04"
 }
 ],
 "paging": {
 "cursors": {
 "before": "MAZDZD",
 "after": "MQZDZD"
 }
 }
}
```

This job gets all stats for the account and returns an asynchronous job ID:

```
v24.0
```

### Async Job Status

| Status | Description |
| --------------- | -------------------------------------------------------------------- |
| Job Not Started | Job has not started yet. |
| Job Started | Job has been started, but is not yet running. |
| Job Running | Job has started running. |
| Job Completed | Job has successfully completed. |
| Job Failed | Job has failed. Review your query and try again. |
| Job Skipped | Job has expired and skipped. Please resubmit your job and try again. |

[#](#)

## Export Reports

We provide a convenience endpoint for exporting `<AD_REPORT_RUN_ID>` to a localized human-readable format.

Note: this endpoint is not part of our versioned Graph API and therefore does not conform to its breaking-change policy. Scripts and programs should not rely on the format of the result as it may change unexpectedly.

```
 curl -G \
 -d 'report_run_id=<AD_REPORT_RUN_ID>' \
 -d 'name=myreport' \
 -d 'format=xls' \
'https://www.facebook.com/ads/ads_insights/export_report/'

```

| Name | Description |
| -------------------- | ------------------------------------------------------------------------------------------- |
| namestring | Name of downloaded file |
| formatenum{csv,xls} | Format of file |
| report_run_idinteger | ID of report to run |
| access_tokenstring | Permissions granted by the logged-in user. Provide this to export reports for another user. |

[#](#)

## Discrepancy with Ads Manager

Beginning June 10, 2025, to reduce discrepancies with Meta Ads Manager, the `use_unified_attribution_setting` and `action_report_time` parameters will be disregarded and API responses will mimic Ads Manager settings:

- Attributed `value`s will be based on ad set level attribution settings (similar to `use_unified_attribution_setting=true`), and inline/on-ad actions will be included in `1d_click` or `1d_view` attribution window data. After this change, standalone `inline` attribution window data will no longer be returned.
- Actions will be reported using `action_report_time=mixed`: on-Meta actions (e.g., Link Clicks) will use impression-based reporting time; whereas off-Meta actions (e.g., Web Purchases) will leverage conversion-based reporting time.

The default behavior of the API is different from the default behavior of Ads Manager. If you would like to observe the same behavior as in Ads Manager, set the `use_unified_attribution_setting` field to `true`.

[#](#)

[#](#)

On This Page

[Limits and Best Practices](#limits-and-best-practices)

[Timeouts](#timeouts)

[Recommendations](#recommendations)

[Data Per Call Limits](#datapercall)

[Best Practices, Data Per Call Limits](#best-practices--data-per-call-limits)

[Insights Call Load Limits](#insightscallload)

[Global Rate Limits](#global-rate-limits)

[Rate Limits Best Practices](#rate-limits-best-practices)

[Insights API Asynchronous Jobs](#asynchronous)

[Async Job Status](#async-job-status)

[Export Reports](#export-reports)

[Discrepancy with Ads Manager](#discrepancy-with-ads-manager)


---

<a id="tracking-and-conversion-specs"></a>

## Tracking and Conversion Specs

> **Source:** [https://developers.facebook.com/docs/marketing-api/tracking-specs](https://developers.facebook.com/docs/marketing-api/tracking-specs)

[Marketing API](https://developers.facebook.com/docs/marketing-api)

- [Overview](https://developers.facebook.com/docs/marketing-api/overview)
- [Get Started](https://developers.facebook.com/docs/marketing-api/get-started)
- [Ad Creative](https://developers.facebook.com/docs/marketing-api/creative)
- [Bidding](https://developers.facebook.com/docs/marketing-api/bidding)
- [Ad Rules Engine](https://developers.facebook.com/docs/marketing-api/ad-rules)
- [Audiences](https://developers.facebook.com/docs/marketing-api/audiences)
- [Insights API](https://developers.facebook.com/docs/marketing-api/insights)

 - [Breakdowns](https://developers.facebook.com/docs/marketing-api/insights/breakdowns)
 - [Limits & Best Practices](https://developers.facebook.com/docs/marketing-api/insights/best-practices)
 - [Tracking and Conversion Specs](https://developers.facebook.com/docs/marketing-api/tracking-specs)
 - [Marketing Mix Modeling](https://developers.facebook.com/docs/marketing-api/insights/marketing-mix-modeling)
 - [Conversion Lift Measurement](https://developers.facebook.com/docs/marketing-api/guides/lift-studies)
 - [Split Testing](https://developers.facebook.com/docs/marketing-api/guides/split-testing)
 - [Ad Volume](https://developers.facebook.com/docs/marketing-api/insights-api/ads-volume)
 - [App Events API](https://developers.facebook.com/docs/marketing-api/app-event-api)
 - [Error Codes](https://developers.facebook.com/docs/marketing-api/insights/error-codes)
- [Brand Safety and Suitability](https://developers.facebook.com/docs/marketing-api/brand-safety-and-suitability)
- [Best Practices](https://developers.facebook.com/docs/marketing-api/best-practices)
- [Troubleshooting](https://developers.facebook.com/docs/marketing-api/troubleshooting)
- [API Reference](https://developers.facebook.com/docs/marketing-api/reference)
- [Changelog](https://developers.facebook.com/docs/marketing-api/marketing-api-changelog)

On This Page

[Tracking and Conversion Specs](#tracking-and-conversion-specs)

[Set Tracking Specs](#create)

[Default Tracking Specs](#default)

[Meta Specs](#meta)

[Custom Tracking Specs](#custom)

[Examples](#examples)

[Pixel Tracking](#tracking)

[Using Conversion Specs](#examples-2)

# Tracking and Conversion Specs

`Tracking Specs` are used primarily for monitoring and reporting purposes. They define what user actions should be tracked after they view or click on an ad. These specs help advertisers understand how users interact with the ad content and whether it leads to offsite conversions, app installs, or other key actions. Tracking specs do not directly influence the optimization of ad delivery but are essential for gathering data on user engagement.

`Conversion specs` are used to define the conditions under which a conversion (a desired action by the user) is counted. These specs are crucial for attributing conversions to specific ads and for optimizing ad performance. Conversion specs are used in the optimization process of ad delivery, where the system predicts and improves conversion rates. `Conversion_specs` has been **read-only** since v2.4. The value is derived from `optimization_goal` from [ad set](https://developers.facebook.com/docs/marketing-api/reference/ad-campaign).

## Set Tracking Specs

Use with any bid type and [creative](https://developers.facebook.com/docs/reference/ads-api/creative-specs/) combination. To specify tracking specs, you need an additional field in an [ad](https://developers.facebook.com/docs/reference/ads-api/adgroup/), named `tracking_specs`. The `tracking_specs` field takes arguments identical to [action spec](https://developers.facebook.com/docs/marketing-api/reference/conversion-action-query/). To create an ad, see [ad creation](https://developers.facebook.com/docs/reference/ads-api/adgroup/).

[#](#)

## Default Tracking Specs

There will be a set of default tracking specs for certain objective, bid\_type and creative combinations. If you set any additional new tracking specs, the default tracking specs are still available and won't be overwritten. Except for `APP_INSTALLS` or `OUTCOME_ENGAGEMENT` objectives, **the default tracking specs will be overwritten**. If you want to have the defaults you must add them to your custom specs.

You can use both string or array notation in the spec such as `'APPLICATION_ID'` or `['APPLICATION_ID']`.

- CPM refers to `billing_event=IMPRESSIONS`, `optimization_goal=IMPRESSIONS`
- CPC refers to `billing_event=CLICKS`, `optimization_goal=CLICKS`
- oCPM refers to `billing_event=IMPRESSIONS`, `optimization_goal` set to an action
- CPA refers to both `billing_event` and `optimization_goal` set to an action

| Objective | Creative, Bid type | Tracking Spec | Description |
| ------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CANVAS_APP_ENGAGEMENT | Canvas app engagement ads withoptimization_goal= APP_INSTALLS | [{'action.type':'app_engagement','application':'APPLICATION_ID'}, {'action.type':'post_engagement','post':'POST_ID', 'page':'PAGE_ID'}] | See app_engagement and post_engagementmeta specs |
| CANVAS_APP_INSTALLS | Canvas app install ads with optimizationnotset tooptimization_goal= APP_INSTALLS | [{'action.type':'app_engagement','application':'APPLICATION_ID'}, {'action.type':'post_engagement','post':'POST_ID', 'page':'PAGE_ID'}] | See app_engagement and post_engagementmeta specs |
| CONVERSIONS | Page post link and photo ads withpromoted_objectset to a pixel ID andoptimization_goal= OFFSITE_CONVERSIONS | {'action.type':'post_engagement','post':'POST_ID', 'page':'PAGE_ID'},{'action.type':'like','page':PAGE_ID} | Post Engagement, Page Like specs. Number of link clicks on the specific page post if there is only one link, number of engagements on the post, and number of times users generate stories or engage with a page |
| CONVERSIONS | Page post link and photo ads with optimizationnotset tooptimization_goal= OFFSITE_CONVERSIONS | {'action.type':'offsite_conversion','fb_pixel':'FACEBOOK_PIXEL_ID'}, {'action.type':{'action.type':'post_engagement','post':'POST_ID', 'page':'PAGE_ID'},{'action.type':'like','page':PAGE_ID} | Conversions, Post Engagement, Page Like specs. Number of link clicks on the specific page post if there is only one link, number of engagements on the post, and number of times users generate stories or engage with a page |
| CONVERSIONS | Domain ads withpromoted_objectset to a pixel ID andoptimization_goal= OFFSITE_CONVERSIONS | {'action.type':'link_click','object':'PAGE_ID'}, {'action.type':'like','page':PAGE_ID} | Page Likes, Link Clicks specs. Number of link clicks on the specific page post if there is only one link, number of engagements on the post, and number of times users generate stories or engage with a page. |
| CONVERSIONS | Domain ads with optimizationnotset tooptimization_goal= OFFSITE_CONVERSIONS | {'action.type':'offsite_conversion','fb_pixel':'FACEBOOK_PIXEL_ID'}, {'action.type':'link_click','object':'PAGE_ID'}, {'action.type':'like','page':PAGE_ID} | Conversion, Page Likes, Link Clicks specs. Number of link clicks on the specific page post if there is only one link, number of engagements on the post, and number of times users generate stories or engage with a page. |
| EVENT_RESPONSES | Event ads with optimizationnotset tooptimization_goal= EVENT_RESPONSES | [{'action.type':'rsvp' ,'response':'yes', 'event':'EVENT_ID'},{'action.type':'rsvp' ,'response':'maybe', 'event':'EVENT_ID'},[{'action.type':'rsvp' ,'response':'no', 'event':'EVENT_ID'}] | Number of RSVPs (yes, maybe, no) to an event. |
| EVENT_RESPONSES | Event ads withoptimization_goal= EVENT_RESPONSES | empty (conversion spec will cover the tracked actions) | Number of RSVPs (yes, maybe, no) to an event. |
| LINK_CLICKS | Page post link and photo ads with any bid option | {'action.type':'post_engagement','post':'POST_ID', 'page':'PAGE_ID'} | Post Engagement.Number of times an offsite url link, link with particular url domain, offsite link on a page, offsite link on a post was clicked. |
| LINK_CLICKS | Domain ads withoptimization_goal= LINK_CLICKS | {'action.type':'like','page':PAGE_ID}] | Page likes.Number of times an offsite url link, link with particular url domain, offsite link on a page, offsite link on a post was clicked. |
| LINK_CLICKS | Domain ads with optimizationnotset tooptimization_goal= LINK_CLICKS | {'action.type':'link_click','object':'PAGE_ID'}, {'action.type':'like','page':PAGE_ID} | Website Click, Page Likes.Number of times an offsite url link, link with particular url domain, offsite link on a page, offsite link on a post was clicked. |
| MOBILE_APP_ENGAGEMENT | Mobile app engagement ads with any bid option | {'action.type':'post_engagement','post':'POST_ID', 'page':'PAGE_ID'}For App Engagement Ads you must specify a tracking spec explicitly using the Facebook App ID:[{'action.type': 'mobile_app_install', 'application': 'APP_ID'}, {'action.type':'app_custom_event','application':APP_ID}] | See post_engagementmeta spec. Also, number of times anapp eventoccurs. |
| MOBILE_APP_INSTALLS | Mobile app install ads with any bid option | {'action.type':'post_engagement','post':'POST_ID', 'page':'PAGE_ID'}For App Install Ads you must specify a tracking spec explicitly using the Facebook App ID:[{'action.type':'app_custom_event','application':APP_ID}, {'action.type': 'mobile_app_install', 'application': 'APP_ID'}] | See post_engagementmeta spec. Also, number of times users install the app through amobile app install adif there is an iOS/Android version and the number of times anapp eventoccurs. |
| NONE | Any ad type | Seedefault trackingspecs by ad type | |
| PAGE_LIKES | Page Like ads or page post ads with any bid option | {'action.type':'page_engagement', 'page':'PAGE_ID'} | See Page Engagementmeta spec |
| POST_ENGAGEMENT | Page post ads with optimizationnotset tooptimization_goal= POST_ENGAGEMENT | {'action.type':'post_engagement','post':'POST_ID', 'page':'PAGE_ID'} | See Page Post Engagementmeta spec |
| POST_ENGAGEMENT | Page post ads withoptimization_goal= POST_ENGAGEMENT | empty | See Page Post Engagementmeta spec |
| POST_ENGAGEMENT (testing) | any | {'action.type':'dwell','post':'POST_ID', 'page':'PAGE_ID'} | A small percentage of this kind of ads hasdwelltracking type, forcusing on users spending at least a min time on the ads. |
| PRODUCT_ CATALOG_SALES | Dynamic Product Ads | {'action.type': 'post_engagement', 'page': PAGE_ID, 'post': POST_ID} | Number of link clicks on the specific page post if there is only one link, number of engagements on the post, number of times users generate stories or engage with a page. You can specify a product set that is different from the product set in the promoted object but the default is the product set specified in the promoted object. |

[#](#)

## Meta Specs

You can specify multiple types of actions on a single object using a single spec.

| Object | Conversion Spec | Description |
| ----------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Application | {"action.type":["app_engagement"], "application":["APPLICATION_ID"]} | Number of times users generate storiesapp_storyor engage with content via app_use, app_install, credit_spent. |
| Page | {"action.type":["page_engagement"], "page":["PAGE_ID"]} | Number of times users perform any of the following actions in the context of the specified page: checkin, comment, follow, like, page post like, mention, post on page, share a post, answer a question. Plus the number of times users perform any of the following actions in the context of the specified page: click a link, view a photo, play a native FB video. |
| Page Post | {"action.type":["post_engagement"], "post":["POST_ID"], "page":["PAGE_ID"]} | Number of times users perform any of the following actions in the context of the specified post: comment, follow question, like, share, answer question. Plus the number of times users perform any of the following actions: click a link, page like, view photo, play a video hosted on Facebook or an inline Youtube video play. For non embedded videos use link_click. |

[#](#)

## Custom Tracking Specs

To define your own tracking specs, use the action spec framework. See the [Action Specs, Reference](https://developers.facebook.com/docs/marketing-api/reference/conversion-action-query/).

| Action (Object Types) | Description, Tracking spec details | Tracking or Conversion Spec |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| app_custom_event (application) | Custom event on an aplication.Number of custome events on a mobile app. | {'action.type':'app_custom_event','application':APP_ID} |
| app_install (application) | Installing an app.Number of installson canvas or mobile app | [{'action.type':'app_install','application':APP_ID},{'action.type':'mobile_app_install','application':APP_ID}] |
| app_use (application) | Number of times app was used. | {'action.type':'app_use','application':APP_ID} |
| checkin (place) | Check in a place.Number of checkins into the place or into any child places of this page. | {'action.type':'checkin','page': PAGE_ID},{'action.type':'checkin','page.parent:PAGE_ID} |
| comment (post) | Commenting on a post.Number of comments on any or specific page post. | {'action.type':'comment','post.wall':PAGE_ID},{'action.type':'comment','post':POST_ID,'post.wall':PAGE_ID} |
| credit_spend (application) | Instances of spending credit in an app. | 'action.type':'credit_spent','application':APP_ID} |
| follow (question) | Subscribing to an object.Number of answers or follows to a question. | {'action.type':'vote', 'question':QUESTION_ID, 'question.creator':PAGE_ID}, {'action.type':'follow', 'question':QUESTION_ID, 'question.creator':PAGE_ID} |
| leadgen_quality_conversion (pixel) | Down funnel lead conversion (CRM) events. | {'action.type': 'leadgen_quality_conversion', 'fb_pixel': 'FACEBOOK_PIXEL_ID'}, {'action.type': 'leadgen_quality_conversion', 'dataset': 'OFFLINE_EVENT_SET_ID'} |
| like(page, post) | Liking an object.Number of likes on a page or a post. | {'action.type':'like','page':PAGE_ID}, {'action.type':'like','post.wall':PAGE_ID}, {'action.type':'like','post':POST_ID,'post.wall':PAGE_ID} |
| link_click (page,post, url, url domain) | Clicking on a link.Number of times an offsite url link, link with particular url domain, offsite link on a page, offsite link on a post was clicked. | {'action.type':['link_click'],'object':['PAGE_ID']},{'action.type':['link_click'],'object.domain':['URL_DOMAIN']},{'action.type':['link_click'],'post.wall':['PAGE_ID']},{'action.type':['link_click'],'post':['POST_ID'],'post.wall':['PAGE_ID']} |
| mention (page) | Mentioning of a Page.Number of mentions of a page. | {'action.type':'mention','object':PAGE_ID'} |
| offsite_conversion (pixel) | Number of offsite conversions, and accumulated revenue. | {'action.type':'offsite_conversion','fb_pixel':'FACEBOOK_PIXEL_ID'} |
| photo_view (page) | Viewing a photo.Number of photo views,video_plays or link_clicks of the photos/videos/link-shares of any or specific post on a page. | {'action.type':'photo_view', 'post.wall':PAGE_ID}{'action.type':'photo_view', 'post':POST_ID,'post.wall':PAGE_ID} |
| post (post) | Sharing a story.Number of users post on a page. | {'action.type':'post','post.wall':PAGE_ID} |
| receive_offer (offer) | Claiming an Offer.Number of people who claimed a specific offer. | {'action.type':'receive_offer','offer':OFFER_ID} |
| rsvp (event) | Rsvping into an Event.Number of RSVPs (yes and maybe) to an event. Valid values areyes,maybe, andno. | {'action.type':'rsvp','event': EVENT_ID},{'action.type':'rsvp','response':'yes','event': EVENT_ID},{'action.type':'rsvp','response':'no','event': EVENT_ID},{'action.type':'rsvp','response':'maybe','event': EVENT_ID} |
| tab_view (page) | Viewing a page tabNumber of views of a specific page tab. If you want all tab views just specify the page. | {'action.type':'tab_view','page.tab.name':'PAGE_TAB_NAME', 'page':PAGE_ID},{'action.type':'tab_view','page':PAGE_ID} |
| video_play (post) | Watching a video.Number of video watches for any or a specific video post on a page. | {'action.type':'video_play', 'post.wall':PAGE_ID},{'action.type':'video_play', 'post':POST_ID,'post.wall':PAGE_ID} |

[#](#)

## Examples

### Pixel Tracking

Track the performance of different pixels in an ad by specifying the tracking pixel in the ad's [tracking\_specs](https://developers.facebook.com/docs/reference/ads-api/tracking-specs/) field. For example:

```
tracking_specs="[
 {'action.type':'offsite_conversion','fb_pixel':1},
 {'action.type':'offsite_conversion','fb_pixel':2},
 {'action.type':'offsite_conversion','fb_pixel':3}
]"
```

This tracks the performance of pixels "1", "2" and "3". If you want to optimize for pixel "1" only, define the `promoted_object` of the parent ad set. This is useful when you want to optimize for `CHECKOUT`, but also want to track the number of `REGISTRATION` and `ADD_TO_CART`.

*Pixels optimized by specifying the pixel ID in the `promoted_object` are automatically tracked, so you do not need to specify the same pixel in `tracking_specs`.*

[#](#)

## Using Conversion Specs

`conversion_specs` is a field for [ad](https://developers.facebook.com/docs/reference/ads-api/adgroup/). It follows the format `{'action.type':'{ACTION}', ... }` where each action applies to an object. Here are examples of conversion specs for various ad types:

| Ad type | Conversion Spec |
| ----------------------------- | -------------------------------------------------------------------------- |
| Domain ad with social context | {'action.type':'link_click', 'object':'PAGE_ID'} |
| Page like ad | {'action.type':'like', 'page':PAGE_ID} |
| Page post link ad | {'action.type':['link_click'], 'post': [POST_ID], 'post.wall':[PAGE_ID]} |
| All other page post ads | {'action.type':'post_engagement', 'post':'POST_ID', 'page':'PAGE_ID'} |
| Event ad | {'action.type':'rsvp' , 'response':'yes', 'event':'EVENT_ID'} |
| Offer ad | {'action.type':'receive_offer', 'offer':OFFER_ID, 'offer.creator':PAGE_ID} |
| Mobile app install ad | N/A - cannot create such an ad with NONE objective. |
| Mobile app engagement ads | N/A - only CPC and CPM bid types are supported |
| Canvas app install ad | N/A - cannot create such an ad with NONE objective |
| Canvas app engagment ad | N/A - cannot create such an ad with NONE objective |

Some conversion specs contain multiple actions that apply to a single object. These are called *meta specs*. Below are examples:

| Object | Conversion Spec | Description |
| ----------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Page | {"action.type":["page_engagement"], "page":["PAGE_ID"]} | Times someone takes the following actions in a specific page: checkin, comment, follow, like, page post like, mention, post on page, share a post, answer a question. Includes the number of times someone performs these actions in a specific page: view a photo, play a native Facebook video. |
| Page Post | {"action.type":["post_engagement"], "post":["POST_ID"], "page":["PAGE_ID"]} | Number of times somone takes one of these actions in a specific post: comment, follow question, like, share, claim offer, answer question. Includes the number of times someone perform these actions: click a link, page like, view photo, play a video hosted on Facebook or an inline Youtube video play. For non-embedded videos uselink_click. |
| Application | {"action.type":["app_engagement"], "application":["APPLICATION_ID"]} | Number of times someone generateapp_storyor engage with content asapp_use,app_install, orcredit_spent. |

[#](#)

[#](#)

On This Page

[Tracking and Conversion Specs](#tracking-and-conversion-specs)

[Set Tracking Specs](#create)

[Default Tracking Specs](#default)

[Meta Specs](#meta)

[Custom Tracking Specs](#custom)

[Examples](#examples)

[Pixel Tracking](#tracking)

[Using Conversion Specs](#examples-2)


---

<a id="marketing-mix-modeling"></a>

## Marketing Mix Modeling

> **Source:** [https://developers.facebook.com/docs/marketing-api/insights/marketing-mix-modeling](https://developers.facebook.com/docs/marketing-api/insights/marketing-mix-modeling)

# Marketing Mix Modeling Breakdown on Insights API

The marketing mix modeling breakdown on the Insights API is a self-service data extraction option you can use in order to export Meta ads data quickly and easily without going through a Meta Marketing Science Partner or third-party agencies and mobile measurement partners.

The API calls are built into the Insights API using the `breakdowns=mmm` parameter. **Note:** It is not supported in combination with other `breakdowns` or `action_breakdowns`.

The responses contain similar metrics and breakdowns as results from the Marketing Mix Modeling Data Export in Ads Reporting. Marketing mix modeling data is available only on the ad set level (equivalent to the `level=adset` parameter). Currently, the supported metrics for marketing mix modeling data are `impressions` and `spend`. **Note:** The `spend` metric is estimated. See [Insights API, Estimated and Deprecated Metrics](https://developers.facebook.com/docs/marketing-api/insights/estimated-in-development) for more information.

### Permissions

You will need the following permissions for your ad account:

- `ads_read`

## Async Export Queries (Preferred)

Running an async export query using the `export_format=csv` parameter results in a downloaded file with column names that match those in Ads Manager.

**Note:** The `time_increment` can be set to 1 day (i.e., `1`), otherwise `all_time` will be used by default.

### Example request

```
v24.0
```

[#](#)

## Retrieve the Marketing Mix Modeling Data

Send a `GET` API call to the `/insights` endpoint with `breakdowns=mmm`.

```
v24.0
```

**Note:** The Insights API uses default values for parameters not specified in the call. We recommend using the `time_range` and `date_preset` parameters. The granularity of the response can be increased further by using `time_increment`.

### Example request

TRetrieve daily marketing mix modeling data for the last week:

```
v24.0
```

For more information about the Insights API and how to onboard to the Marketing API see the [Insights API Quickstart](https://developers.facebook.com/docs/marketing-api/insights).

[#](#)

## Querying at the Business Manager Level

A common use case is to retrieve marketing mix modeling data for a single Business Manager. This operation isn't directly supported because the Insights API works on the ad account level and below.

To download data for a Business Manager you first need to query available ad accounts with the `/owned_ad_accounts` and `/client_ad_accounts` endpoints. Then iterate over the returned individual ad account IDs to query the marketing mix modeling data for each ad account.

### Example requests

Using `/owned_ad_accounts`

```
v24.0
```

Using `/client_ad_accounts`

```
v24.0
```

[#](#)

## Limits and Best Practices

The granularity of marketing mix modeling data causes the response to have a large number of records as well as a substantial record size. This can cause your requests to time out during computation. To mitigate this, decrease the size of the request by using the `time_range` and `filtering` parameters and query for the total time range in sections. To learn more, see [Insights API Limits & Best Practices](https://developers.facebook.com/docs/marketing-api/insights/best-practices).

Only specific `filtering` supported for querying the marketing mix modeling data. Only these listed operator combinations are allowed for a field; other usages of `filtering` will return an error.

| Field | Allowed Operators |
| ------------------ | ------------------- |
| campaign.id | IN,NOT_IN |
| campaign.name | CONTAIN,NOT_CONTAIN |
| adset.id | IN,NOT_IN |
| adset.name | CONTAIN,NOT_CONTAIN |
| country | IN |
| region | IN |
| dma | IN |
| device_platform | IN |
| publisher_platform | IN |
| platform_position | IN |

We recommend leveraging the Marketing Mix Modeling Data Export in Ads Reporting to export historical data if the API is not needed.

Alternatively, you can use the Insights API Asynchronous Jobs flow. This creates a job that computes the data in an asynchronous fashion. The endpoint responds with the `id` of an Ad Report Run, which you can query for the job status and to retrieve the computed data. **Note:** Some requests can time out even as an asynchronous job. For more information, see [Insights API Asynchronous Jobs](https://developers.facebook.com/docs/marketing-api/insights/best-practices).

You may encounter slightly different column header mappings and column header ordering than the Marketing Mix Modeling Data Export in Ads Reporting. You also have full flexibility to join the marketing mix modeling breakdown's default data with other tables queried from the API.

| Column Index | Default Column Headers from Marketing Mix Modeling Breakdown |
| ------------ | ------------------------------------------------------------ |
| 0 | account_id |
| 1 | campaign_id |
| 2 | adset_id |
| 3 | date_start |
| 4 | date_stop |
| 5 | impressions |
| 6 | spend |
| 7 | country |
| 8 | region |
| 9 | dma |
| 10 | device_platform |
| 11 | platform_position |
| 12 | publisher_platform |
| 13 | creative_media_type |

[#](#)

[#](#)


---

<a id="conversion-lift-measurement"></a>

## Conversion Lift Measurement

> **Source:** [https://developers.facebook.com/docs/marketing-api/guides/lift-studies](https://developers.facebook.com/docs/marketing-api/guides/lift-studies)

[Marketing API](https://developers.facebook.com/docs/marketing-api)

- [Overview](https://developers.facebook.com/docs/marketing-api/overview)
- [Get Started](https://developers.facebook.com/docs/marketing-api/get-started)
- [Ad Creative](https://developers.facebook.com/docs/marketing-api/creative)
- [Bidding](https://developers.facebook.com/docs/marketing-api/bidding)
- [Ad Rules Engine](https://developers.facebook.com/docs/marketing-api/ad-rules)
- [Audiences](https://developers.facebook.com/docs/marketing-api/audiences)
- [Insights API](https://developers.facebook.com/docs/marketing-api/insights)

 - [Breakdowns](https://developers.facebook.com/docs/marketing-api/insights/breakdowns)
 - [Limits & Best Practices](https://developers.facebook.com/docs/marketing-api/insights/best-practices)
 - [Tracking and Conversion Specs](https://developers.facebook.com/docs/marketing-api/tracking-specs)
 - [Marketing Mix Modeling](https://developers.facebook.com/docs/marketing-api/insights/marketing-mix-modeling)
 - [Conversion Lift Measurement](https://developers.facebook.com/docs/marketing-api/guides/lift-studies)
 - [Split Testing](https://developers.facebook.com/docs/marketing-api/guides/split-testing)
 - [Ad Volume](https://developers.facebook.com/docs/marketing-api/insights-api/ads-volume)
 - [App Events API](https://developers.facebook.com/docs/marketing-api/app-event-api)
 - [Error Codes](https://developers.facebook.com/docs/marketing-api/insights/error-codes)
- [Brand Safety and Suitability](https://developers.facebook.com/docs/marketing-api/brand-safety-and-suitability)
- [Best Practices](https://developers.facebook.com/docs/marketing-api/best-practices)
- [Troubleshooting](https://developers.facebook.com/docs/marketing-api/troubleshooting)
- [API Reference](https://developers.facebook.com/docs/marketing-api/reference)
- [Changelog](https://developers.facebook.com/docs/marketing-api/marketing-api-changelog)

On This Page

[Lift Study](#lift-study)

[Set Up Studies](#setup)

[Create a Test Group](#test_group)

[Set Up Multiple Test Groups](#multi_cell)

[Define Advertising Objectives](#objective)

[Create an Objective](#create-objective)

[Reporting](#reporting)

[Retrieve Objectives](#retrieve-objectives)

[Retrieve Results](#retrieve-results)

[Breakdown Results](#breakdown-results)

[Results for a Specific Date Stamp](#datestamp)

# Lift Study

Conversion Lift Measurement is currently limited. Please contact your Meta Representative for information about obtaining access.

Create and run an experiment to measure your Facebook campaign's efficiency. Determine what ads strategy drives the most business impact.
See [Ad Study, Reference](https://developers.facebook.com/docs/marketing-api/reference/ad-study).

When you create a lift study, you create a randomized **test group** of Accounts Center accounts that see your ads and **control group** who don't see your ads.

![](https://scontent-ams2-1.xx.fbcdn.net/v/t39.2178-6/17433022_414854062233610_1617103479556276224_n.png?_nc_cat=104&ccb=1-7&_nc_sid=34156e&_nc_ohc=fRSAAzCnkr4Q7kNvwEfrcRB&_nc_oc=AdnanjsLM9zjiD9QNkiNQVPcdWFDu6T7PNcaL_AMSpWa-c9q12obWjGGGu0erNucK3vO45GQMGRM04Tdd-4qY4_a&_nc_zt=14&_nc_ht=scontent-ams2-1.xx&_nc_gid=wnqGd90DOz3-Nvp9HQ61MA&oh=00_AfqDBnGOV8mwYre19OTJKO-14Op2OHBxxSxGxS-nofJWCg&oe=6965CFAE)

You can securely share conversion data from your ad campaign with Facebook using [Facebook pixels](https://developers.facebook.com/docs/facebook-pixel), or [App Events](https://developers.facebook.com/docs/app-events). Facebook determines the increased conversions generated from your campaign. We compare the number of conversions, Accounts Center accounts converting, and available sales revenue between test and control groups.

## Set Up Studies

Set up a study with one or more groups, called *cells*. When you set up your study, Facebook randomizes the audience for your ads and assigns Accounts Center accounts to either the test or control group. After you run a study, Facebook calculates the difference between the test groups and control groups so that you evaluate the impact of your Facebook ads towards business goals.

To set up a study, make a `POST` call:

```
'https://graph.facebook.com/<API_VERSION>/<BUSINESS_ID>/ad_studies'
```

You can set up a study with a single test group to see how Facebook ads lead to additional business. You can also set up a study with [multiple test groups](#multi_cell), which lets you determine what **advertising approach** works best for your audience.

**Example** - Set up a lift study with one test group

cURL

```
curl \
 -F 'name="new study"' \
 -F 'description="description of my study"' \
 -F 'start_time=1435622400' \
 -F 'end_time=1436918400' \
 -F 'cooldown_start_time=1433116800' \
 -F 'observation_end_time=1438300800' \
 -F 'viewers=[<USER_ID1>, <USER_ID2>]' \
 -F 'type=LIFT' \
 -F 'cells=[{name:"test group",description:"description of my test group",treatment_percentage:90,control_percentage:10,adaccounts:[<ACCOUNT_ID1>,<ACCOUNT_ID2>]}]' \
 -F 'objectives=[{name:"new objective",is_primary:true,type:"CONVERSIONS",applications:[{id:<APP_ID>}]}]' \
 -F 'access_token=<ACCESS_TOKEN>' \
 'https://graph.facebook.com/<API_VERSION>/<BUSINESS_ID>/ad_studies'
```



To create a new study, provide the following:

| Parameter | Description |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| name | Name of study. |
| description | Brief description of the study's purpose. |
| cooldown_start_time | Deprecated. Facebook still delivers during the time betweenobservation_end_timeandend_time. If you usecooldown_start_time, you should now set this time usingstart_time. |
| start_time | Start time of campaign active period.Study start time must be in the future. |
| end_time | End time of campaign active period. |
| observation_end_time | End of thepost test conversion window. During this window (that is, betweenend_timeandobservation_end_time), all Facebook ads (including ones added to this study) are delivered normally to both the test and the control group, but no new users will be opportunity logged. We will continue to match conversions during this period to users in their respective groups. If you don't need apost test conversion windowfor your study, set this toend_time. |
| cells | Cells in study that define test and control groups. |
| objectives | Objectives of the study. SeeDefining Study Objective. |
| viewers | Share this study to a list of Facebook user IDs. |
| type | For Conversion Lift, the type should beLIFT. |

**RESTRICTIONS** -
Once the study starts, you cannot update `start_time` and `treatment_percentage` of the cells. You also cannot remove the associated objects, such as `adaccounts` or `campaigns`, of the test groups. You can still update the `end_time` and `observation_end_time` to a future time if the study has not yet ended, and add new associated objects to test groups.

To run Reach and Frequency in conjunction with Lift measurement, you must set up a Lift study first and make sure the duration of the Reach and Frequency is within the duration of the Lift study.

[#](#)

## Create a Test Group

To begin, determine how many Accounts Center accounts recieve your ads and how many Accounts Center accounts do not. You must create a test group when you set up the study; pass a list of JSON objects in `cells` under `ad_studies`. See [Ad Study Cell, Reference](https://developers.facebook.com/docs/marketing-api/reference/ad-study-cell). A test group contains the following information.

| Parameter | Description |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| name | Name of test group. |
| description | Brief description of test group. |
| treatment_percentage | Defines the Accounts Center accounts who receive your ads. |
| control_percentage | Defines aholdout percentageof the Accounts Center accounts who will not see ads. Treatment plus control percentages must equal 100. |
| ad_studies | List of ad entities, such asadaccountsorcampaigns, to study. Facebook runs and measures all ads under active ad entities during the study period. |

**Example** - Read test groups in a study

cURL

```
curl -G \
 -d 'access_token=<ACCESS_TOKEN>' \
 'https://graph.facebook.com/<API_VERSION>/<STUDY_ID>/cells'
```



**Example** - Update or modify cell information and treatment and control percentages by providing the cell ID in `cells`

cURL

```
curl \
 -F 'cells=[{id:<CELL_ID>,treatment_percentage:80,control_percentage:20}]' \
 -F 'access_token=<ACCESS_TOKEN>' \
 'https://graph.facebook.com/<API_VERSION>/<STUDY_ID>'
```



**Example** - Read all the studies that you created at `ad_studies` for your business

cURL

```
curl -G \
 -d 'access_token=<ACCESS_TOKEN>' \
 'https://graph.facebook.com/<API_VERSION>/<BUSINESS_ID>/ad_studies'
```

You can also see all studies associated with your ad account by making a `GET` request at `{ad-account-ID/include_all_studies=true}` with your access token.

[#](#)

## Set Up Multiple Test Groups

Set up a study with multiple test groups of Facebook users. This helps measure incremental impact of different Facebook strategies on business goals, such as using different ads targeting options. To set up a study with multiple test groups, provide a list of test groups in `cells`.

cURL

```
curl \
 -F 'name="new study"' \
 -F 'description="description of my study"' \
 -F 'start_time=1435622400' \
 -F 'end_time=1436918400' \
 -F 'cooldown_start_time=1433116800' \
 -F 'observation_end_time=1438300800' \
 -F 'viewers=[<USER_ID1>, <USER_ID2>]' \
 -F 'type=LIFT' \
 -F 'cells=[{name:"group A",description:"description of group A",treatment_percentage:50,control_percentage:20,campaigns:[<CAMPAIGN_ID1>]},{name:"group B",description:"description of group B",treatment_percentage:20,control_percentage:10,campaigns:[<CAMPAIGN_ID2>]}]' \
 -F 'objectives=[{name:"new objective",is_primary:true,type:"CONVERSIONS",applications:[{id:<APP_ID>}]}]' \
 -F 'access_token=<ACCESS_TOKEN>' \
 'https://graph.facebook.com/<API_VERSION>/<BUSINESS_ID>/ad_studies'
```



`control_percentage` determines the holdout for each test group respective to the total population. For example, you have a study with two test groups: group A is 50% treatment with 20% control and group B is 20% treament with 10% control. This results in ~28.6%, or 20%/70% of the population in group A, to be control users and ~33.3%, or 10%/30% of the population in group B, to be control users.

![](https://scontent-ams2-1.xx.fbcdn.net/v/t39.2178-6/17365454_785959168240424_3685251067190181888_n.png?_nc_cat=105&ccb=1-7&_nc_sid=34156e&_nc_ohc=Fs6LNqnw6I4Q7kNvwFtQX0n&_nc_oc=Adl3VGJuC8uSveAwI9ikaCsbrRVqmRaEOPuxvqgtVst7vmWunizYjlVy8sWyzm8uTMqNMulTBTjqEMEVAPpTwYsC&_nc_zt=14&_nc_ht=scontent-ams2-1.xx&_nc_gid=wnqGd90DOz3-Nvp9HQ61MA&oh=00_AfrYwg21WB9_0JyBM4UtXie2uPREJB6-WSwA2gxxyCLTfA&oe=6965C4DA)

The sum of treatment and control percentages across test groups normally should equal 100. However, it can be less than 100 for some specific use cases. For example, when you have three test groups that are split evenly at 33%.

You can update, add, and remove test groups in a study.

- To update an existing test group, refer to its ID in test group.
- To add a new test group, provide a new test group object.
- To remove a test group, simply omit it from `cells` when you update the study:

cURL

```
curl \
 -F 'cells=[{id:<CELL_ID1>,treatment_percentage:60,control_percentage:10},{name:"group C",description:"replacing group B",treatment_percentage:25,control_percentage:5,campaigns:[<CAMPAIGN_ID3>]}]' \
 -F 'access_token=<ACCESS_TOKEN>' \
 'https://graph.facebook.com/<API_VERSION>/<STUDY_ID>'
```

[#](#)

## Define Advertising Objectives

Define advertising objectives you want to measure and how you pass conversion data to Facebook. **A lift study requires at least one objective. You cannot modify objectives after the study starts running.** See [Ad Study Objective, Reference](https://developers.facebook.com/docs/marketing-api/reference/ad-study-objective).

**Example** - Create and add the `CONVERSIONS` objective to a study

cURL

```
curl \
 -F 'name="new study"' \
 -F 'description="description of my study"' \
 -F 'start_time=1435622400' \
 -F 'end_time=1436918400' \
 -F 'cooldown_start_time=1433116800' \
 -F 'observation_end_time=1438300800' \
 -F 'viewers=[<USER_ID1>, <USER_ID2>]' \
 -F 'type=LIFT' \
 -F 'cells=[{name:"test group",description:"description of my test group",treatment_percentage:90,control_percentage:10,adaccounts:[<ACCOUNT_ID1>,<ACCOUNT_ID2>]}]' \
 -F 'objectives=[{name:"new objective",is_primary:true,type:"CONVERSIONS",applications:[{id:<APP_ID>}]}]' \
 -F 'access_token=<ACCESS_TOKEN>' \
 'https://graph.facebook.com/<API_VERSION>/<BUSINESS_ID>/ad_studies'
```




| Name | Description | Data Sources |
| ----------- | -------------------------------- | -------------------------- |
| CONVERSIONS | Measure the lift in conversions. | CAPI-based Facebook pixels |

If you use `CONVERSIONS` and use Facebook pixel or Mobile App as event sources, you must provide a list of the event names that you want to capture for the objective. Facebook can then report results based on these specific conversion events.

| Measurement Source | Event Names |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Facebook Pixel | fb_pixel_view_content,fb_pixel_search,fb_pixel_add_to_cart,fb_pixel_add_to_wishlist,fb_pixel_initiate_checkout,fb_pixel_add_payment_info,fb_pixel_purchase,fb_pixel_lead,fb_pixel_complete_registration,custom |
| Mobile App | fb_mobile_activate_app,fb_mobile_complete_registration,fb_mobile_content_view,fb_mobile_search,fb_mobile_rate,fb_mobile_tutorial_completion,fb_mobile_add_to_cart,fb_mobile_add_to_wishlist,fb_mobile_initiated_checkout,fb_mobile_add_payment_info,fb_mobile_purchase,fb_mobile_level_achieved,fb_mobile_achievement_unlocked,fb_mobile_spent_credits |

### Create an Objective

Create an objective by passing a list of JSON objects `objectives` when you create a new study. Objectives contain the following information:

| Parameter | Description |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| name | Name of the objective. |
| is_primary | A boolean specifying that this is your primary advertising objective. A study can only have one primary objective. |
| type | Objective value ofCONVERSIONS. |
| adspixels | List of Facebook pixel IDs along with the relevant list ofevent_namesper ID, if applicable. |
| applications | List of your mobile apps including relevantevent_namesper ID. |
| offline_conversion_data_sets | List of Offline Event set IDs if applicable.Currently, we don't support event breakdowns for Offline Conversion. |
| customconversions | List of Custom Conversion IDs, if applicable. |

You can also have multiple objectives per study. The result will be aggregated based on objectives. Below is an example of a study with multiple objectives.

cURL

```
curl \
 -F 'name="another study"' \
 -F 'description="description of another study"' \
 -F 'start_time=1435622400' \
 -F 'end_time=1436918400' \
 -F 'cooldown_start_time=1433116800' \
 -F 'observation_end_time=1438300800' \
 -F 'viewers=[<USER_ID1>, <USER_ID2>]' \
 -F 'type=LIFT' \
 -F 'cells=[{name:"test group",description:"description of my test group",treatment_percentage:90,control_percentage:10,adaccounts:[<ACCOUNT_ID1>,<ACCOUNT_ID2>]}]' \
 -F 'objectives=[{name:"first objective objective",is_primary:true,type:"CONVERSIONS",applications:[{id:<APP_ID1>},{id:<APP_ID2>}]},{name:"scond objective",type:"CONVERSIONS",applications:[{id:<APP_ID3>,event_names:["fb_mobile_purchase"]}],adspixels:[{id:<FB_PIXEL_ID>,event_names:["fb_pixel_purchase","fb_pixel_lead"]}]}]' \
 -F 'access_token=<ACCESS_TOKEN>' \
 'https://graph.facebook.com/<API_VERSION>/<BUSINESS_ID>/ad_studies'
```



You can update, add, and remove objectives in a study by doing so at the study level similar to modifying test groups. To update an existing objective, refer to its ID in the `objectives` object. To add a new objective, provide a new objective object. To remove an objective, simply omit it from the `objectives` parameter when you update it.

**Example** - Update an objective's `applications` measurement sources and remove its `adspixels` measurement sources

cURL

```
curl \
 -F 'objectives=[{id:<OBJECTIVE_ID>,name:"new objective name",applications:[{id:<APP_ID>}],adspixels:[]}]' \
 -F 'access_token=<ACCESS_TOKEN>' \
 'https://graph.facebook.com/<API_VERSION>/<STUDY_ID>'
```



**Example** - Read objectives for a study

cURL

```
curl -G \
 -d 'access_token=<ACCESS_TOKEN>' \
 'https://graph.facebook.com/<API_VERSION>/<STUDY_OBJECTIVE_ID>?fields=results&breakdowns=["cell_id"]'
```

[#](#)

## Reporting

### Retrieve Objectives

All "buyers" metrics will show up for studies started before the cut-off date 7/13/2021. Studies started after 7/13 will not have "buyers" metrics and breakdown by gender, age and country. This change will impact fields below that start with “buyers" (`buyers_test`, `buyers_control_scaled2`, and so on).

Note also that you need to use the `cell_id` breakdown in order to get cell level results.

A study's objectives are defined during the study setup. See the [setup guide](https://developers.facebook.com/docs/marketing-api/guides/lift-studies) on how to define your study's objectives

You can read the objectives that were created for a study by making a `GET` call to the study's `objectives` edge.

cURL

```
curl -G \
 -d 'access_token=<ACCESS_TOKEN>' \
 'https://graph.facebook.com/<API_VERSION>/<STUDY_OBJECTIVE_ID>?fields=results&breakdowns=["cell_id"]'
```

For more details on objectives, refer to the [Ad Study Objective](https://developers.facebook.com/docs/marketing-api/reference/ad-study-objective) reference documentation.

### Retrieve Results

To retrieve results for an objective, you can make a `GET` call to the objective node by specifying `results` in the fields parameter. The `last_updated_results` field also tells you when the results data for this particular objective was last updated.

Sample response shown as parsed JSON for ease of reading.

Command:

cURL

```
curl -G \
 -d 'access_token=<ACCESS_TOKEN>' \
 'https://graph.facebook.com/<API_VERSION>/<STUDY_OBJECTIVE_ID>?fields=results&breakdowns=["cell_id"]'
```



The resulting data is a JSON object, containing metrics name and values strings. Please refer to Facebook [Lift Metrics Glossary](https://www.facebook.com/business/help/1092662031214127).

With buyers:

```
{
	"results": [
	"{"cell_id":"<cell_id>",
	"population_test":2334212,
	"population_control":123407,
	"population_reached":1862084,
	"impressions":19020874,
	"spend":26059,
	"buyers_control_raw_scaled":37672.615701199,
	"buyers_exposed":30085.482427228,
	"buyers_frequentist_pValue":0.00064950107027983,
	"conversions_control_raw_scaled":110918.27003534,
	"conversions_exposed":86961.044050743,
	"conversions_raw_pValue":0.12863848309723,
	"conversions_test":104412.89695396,
	"conversions_control_scaled":104575.81331581,
	"conversions_incremental":-162.91636184894,
	"conversions_notExposed":87123.960412592,
	"conversions_confidence":0.69291721817069,
	"conversions_multicell_confidence":null,
	"conversions_incremental_lower":-3470.6251396487,
	"conversions_incremental_upper":3235.0644420632,
	"conversions_multicell_rank":null,
	"conversions_incremental_share":-0.001873440730011,
	"conversions_CPiC":-159.95324044961,
	"buyers_test":40732.369934386,
	"buyers_control_scaled":41990.129061459,
	"buyers_incremental":-1257.7591270729,
	"buyers_notExposed":36617.935710157,
	"buyers_confidence":0.19318944031404,
	"buyers_multicell_confidence":null,
	"buyers_incremental_lower":-2905.5296282828,
	"buyers_incremental_upper":426.25813050358,
	"buyers_multicell_rank":null,
	"buyers_incremental_share":-0.041806181107957,
	"buyers_CPiB":-20.718593440578}"
	 ],
	 "id": "<objective_id>"
}
```



Without buyers:

```
{
	"results": [
	"{"cell_id":"<cell_id>",
	"population_test":2334212,
	"population_control":123407,
	"population_reached":1862084,
	"impressions":19020874,
	"spend":26059,
	"conversions_control_raw_scaled":110918.27003534,
	"conversions_exposed":86961.044050743,
	"conversions_raw_pValue":0.12863848309723,
	"conversions_test":104412.89695396,
	"conversions_control_scaled":104575.81331581,
	"conversions_incremental":-162.91636184894,
	"conversions_notExposed":87123.960412592,
	"conversions_confidence":0.69291721817069,
	"conversions_multicell_confidence":null,
	"conversions_incremental_lower":-3470.6251396487,
	"conversions_incremental_upper":3235.0644420632,
	"conversions_multicell_rank":null,
	"conversions_incremental_share":-0.001873440730011,
	"conversions_CPiC":-159.95324044961}"
	 ],
	 "id": "<objective_id>"
}
```

### Breakdown Results

In addition to retrieving the results per objective, you may choose to breakdown the results by providing the `breakdowns` parameter.

cURL

```
curl -G \
 -d 'access_token=<ACCESS_TOKEN>' \
 'https://graph.facebook.com/<API_VERSION>/<STUDY_OBJECTIVE_ID>?fields=results&breakdowns=["cell_id"]'
```



The following are the available breakdown dimensions:

Studies started after 7/13 will not have breakdowns by gender, age and country.

| Breakdown | Values |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| age | 13-17,18-24,25-34,35-44,45-54,55-54,65+ |
| cell_id | IDs of the available cells in the study. |
| gender | MorF |
| country | Two-letter country codes (ISO 3166-1 alpha-2). Example:US,GB,IN,AU.Currently supported only when queried in combination withcell_id.Example:breakdowns=['cell_id','country'] |

The results return multiple JSON objects in the array based on the available breakdowns. For example, if `cell_id` is provided, the results are broken down by the number of cells in the study. You may provide one or more breakdowns; however, the combination of breakdowns must at least 100 conversions from test and control groups combined for results to display.

```
{
 "id": "<STUDY_OBJECTIVE_ID>",
 "results": [
 {
 "cell_id": "<CELL_ID1>",
 ...
 Default fields where the values are specific to the <CELL_ID1> breakdown
 ...
 },
 {
 "cell_id": "<CELL_ID2>",
 ...
 Default fields where the values are specific to the <CELL_ID2> breakdown
 ...
 }],
}
```

[#](#)

## Results for a Specific Date Stamp

You can specify a date stamp in your API call to obtain study results from a specific date. Note that the call returns the same result that it would if you made the same call on that specific date without including the date stamp field. The date should be within the prior 30 days.

cURL

```
curl -G \
 -d 'access_token=<ACCESS_TOKEN>' \
 'https://graph.facebook.com/<API_VERSION>/<STUDY_OBJECTIVE_ID>?fields=results&ds=2020-03-01'
```



[#](#)

[#](#)

On This Page

[Lift Study](#lift-study)

[Set Up Studies](#setup)

[Create a Test Group](#test_group)

[Set Up Multiple Test Groups](#multi_cell)

[Define Advertising Objectives](#objective)

[Create an Objective](#create-objective)

[Reporting](#reporting)

[Retrieve Objectives](#retrieve-objectives)

[Retrieve Results](#retrieve-results)

[Breakdown Results](#breakdown-results)

[Results for a Specific Date Stamp](#datestamp)


---

<a id="split-testing"></a>

## Split Testing

> **Source:** [https://developers.facebook.com/docs/marketing-api/guides/split-testing](https://developers.facebook.com/docs/marketing-api/guides/split-testing)

# Split Testing

Test different advertising strategies on mutually exclusive audiences to see what works.
The API automates audience division, ensures no overlap between groups and helps you to test different variables. Test the impact of different audience types, delivery optimization techniques, ad placements, ad creative, budgets and more. You or your marketing partner can create, initiate and view test results in one place. See [Ad Study Reference](https://developers.facebook.com/docs/marketing-api/reference/ad-study/).

![](https://scontent-ams2-1.xx.fbcdn.net/v/t39.2178-6/17626074_747032625468100_4897318699574231040_n.png?_nc_cat=110&ccb=1-7&_nc_sid=34156e&_nc_ohc=nQ80EQrHtZEQ7kNvwF1Hj8f&_nc_oc=Adl_M_vxk5h64aKpPI1VRv5CnfBcJyHvJDqAV419nlxfRN74xJEzlOTCWFYv6rBTTlwcyCy-VDTpIdlFOzoMiT-0&_nc_zt=14&_nc_ht=scontent-ams2-1.xx&_nc_gid=26nfIk_Xwle0mvR8ZUgwow&oh=00_AfqHrg1V6QqSclqy_TszrTekDWB4Vo8P0fXggsQ4j63ByQ&oe=6965BDE6)

## Guidelines

- **Define KPIs** with your marketing partner or internal team you create a test.
- **Confidence Level** Determine this before creating a test. Tests with larger reach, longer schedules, or higher budgets tend to deliver more statistically significant results.
- **Select only one variable per test.** This helps determine the most likely cause of difference in performance.
- **Comparable Test Sizes** When you test for volume metrics, such as number of conversions, you should scale results and audience sizes so both both test sizes are comparable.

## Test Restrictions

- Max concurrent studies per advertiser: 100
- Max cells per study: 150
- Max ad entities per cell: 100

### Variable Testing

*While you can test many different types of variables, we recommend you only test one variable at a time.* This preserves the scientific integrity of your test, and helps you identify the specific difference that drives better performance.

For example, consider a split test with ad set A and ad set B. If A uses conversions as its delivery optimization method *and* automatic placements, while B uses link clicks for delivery optimization *and* custom placements, you cannot determine if the different delivery optimization methods or the different placements drove better performance.

In this example, if both ad sets used conversions for delivery optimization, but had different placements, you know that placement strategy is responsible for differences in performance.

To setup this test at the ad set level:

```
curl \
-F 'name="new study"' \
-F 'description="test creative"' \
-F 'start_time=1478387569' \
-F 'end_time=1479597169' \
-F 'type=SPLIT_TEST' \
-F 'cells=[{name:"Group A",treatment_percentage:50,adsets:[<AD_SET_ID>]},{name:"Group B",treatment_percentage:50,adsets:[<AD_SET_ID>]}]' \
-F 'access_token=<ACCESS_TOKEN>' \ https://graph.facebook.com/<API_VERSION>/<BUSINESS_ID>/ad_studies
```

### Testing Strategies

You can test two or more strategies against one another. For example, do ads with the conversion objective have a greater impact on your direct response marketing than a website visits objective? To setup this test at the campaign level:

```
curl \
-F 'name="new study"' \
-F 'description="test creative"' \
-F 'start_time=1478387569' \
-F 'end_time=1479597169' \
-F 'type=SPLIT_TEST' \
-F 'cells=[{name:"Group A",treatment_percentage:50,campaigns:[<CAMPAIGN_ID>]},{name:"Group B",treatment_percentage:50,campaigns:[<CAMPAIGN_ID>]}]' \
-F 'access_token=<ACCESS_TOKEN>' \ https://graph.facebook.com/<API_VERSION>/<BUSINESS_ID>/ad_studies
```

### Evaluating Tests

To determine the test that performs the best, chose a strategy or variable that achieves the highest **efficiency metric** based on your campaign objective. For example, to test the conversions objective, the ad set that achieves the **lowest cost-per-action (CPA) performs the best**.

Avoid evaluating tests with uneven test group sizes, or significantly different audience sizes. In this case, you should increase the size and results of one split so that it is comparable to you other tests. If your budget is not proportionate to the size of the test group you should consider the volume of outcomes in addition to efficiency.

You should also use an attribution model that makes sense for your business, and to agree upon it before initiating a split test. If your current attribution model needs reevaluation, contact your Facebook representative to run a lift study. This can show the true causal impact of your conversion and brand marketing efforts.

### Budgeting

You can use custom budgets with your split tests, and choose to test different budgets against each other. However, budget directly impacts reach for your test groups. If your test groups result in large differences in reach or audience size, you increase budget to improve your results and make your test comparable.

[#](#)


---

<a id="ad-volume"></a>

## Ad Volume

> **Source:** [https://developers.facebook.com/docs/marketing-api/insights-api/ads-volume](https://developers.facebook.com/docs/marketing-api/insights-api/ads-volume)

# Ad Volume

View the volume of ads *running or in review* for your ad accounts. These ads count against the ads limit per page that we enacted in early 2021. Query the number of ads running or in review for a given ad account.

## View Ad Volume for Your Ad Account

To see the ad volume for your ad account:

```
curl -G \
 -d "access_token=<ACCESS_TOKEN>" \
 "https://graph.facebook.com/v<API_VERSION>/act_<AD_ACCOUNT_ID>/ads_volume"
```

**Response**

```
{"data":[{"ads_running_or_in_review_count":2}]}
```

For information on managing ad volume, see [About Managing Ad Volume](https://www.facebook.com/business/help/2720085414702598).

[#](#)

## View Running or In Review Status

To see if an ad is running or in review, we check `effective_status`, then `configured_status`, and the ad account's status:

- If an ad has `effective_status` of `1` - `active`, we consider it in *running or in review* state.
- If an ad has `configured_status` of `active` and `effective_status` of `9` - `pending review` or `17` - `pending processing`, we consider it a *running* or *in review*.
- The ad can be *running* or *in review* only if the ad account status is in `1` - `active`, `8` - `pending settlement`, or `9` - `in grace period`.

We also determine if an ad is running or in review based on the ad set's schedule:

- If start time is before current time, and current time is before end time, then we consider the ad running or in review.
- If start time is before current time and the ad set has no end time, we also consider it running or in review.

For example, if the ad set is scheduled to run in the future, the ads are not running or in review. However, if the ad set is scheduled to run from now until 3 months from now, we consider the ads running or in review.

If you are using special ads scheduling features, such as day-parting, we consider the ad running or in review the *whole day* not just for the part of the day when the ad starts running.

[#](#)

## Breakdown by Actors

Use the `show_breakdown_by_actor` field to get a breakdown of ad limits by a specific `actor_id`:

```
curl -G \
 -d "show_breakdown_by_actor=true" \
 -d "access_token=<ACCESS_TOKEN>" \
 "https://graph.facebook.com/v<API_VERSION>/act_<AD_ACCOUNT_ID>/ads_volume"
```

**Response**

```
{
 "data": [
 {
 "ads_running_or_in_review_count": 0,
 "current_account_ads_running_or_in_review_count": 0,
 "actor_id": "<ACTOR_ID_1>",
 "recommendations": [
 ]
 },
 {
 "ads_running_or_in_review_count": 2,
 "current_account_ads_running_or_in_review_count": 2,
 "actor_id": "<ACTOR_ID_2>",
 "recommendations": [
 ]
 }
 ],
}
```

Use `page_id` to get the ad limits for a specific page:

```
curl -G \
 -d "page_id=<PAGE_ID>" \
 -d "access_token=<ACCESS_TOKEN>" \
 "https://graph.facebook.com/v<API_VERSION>/act_<AD_ACCOUNT_ID>/ads_volume"
```

**Response**

```
{
 "data": [
 {
 "ads_running_or_in_review_count": 2,
 "current_account_ads_running_or_in_review_count": 2,
 "actor_id": "<ACTOR_ID>",
 "recommendations": [
 ]
 }
 ],
}
```

### Supported Fields

| Field | Description |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| actor_id | Actor that the limit is enforced against. Currently, this is always the page ID. |
| ads_running_or_in_review_count | Number of ads running or in review for a specific actor. |
| current_account_ads_running_or_in_review_count | Number of ads running or in review within the current ad account on a specific actor. |
| actor_name | Actor that the ads volume aggregated on. Currently, it can only be page name. |
| ad_limit_scope_business | Used in cases where an ad account belongs to a Business Managerandthe ad account is subject to Business Manager level ad limits.This field has the business that defines the ad limits for an ad account. |
| ad_limit_scope_business_manager_id | Used in cases where an ad account belongs to a Business Managerandthe ad account is subject to Business Manager level ad limits.This field has the Business Manager ID for a business that defines the ad limits for an ad account. |
| ad_limit_set_by_page_admin | Ad limit set by a page admin for the business that owns the ad account. |
| ads_running_or_in_review_count_subject_to_limit_set_by_page | Number of ads running or in review for a group of ad accounts. In this case, the group can contain ad accounts that belong to a business or individual ad accounts.If ad limit is not set by the page owner, it returnsnull.If ad limit is set by the page owner, it returns the number of ads running or in review for the group of ad accounts. |
| future_limit_activation_date | Starting date of ad limit that will be effective in the future. |
| future_limit_on_ads_running_or_in_review | Ad limit that will be effective in the future. This limit is related to the number of ads running or in review for the given actor. |
| limit_on_ads_running_or_in_review | Current ad limit for a given actor ID. This limit is related to the number of ads running or in review. |
| recommendations | Recommendations to help reduce the ad volume. Currently, supported values are:zero_impressionlearning_limitedtop_campaigns_with_ads_under_captop_adsets_with_ads_under_capMore information can be found in theBusiness Help Center. |

### Parameters

| Field | Description |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| recommendation_type | Type of the recommendation to help reduce the ad volume. Currently, supported values are:zero_impressionlearning_limitedtop_campaigns_with_ads_under_captop_adsets_with_ads_under_capSee more information aboutmanaging ad volume. |

[#](#)

[#](#)


---

<a id="app-events-api"></a>

## App Events API

> **Source:** [https://developers.facebook.com/docs/marketing-api/app-event-api](https://developers.facebook.com/docs/marketing-api/app-event-api)

# App Events API

We no longer recommend App Events API for new integrations. The [Conversions API](https://developers.facebook.com/docs/marketing-api/conversions-api) now supports web, app, and offline events, so we recommend that advertisers use the Conversions API instead of App Events API. Existing App Events API users can continue to use it, but we will discontinue development of this API. Future innovation will be developed on the Conversions API. Learn more about [Conversions API for App Events](https://developers.facebook.com/docs/marketing-api/conversions-api/app-events).



App Events allow you to track actions that occur in your mobile app or web page such as app installs and purchase events. By tracking these events you can [measure ad performance](https://developers.facebook.com/docs/marketing-api/insights) and [build audiences](https://developers.facebook.com/docs/marketing-api/audiences-api) for ad targeting.

For information on tracking App Events for Business Messaging, please see the [**App Events API for Business Messaging**](https://developers.facebook.com/docs/messenger-platform/analytics/messaging-events-api) in our [Messenger Platform documentation](https://developers.facebook.com/docs/messenger-platform).

## How It Works

There are three types of App Events:

- Automatically Logged Events - The Facebook SDK automatically logs app installs, app sessions, and in-app purchases.
- Standard Events - Popular events that Facebook has created for you.
- Custom Events - Events you create that are specific to your app.

An app event has three parts:

1. `name` - A required string that describes the event. The name appears in the Event log when the app event is sent to Analytics.
2. `valueToSum` - An optional value that Analytics adds to other Value To Sum values from app events with the same name.
3. `parameters` - Optional values included with your app event.

The maximum number of different event names is 1,000. Note: No new event types will be logged once this cap is hit and if you exceed this limit you may see an `100 Invalid parameter` error when logging. However it is possible to [deactivate obsolete events](https://www.facebook.com/help/analytics/966883707418907). Read more about event limits in the [FAQ](https://developers.facebook.com/docs/app-events/faq).

### Before You Start

You will need:

- Your advertiser ID, the advertising ID from an Android device or the Advertising Identifier (IDFA) from an Apple device
- An app access token for Facebook to authenticate. **Do not** store your app access token on the client.

## App Installs

Send a `POST` request from your server to the `/{app-id}/activities` endpoint with the `application_tracking_enabled` and `advertiser_tracking_enabled` parameters:

*Formatted for readability.*

```
curl -i -X POST "https://graph.facebook.com/{app-id}/activities
 ?event=MOBILE_APP_INSTALL
 &application_tracking_enabled=0
 &advertiser_tracking_enabled=0
 &advertiser_id={advertiser-tracking-id}
 &{app-access-token}"
```

On success, your app receives the following response:

```
{
 "success": true
}
```

#### Caveats

- You should report only one install per user. Deduplicate IDs on the ID and user levels if possible.

Visit our [Application Activities Reference guide](https://developers.facebook.com/docs/graph-api/reference/application/activities/) for a list of available parameters.

[#](#)

## Enable Ad Tracking

The `advertiser_tracking_enabled` field specifies whether a person has enabled advertising tracking on their iOS 14.5+ device. Set to 0 for disabled or 1 for enabled. You should fetch this data and return it to Facebook to determine if ad tracking can be used for optimization or conversions.
Meta will use the event data (from partners about user activities off Meta) pursuant to its Data Policy, including for ad reporting, fraud detection and to build and improve our products (including our ads delivery products), but will restrict use of data about that individual to personalize that user’s ads. For devices running earlier versions than iOS 6, this parameter should default to 1.

Visit [Apple, AdSuppport Reference](https://l.facebook.com/l.php?u=https%3A%2F%2Fdeveloper.apple.com%2Flibrary%2Fios%2Fdocumentation%2FAdSupport%2FReference%2FASIdentifierManager_Ref&h=AT0_WG-M4i0vlXr6WRzDS1B9-aWcgAF1KomHhoCtiTcCXV0RnJ6Dj-doDE-7RH0jrzQWAfGjt6YD85rT2_44Cg0jG1SM81JvvXHywLOXk6ICw5Lbyi7PctWXVWyx5SBp_XfD16zcaNtXkreqmMJpeKXaYu2xi38KnqyyU6ttzKo) to get tracking status of a user.

The following code snippet illustrates how to fetch the value of the tracking enabled flag.

You can get the current setting of the tracking enabled flag from the `Settings.shared.isAdvertiserTrackingEnabled` property.

```
print("isAdvertiserTrackingEnabled: \(Settings.shared.isAdvertiserTrackingEnabled)")
```

### Disable Ad Tracking

Any application can choose to include a setting for users to turn off ad tracking within that app. Facebook asks partners to include this option in their SDK and report back the user's choice to Facebook along with the install or conversion event. Facebook uses the install or conversion event for ad reporting, but restricts it from being used in ad optimization. The user's setting must persist across app launches.

[#](#)

## Conversion Events

Send a `POST` request to the `/{app-id}/activities` endpoint with the `event` set to `CUSTOM_APP_EVENTS` and set `advertiser_tracking_enabled` for each individual event. The `advertiser_id` or `attribution` parameter is required.

*Formatted for readability.*

```
curl -i -X POST "https://graph.facebook.com/{app-id}/activities
 ?event=CUSTOM_APP_EVENTS"
 &advertiser_id={advertiser-tracking-id}
 &advertiser_tracking_enabled=1
 &application_tracking_enabled=1
 &custom_events=[
 {"_eventName":"fb_mobile_purchase",
 "event_id":"123456",
 "fb_content":"[
 {"id": "1234", "quantity": 2,},
 {"id": "5678", "quantity": 1,}
 ]",
 "fb_content_type":"product",
 "_valueToSum":21.97,
 "fb_currency":"GBP",
 }
 ]
 &{app-access-token}"
```

On success, your app receives the following response:

```
{
 "success": true
}
```

[#](#)

## Attribution

The `attribution` endpoint returns installs and conversions based on clicks that happened on an ad within 30 days. Ads Manager uses a 1-day view through a 28-day click-through attribution model and insights are surfaced based on impression or click time, not install or conversion time. This is important when comparing your reporting to Facebook Ads Manager reports. In addition to the standard ad click app event claims, you should also keep the following scenarios in mind:

- **View-Through Attribution Claims** - Setting `consider_views=TRUE` returns attribution data for installs that occurred within 1 day of an ad impression, provided the Accounts Center account did not click on an ad within 30 days.The response returned will be `is_view_through=TRUE` and `view_time` will replace `click_time`. All other attributions are the same as with ad click attribution data.
- **Cross-Campaign Claims** - Advertisers are able to track the performance of all ads that have led to an app event. Facebook sends claims for events from ad campaigns as long as the campaign objective is not set to mobile app install or mobile app engagement. This data is surfaced only if the advertiser has added the app to “Mobile App Events Tracking” field in their ad.
- **User Case** — If your client wants to track the installs generated by a Page post ad or website ad clicks that sends users to a mobile site, they can do this in ads manager and Facebook will claim the relevant app installs.
- **Cross-Device Claims** - Advertisers with apps on multiple platform can see data for app installs being driven from ads across these multiple platforms.
- **Use Case** — A user clicks an iPhone ad for an app and then installs the same app on their iPad. We can then attribute the iPad app installation to the iPhone ad regardless of the ad targeting.

[#](#)

## Advanced Matching

Advanced matching allows you to send customer data to Facebook where we use this data to more accurately determine which Accounts Center accounts took action in response to your ad. With this data, Facebook can match conversion events to your customers to optimize your ads and build larger re-marketing audiences.

Send a `POST` request to the `/{app-id}/activities` endpoint with the [`ud` parameter](#params) set to a parameter that will help to track your customer such as customer email or phone number. All customer data must be hashed or Facebook will ignore it. Be sure to set `advertiser_tracking_enabled` for each individual event.

*Formatted for readability.*

```
curl -i -X POST "https://graph.facebook.com/{app-id}/activities
 ?event=CUSTOM_APP_EVENTS
 &advertiser_id={advertiser-tracking-id}
 &advertiser_tracking_enabled=1
 &application_tracking_enabled=1
 &custom_events=[
 {"_eventName":"fb_mobile_purchase",
 "event_id":"123456",
 "fb_content":"[
 {"id": "1234", "quantity": 2,},
 {"id": "5678", "quantity": 1,}
 ]",
 "fb_content_type":"product",
 "_valueToSum":21.97,
 "fb_currency":"GBP",
 }
 ]
 &ud[em]={sha256-hashed-email}
 &{app-access-token}"
```

On success, your app receives the following response:

```
{
 "success": true
}
```

**All user data must be SHA256 hashed before you send it to Facebook. Facebook will ignore data that is not hashed.**

[#](#)

## Deduplication

For app events, we apply the same deduplication functionality that exists for web events. The logic leverages the field `event_id` and `event_name` based deduplication. The `event_id` parameter is an identifier that can uniquely distinguish between similar events. Inaccurate event IDs may cause your conversion to be wrongly deduplicated, further impacting conversion reporting and campaign performance.

[#](#)

## Extended Device Information

Send device information, such as screen width and height, in your app event call using `/{app-id}/activities?extinfo`. Values are separated by commas and must be in the order indexed in the [`/application/activites` reference guide](https://developers.facebook.com/docs/graph-api/reference/application/activities/). When using `extinfo` all values are required.

- `version` must be `a2` for Android
- `version` must be `i2` for iOS

#### Reference

- [ApplicationActivities Parameters](https://developers.facebook.com/docs/graph-api/reference/application/activities/)
- [Android Developer Documentation - Display Metrics](https://l.facebook.com/l.php?u=https%3A%2F%2Fdeveloper.android.com%2Freference%2Fandroid%2Futil%2FDisplayMetrics.html&h=AT0e6pyR_x1LA1yUYfgL9AQy3Uq38ssIlS-1Jt3wKghhQkvMOB9N-2J0VA5ujAmtWsr6dic7id3E2calYCgxSSAvhUnR9rQGjlC1EktAx-vO_fzQzXdVd6NQEPafFd5k78kNMEY1KNwJTa0T6z6Fxilk_3MjMrPu0isYkbXcrk4)
- [Android Developer Documentation - External Storage](https://l.facebook.com/l.php?u=https%3A%2F%2Fdeveloper.android.com%2Freference%2Fandroid%2Fos%2FEnvironment.html%23getExternalStorageDirectory%28%29&h=AT1k27XFFbpgdqnmx2n0d4FlUasE9NR0KKTPJA9yA1P8FLv5eq8_QekSYM4C8ENYizzv50kbjpwYNkbymRYYeCUA_u36cVQDKaux8m30D9MfdogaVPkIz4H0vUiRLyQAMcQhau4zaQ-z_IYd57leWplbQQp3DmYfWhXo9XHaY98)
- [Apple Developer Documentation - Display Metrics](https://l.facebook.com/l.php?u=https%3A%2F%2Fdeveloper.apple.com%2Fdocumentation%2Fcoregraphics%2Fcgsize%2F&h=AT3cpRc5xJYmKxAIH6gRA6XNUebrpwapFBJd8-F_4Tzqei6chUwB3u8i7LqUqAbe_ERYN2hUJO8nPpv2dX_Cty6l9Dql-ZqoY9BGNY17U0uKhGT2YveTyNbyvINC0vqkepMBPw-kcfwYAvTLOUutBCiWojtXPch8txrnRjq-aYY)
- [Apple Developer Documentation - External Storage](https://l.facebook.com/l.php?u=https%3A%2F%2Fdeveloper.apple.com%2Fdocumentation%2Ffoundation%2Fnsfilemanager%3Flanguage%3Dobjc&h=AT0aNObh3P2pAzmrK8c8M8afx4jPQgJNhu_ahjIkAShGOBKaU0dmDy2Lt8MCFq_OFjNc36W6l8BjcD71IJIBktusnyBHefJhu1x2QxNeGUbISOz_J96MlzW_BigW_gKelmHkYEYZ9Yr4zTvz2upE2YdcFW6JOeJ55mMLJ2VS900)
- [Apple Developer Documentation - Screen Size](https://l.facebook.com/l.php?u=https%3A%2F%2Fdeveloper.apple.com%2Fdocumentation%2Fuikit%2Fuiscreen%2F1617836-scale%3Flanguage%3Dobjc&h=AT1xptqVyBN1GrASJVlDUbe2o7bLiIOzflO79Gi3Ba7c0AG8C6a3LrkfAItHjsN4Y4bsrY7_pkWWiFwcxoHEWJk-oAnX-5jq9HvL0_hQbp9jM_eeL2nAp4cTQKqbMU9T1iGywIFjgyR8p6wgTjO4DMA4yguxxLjHeLOykDfDrFI)

[#](#)

## Get Mobile Cookies

We encourage you to associate app events with an `advertiser_id`. However, for Android devices and iOS devices earlier than iOS 6, you can also use the [`attribution` parameter](https://developers.facebook.com/docs/graph-api/reference/application/activities/) set to the mobile cookie of the device.

Note: Mobile cookies are not derived from any user or device attributes. These cookies are not persistent and are designed to be refreshed frequently. Do not use mobile cookies for re-targeting ads.

### Android

The cookie is a random 22-character alphanumeric string.

Get the Facebook attribution ID using `ContentProvider`:

```
public static final Uri ATTRIBUTION_ID_CONTENT_URI = Uri.parse("content://com.facebook.katana.provider.AttributionIdProvider");

public static final String ATTRIBUTION_ID_COLUMN_NAME = "aid";

public static String getAttributionId(ContentResolver contentResolver) {
 String [] projection = {ATTRIBUTION_ID_COLUMN_NAME};
 Cursor c = contentResolver.query(ATTRIBUTION_ID_CONTENT_URI, projection, null, null, null);
 if (c == null || !c.moveToFirst()) {
 return null;
 }
 String attributionId = c.getString(c.getColumnIndex(ATTRIBUTION_ID_COLUMN_NAME));
 c.close();
 return attributionId;
 }
```

You should also [fetch the advertising ID](https://l.facebook.com/l.php?u=https%3A%2F%2Fdeveloper.android.com%2Fgoogle%2Fplay-services%2Fid.html&h=AT1f7nOLNfTrSsseqIBVP3Jr0_fg6yZ4UycywPzQle0KqFo7IWpmVs2CT-esSyWIJvw-1pZygTTvE8v4M6SbYth_EelH6XtpsmMl_FzqHbIzRZO-dFm2qIZB-XoOMWC7gtinpCZF-kJsAZMCIGhHwZVJf51bCuJStr4GHV_rZ5c) of your Android app.

### iOS

The mobile cookie is created by Facebook iOS apps using `CFUUIDCreateString` and is [128-bit UUID string representation](https://l.facebook.com/l.php?u=https%3A%2F%2Fen.wikipedia.org%2Fwiki%2FUniversally_unique_identifier&h=AT0zIC_F40scCxgvE-mJflASECkG9JOiVv8C-iNAYRbvRbBnozr9ttyfwXzUSMZXuM6blCkd4RRbXE8Dk9dzadYXa5KRnNH5qhbcpoFPbd3plK3WHX8-sl5Qky_ENF5IzAaROMZtKdXYWqtZtzxnXWax6HU6Epb51XR68OzcwQ8).

Get both the cookie ID and the IDFA and send them to Facebook as an identifier:

```
ASIdentifierManager *manager = [ASIdentifierManager sharedManager];
NSString *advertiserID = [[manager advertisingIdentifier] UUIDString];

if (advertiserID) {
 // do stuff
}
```

[#](#)

## X-Forwarded-For HTTP Header

If `POST` requests are done from a central place such as a server or proxy, basically, a server-to-server call, then X-Forwarded-For HTTP header is required to ensure accurate location and device information. Send the device's IP address, IPv4 or IPv6 format, via the X-Forwarded-For HTTP header parameter in each of the app event requests you send. By doing so, it allows us to pair the `advertiser_id` to the correct IP address, which we can then use in our platform.

#### IPv6 Example

```
curl ...
 -H "X-Forwarded-For: fd45:f238:3b40:23b1:ffff:ffff:ffff:abcd" \
 https://graph.facebook.com/<APP_ID>/activities/
```

#### IPv4 Example

```
curl ...
 -H "X-Forwarded-For: 192.168.0.99" \
 https://graph.facebook.com/<APP_ID>/activities
```

[#](#)

## Testing

1. Go to [Events Manager](https://business.facebook.com/events_manager2/list).
2. Click the Data sources icon on the left side of the page.
3. Select the name and ID of your data.
4. Click Test events, and select channel as App.
5. Send a AE-API request with [graph api tool](https://developers.facebook.com/tools/explorer/).
6. Your interactions will soon appear in the Test events tab.

[#](#)

## Discrepancies

In the event a client compares a mobile measurement partner's reports with Facebook reports and sees discrepancies, here are some items to check:

If Facebook is reporting fewer installs than MMP:

- Is the FB SDK integrated properly?
- Is the client using the wrong app ID?

If Facebook is reporting more installs than MMP:

- Are the [attribution](#attribution) windows the same? Facebook generally has a larger attribution window than most mobile measurement partners.
- Is the MMP SDK integrated properly?
- Is the client using the wrong app ID?
- Is the discrepancy iOS7 only? Is the MMP receiving Apple's Advertising Identifier (IDFA) from the device and passing it properly to FB?

[#](#)

## Reference

### Application Activities Extinfo

Visit the [`/application/activites` reference guide](https://developers.facebook.com/docs/graph-api/reference/application/activities/) for more information on app extended information.

### User Data Parameters

[Please download this CSV file](https://scontent-ams2-1.xx.fbcdn.net/v/t39.8562-6/314008612_2367937923355843_814664035015443172_n.csv?_nc_cat=101&ccb=1-7&_nc_sid=b8d81d&_nc_ohc=9FdaE6-q3dMQ7kNvwFPmrrd&_nc_oc=Adkt4TykxnvbuAVsNPm_RYO9Hr15TWZHKqj4mUTRHAij8CkKr9onTe4lN3oJqXWZijNjBxxikaM6lEKPW1Opw-Bp&_nc_zt=14&_nc_ht=scontent-ams2-1.xx&_nc_gid=3tMlyd2_CvAmIBpWMfutdg&oh=00_Afr9x-kzwNtQQh9szQ8o_s89B1h_q4k1e_0qJvRoLqM6mg&oe=6965B724)

for examples of properly normalized and hashed data for the parameters below.



[Download (Right-click > Save Link As)](https://scontent-ams2-1.xx.fbcdn.net/v/t39.8562-6/314008612_2367937923355843_814664035015443172_n.csv?_nc_cat=101&ccb=1-7&_nc_sid=b8d81d&_nc_ohc=9FdaE6-q3dMQ7kNvwFPmrrd&_nc_oc=Adkt4TykxnvbuAVsNPm_RYO9Hr15TWZHKqj4mUTRHAij8CkKr9onTe4lN3oJqXWZijNjBxxikaM6lEKPW1Opw-Bp&_nc_zt=14&_nc_ht=scontent-ams2-1.xx&_nc_gid=3tMlyd2_CvAmIBpWMfutdg&oh=00_Afr9x-kzwNtQQh9szQ8o_s89B1h_q4k1e_0qJvRoLqM6mg&oe=6965B724)

| User Data | Parameter | Format | Example |
| ------------------ | ----------- | -------------------------------------------------------------------------------------------------- | ------------------------- |
| Email | em | | jsmith@example.com |
| First Name | fn | Lowercase letters | john |
| Last Name | ln | Lowercase letters | smith |
| Phone | ph | Digits only including country code and area code | 16505554444 |
| External ID | external_id | Any unique ID from the advertiser, such as loyalty membership ID, user ID, and external cookie ID. | a@example.com |
| Gender | ge | Single lowercase letter,form, if unknown, leave blank | f |
| Birthdate | db | Digits only with birth year, month, then day | 19910526for May 26, 1991. |
| City | ct | Lowercase with any spaces removed | menlopark |
| State or Province | st | Lowercase two-letter state or province code | ca |
| Zip or Postal Code | zp | Digits only | 94025 |
| Country | cn | Lowercase two-letter country code | us |

### Standard Event Names

| Event Name | Event Parameters | _valueToSum |
| ------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| AdClick | fb_ad_type | |
| AdImpression | fb_ad_type | With App Ads, revenue of ads from a third-party platform appears on-screen within your app. |
| Contact | | |
| CustomizeProduct | | |
| Donate | | |
| fb_mobile_achievement_unlocked | fb_description | |
| fb_mobile_activate_app* | | |
| fb_mobile_add_payment_info | fb_success | |
| fb_mobile_add_to_cart | fb_content_type,fb_content_idandfb_currency | Price of item added |
| fb_mobile_add_to_wishlist | fb_content_type,fb_content_idandfb_currency | Price of item added |
| fb_mobile_complete_registration | fb_registration_method | |
| fb_mobile_content_view | fb_content_type,fb_content_idandfb_currency | Price of item viewed (if applicable) |
| fb_mobile_initiated_checkout | fb_content_type,fb_content_id,fb_num_items,fb_payment_info_availableandfb_currency | Total price of items in cart |
| fb_mobile_level_achieved | fb_level | |
| fb_mobile_purchase | fb_num_items,fb_content_type,fb_content_idandfb_currency | Purchase price |
| fb_mobile_rate | fb_content_type,fb_content_idandfb_max_rating_value | Rating given |
| fb_mobile_search | fb_content_type,fb_search_stringandfb_success | |
| fb_mobile_spent_credits | fb_content_typeandfb_content_id | Total value of credits spent |
| fb_mobile_tutorial_completion | fb_successandfb_content_id | |
| FindLocation | | |
| Schedule | | |
| StartTrial | fb_order_idandfb_currency | Price of subscription |
| SubmitApplication | | |
| Subscribe | fb_order_idandfb_currency | Price of subscription |

\*Use `fb_mobile_activate_app` event in addition to [install reporting](#installs) to exclude users from seeing ads for this app. **Do not use this event if you have [automatic event logging](https://developers.facebook.com/docs/app-events/automatic-event-collection-detail) enabled.**

[#](#)

### Standard Event Parameters

| Event Parameter Name | Value | Description |
| ------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| _logTime | int | Recommend parameter to specify the time of event, specified in unixtime |
| _valueToSum | float | Numeric value of individual event to be summed in reporting, see above for recommended events to attach to |
| fb_content_id | string | International Article Number (EAN) when applicable, or other product or content identifier(s). For multiple product ids: e.g. "[\"1234\",\"5678\"]" |
| fb_content | string | A list of JSON object that contains the International Article Number (EAN) when applicable, or other product or content identifier(s) as well as quantities and prices of the products.Required:id,quantity. e.g. "[{\"id\": \"1234\", \"quantity\": 2,}, {\"id\": \"5678\", \"quantity\": 1,}]". |
| fb_content_type | string | Theproductorproduct_group |
| fb_currency | string | ISO 4217 code, e.g., "EUR", "USD", "JPY". Required when passing_valueToSumas a price or a purchase amount. |
| fb_description | string | A string description |
| fb_level | string | Level of a game |
| fb_max_rating_value | int | Upper bounds of a rating scale, for example 5 on a 5 star scale |
| fb_num_items | int | Number of items |
| fb_payment_info_available | boolean | 1for yes,0for no |
| fb_registration_method | string | Facebook, Email, Twitter, etc. |
| fb_search_string | string | The text string that was searched for |
| fb_success | boolean | 1for yes,0for no |

[#](#)

## See Also

- [App Events](https://developers.facebook.com/docs/app-events)
- [App Events Best Practices](https://developers.facebook.com/docs/app-events/best-practices)
- [Handling Errors](https://developers.facebook.com/docs/graph-api/using-graph-api/error-handling)
- [GDPR Compliance](https://developers.facebook.com/docs/app-events/gdpr-compliance)
- [Facebook Ads Manager](https://www.facebook.com/ads/manager/accounts/)
- [Facebook App Dashboard](https://developers.facebook.com/apps)

[#](#)

[#](#)


---

<a id="error-codes"></a>

## Error Codes

> **Source:** [https://developers.facebook.com/docs/marketing-api/insights/error-codes](https://developers.facebook.com/docs/marketing-api/insights/error-codes)

# Ads Insights API Error Codes

Error code information for async sources will be available with Marketing API v25.0+.

| Error Code | Error Subcode | Source | Summary | Description |
| ---------- | ------------- | ------------ | ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| -2 | 2490547 | Async | Report Failed | Generating the report failed. Please try again later. |
| 100 | 1504018 | Sync | Request Timed Out | Your request timed out. Please try a smaller date range, fetch less data, or use async jobs. |
| 4 | 1504022 | Async & Sync | Too Many API Requests | Your app has exceeded the allowed number of API requests. Please wait before retrying. For more info, seeAPI Rate Limits. |
| 2 | 1504038 | Sync | Request Timed Out | Your request timed out. Please try a smaller date range, fetch less data, or use async jobs. |
| 4 | 1504039 | Async & Sync | Too Many API Requests | Your app has exceeded the allowed number of API requests. Please wait before retrying. For more info, seeAPI Rate Limits. |
| 2 | 1504041 | Async & Sync | Invalid Breakdowns | No data is available for the requested metrics and breakdowns. Please try different metrics or breakdowns. SeeBreakdowns Documentation. |
| 2 | 1504042 | Async & Sync | Invalid Custom Metrics | You are querying invalid custom metrics. Please try selecting different ones. |
| 2 | 1504043 | Async & Sync | Intermittent Error | Your request encountered an intermittent error, please retry at a later time. |
| 2 | 1504044 | Sync | Unknown Error Occurred | An unexpected error occurred. Please refresh the page or try again. If the issue persists, contactMeta Support. |
| -3 | 1504045 | Async | Report Too Large | Your report was too large. Check the documentation for guidance and try again. SeeData Per Call Limits. |
| 100 | 3191001 | Async & Sync | Permission Error | Ads Insights API permission denied. |

[#](#)


---

