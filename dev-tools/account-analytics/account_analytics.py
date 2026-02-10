"""Generate account-wide Pinterest analytics report with organic and campaign tabs."""

import argparse
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import plotly.graph_objects as go
import requests

sys.path.insert(0, str(Path(__file__).parent.parent / "get-pin-ids"))
from auth import PINTEREST_API_URL, get_access_token

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ORGANIC_METRICS = ["IMPRESSION", "SAVE", "PIN_CLICK", "OUTBOUND_CLICK"]
CAMPAIGN_METRICS = ["TOTAL_IMPRESSION", "TOTAL_CLICKTHROUGH", "SPEND_IN_DOLLAR", "CTR", "ECPC_IN_DOLLAR"]

METRIC_LABELS = {
    "IMPRESSION": "Impressions",
    "TOTAL_IMPRESSION": "Impressions",
    "SAVE": "Saves",
    "PIN_CLICK": "Pin Clicks",
    "OUTBOUND_CLICK": "Outbound Clicks",
    "CLICKTHROUGH": "Clicks",
    "TOTAL_CLICKTHROUGH": "Clicks",
    "SPEND_IN_DOLLAR": "Spend ($)",
    "CTR": "CTR (%)",
    "ECPC_IN_DOLLAR": "CPC ($)",
}

COLORS = {
    "IMPRESSION": "#1f77b4",
    "TOTAL_IMPRESSION": "#1f77b4",
    "SAVE": "#2ca02c",
    "PIN_CLICK": "#ff7f0e",
    "OUTBOUND_CLICK": "#d62728",
    "CLICKTHROUGH": "#9467bd",
    "TOTAL_CLICKTHROUGH": "#9467bd",
    "SPEND_IN_DOLLAR": "#8c564b",
    "CTR": "#e377c2",
    "ECPC_IN_DOLLAR": "#7f7f7f",
}

TIME_PERIODS = {
    "1w": 7,
    "2w": 14,
    "1m": 30,
    "3m": 90,
}


# =============================================================================
# Organic Data Fetching
# =============================================================================

def fetch_all_pins(access_token: str) -> list[dict]:
    """Fetch all pins from the account."""
    pins = []
    headers = {"Authorization": f"Bearer {access_token}"}
    bookmark = None

    print("Fetching pins...")

    while True:
        params = {"page_size": 100}
        if bookmark:
            params["bookmark"] = bookmark

        response = requests.get(
            f"{PINTEREST_API_URL}/pins", headers=headers, params=params
        )

        if not response.ok:
            print(f"Failed to fetch pins: {response.status_code}")
            break

        data = response.json()
        items = data.get("items", [])
        pins.extend(items)
        print(f"  Fetched {len(items)} pins (total: {len(pins)})")

        bookmark = data.get("bookmark")
        if not bookmark:
            break

    return pins


def fetch_pin_analytics(access_token: str, pin_id: str, days: int = 14) -> dict | None:
    """Fetch analytics for a single pin."""
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=days - 1)

    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "metric_types": ",".join(ORGANIC_METRICS),
    }

    response = requests.get(
        f"{PINTEREST_API_URL}/pins/{pin_id}/analytics",
        headers=headers,
        params=params,
    )

    if not response.ok:
        return None

    return response.json()


def collect_organic_analytics(access_token: str, pins: list[dict], days: int = 14) -> list[dict]:
    """Fetch analytics for all pins with rate limiting."""
    results = []
    total = len(pins)

    for i, pin in enumerate(pins):
        pin_id = pin.get("id")
        title = pin.get("title", "Untitled")[:40]

        print(f"  [{i+1}/{total}] {pin_id} - {title}")

        analytics = fetch_pin_analytics(access_token, pin_id, days)

        if analytics:
            daily = analytics.get("all", {}).get("daily_metrics", [])
            totals = {m: 0 for m in ORGANIC_METRICS}
            daily_data = {m: [] for m in ORGANIC_METRICS}
            dates = []

            for day in daily:
                dates.append(day.get("date", ""))
                for m in ORGANIC_METRICS:
                    val = day.get(m, 0)
                    totals[m] += val
                    daily_data[m].append(val)

            results.append({
                "pin_id": pin_id,
                "title": pin.get("title", "Untitled"),
                "created_at": pin.get("created_at", ""),
                "link": pin.get("link", ""),
                "totals": totals,
                "daily": daily_data,
                "dates": dates,
            })

        time.sleep(0.5)

    return results


# =============================================================================
# Campaign Data Fetching
# =============================================================================

def fetch_ad_accounts(access_token: str) -> list[dict]:
    """Fetch all ad accounts."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{PINTEREST_API_URL}/ad_accounts", headers=headers)

    if not response.ok:
        print(f"Failed to fetch ad accounts: {response.status_code} - {response.text}")
        return []

    return response.json().get("items", [])


def fetch_campaigns(access_token: str, ad_account_id: str) -> list[dict]:
    """Fetch all campaigns for an ad account."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns",
        headers=headers,
    )

    if not response.ok:
        print(f"Failed to fetch campaigns: {response.status_code}")
        return []

    return response.json().get("items", [])


def fetch_ad_groups(access_token: str, ad_account_id: str) -> list[dict]:
    """Fetch all ad groups for an ad account."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/ad_groups",
        headers=headers,
    )

    if not response.ok:
        print(f"Failed to fetch ad groups: {response.status_code}")
        return []

    return response.json().get("items", [])


def fetch_ads(access_token: str, ad_account_id: str) -> list[dict]:
    """Fetch all ads for an ad account."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/ads",
        headers=headers,
    )

    if not response.ok:
        print(f"Failed to fetch ads: {response.status_code}")
        return []

    return response.json().get("items", [])


def fetch_entity_analytics(
    access_token: str,
    ad_account_id: str,
    entity_type: str,
    entity_ids: list[str],
    days: int = 14
) -> list[dict]:
    """Fetch analytics for campaigns, ad_groups, or ads."""
    if not entity_ids:
        return []

    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=days - 1)

    headers = {"Authorization": f"Bearer {access_token}"}

    # Map entity type to API parameter name
    id_param = {
        "campaigns": "campaign_ids",
        "ad_groups": "ad_group_ids",
        "ads": "ad_ids",
    }[entity_type]

    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        id_param: ",".join(entity_ids),
        "columns": "TOTAL_IMPRESSION,TOTAL_CLICKTHROUGH,SPEND_IN_DOLLAR,CTR,ECPC_IN_DOLLAR",
        "granularity": "DAY",
    }

    response = requests.get(
        f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/{entity_type}/analytics",
        headers=headers,
        params=params,
    )

    if not response.ok:
        print(f"Failed to fetch {entity_type} analytics: {response.status_code} - {response.text}")
        return []

    return response.json()


def process_entity_analytics(analytics: list[dict], entity_map: dict, id_field: str) -> list[dict]:
    """Process analytics rows into aggregated entity data."""
    # Group daily rows by entity ID
    entity_daily = {}
    for row in analytics:
        eid = row.get(id_field)
        if eid not in entity_daily:
            entity_daily[eid] = []
        entity_daily[eid].append(row)

    results = []
    for entity_id, daily_rows in entity_daily.items():
        entity_info = entity_map.get(entity_id, {})

        daily_data = {m: [] for m in CAMPAIGN_METRICS}
        dates = []
        totals = {m: 0 for m in CAMPAIGN_METRICS}

        # Sort by date
        daily_rows.sort(key=lambda x: x.get("DATE", ""))

        for row in daily_rows:
            dates.append(row.get("DATE", ""))
            for m in CAMPAIGN_METRICS:
                val = row.get(m, 0) or 0
                daily_data[m].append(val)
                if m in ["TOTAL_IMPRESSION", "TOTAL_CLICKTHROUGH", "SPEND_IN_DOLLAR"]:
                    totals[m] += val

        # Calculate rate metrics
        if totals["TOTAL_IMPRESSION"] > 0:
            totals["CTR"] = (totals["TOTAL_CLICKTHROUGH"] / totals["TOTAL_IMPRESSION"]) * 100
        if totals["TOTAL_CLICKTHROUGH"] > 0:
            totals["ECPC_IN_DOLLAR"] = totals["SPEND_IN_DOLLAR"] / totals["TOTAL_CLICKTHROUGH"]

        results.append({
            "id": entity_id,
            "name": entity_info.get("name", "Unknown"),
            "status": entity_info.get("status", "UNKNOWN"),
            "campaign_id": entity_info.get("campaign_id", ""),
            "ad_group_id": entity_info.get("ad_group_id", ""),
            "totals": totals,
            "daily": daily_data,
            "dates": dates,
        })

    return results


def collect_campaign_data(access_token: str, ad_account_id: str, days: int = 14) -> dict:
    """Collect campaign-level data."""
    campaigns = fetch_campaigns(access_token, ad_account_id)
    if not campaigns:
        return {"items": [], "aggregated": {}}

    campaign_ids = [c.get("id") for c in campaigns]
    campaign_map = {c.get("id"): c for c in campaigns}

    analytics = fetch_entity_analytics(access_token, ad_account_id, "campaigns", campaign_ids, days)
    items = process_entity_analytics(analytics, campaign_map, "CAMPAIGN_ID")

    return {"items": items, "aggregated": aggregate_metrics(items)}


def collect_ad_group_data(access_token: str, ad_account_id: str, days: int = 14) -> dict:
    """Collect ad group-level data."""
    ad_groups = fetch_ad_groups(access_token, ad_account_id)
    if not ad_groups:
        return {"items": [], "aggregated": {}}

    ad_group_ids = [ag.get("id") for ag in ad_groups]
    ad_group_map = {ag.get("id"): ag for ag in ad_groups}

    analytics = fetch_entity_analytics(access_token, ad_account_id, "ad_groups", ad_group_ids, days)
    items = process_entity_analytics(analytics, ad_group_map, "AD_GROUP_ID")

    return {"items": items, "aggregated": aggregate_metrics(items)}


def collect_ad_data(access_token: str, ad_account_id: str, days: int = 14) -> dict:
    """Collect ad-level data."""
    ads = fetch_ads(access_token, ad_account_id)
    if not ads:
        return {"items": [], "aggregated": {}}

    ad_ids = [a.get("id") for a in ads]
    ad_map = {a.get("id"): a for a in ads}

    analytics = fetch_entity_analytics(access_token, ad_account_id, "ads", ad_ids, days)
    items = process_entity_analytics(analytics, ad_map, "AD_ID")

    return {"items": items, "aggregated": aggregate_metrics(items)}


def aggregate_metrics(items: list[dict]) -> dict:
    """Aggregate daily metrics across all items."""
    if not items:
        return {}

    # Find item with dates
    dates = []
    for item in items:
        if item.get("dates"):
            dates = item["dates"]
            break

    if not dates:
        return {}

    aggregated = {"dates": dates}
    for m in CAMPAIGN_METRICS:
        aggregated[m] = [0] * len(dates)

    for item in items:
        for m in ["TOTAL_IMPRESSION", "TOTAL_CLICKTHROUGH", "SPEND_IN_DOLLAR"]:
            daily = item.get("daily", {}).get(m, [])
            for i, val in enumerate(daily):
                if i < len(aggregated[m]):
                    aggregated[m][i] += val or 0

    # Calculate daily CTR and CPC
    for i in range(len(dates)):
        if aggregated["TOTAL_IMPRESSION"][i] > 0:
            aggregated["CTR"][i] = (aggregated["TOTAL_CLICKTHROUGH"][i] / aggregated["TOTAL_IMPRESSION"][i]) * 100
        if aggregated["TOTAL_CLICKTHROUGH"][i] > 0:
            aggregated["ECPC_IN_DOLLAR"][i] = aggregated["SPEND_IN_DOLLAR"][i] / aggregated["TOTAL_CLICKTHROUGH"][i]

    return aggregated


def aggregate_organic_metrics(results: list[dict]) -> dict:
    """Aggregate daily metrics across all pins."""
    if not results:
        return {}

    dates = []
    for r in results:
        if r.get("dates"):
            dates = r["dates"]
            break

    if not dates:
        return {}

    aggregated = {"dates": dates}
    for m in ORGANIC_METRICS:
        aggregated[m] = [0] * len(dates)

    for r in results:
        for m in ORGANIC_METRICS:
            daily = r.get("daily", {}).get(m, [])
            for i, val in enumerate(daily):
                if i < len(aggregated[m]):
                    aggregated[m][i] += val

    return aggregated


# =============================================================================
# Chart Generation
# =============================================================================

def create_aggregate_chart(data: dict, metrics: list[str], title: str, chart_id: str) -> str:
    """Create aggregate line chart for metrics."""
    if not data or not data.get("dates"):
        return "<p>No data available</p>"

    fig = go.Figure()

    for m in metrics:
        if m in data:
            fig.add_trace(go.Scatter(
                x=data["dates"],
                y=data[m],
                mode="lines+markers",
                name=METRIC_LABELS.get(m, m),
                line=dict(color=COLORS.get(m, "#333"), width=2),
                marker=dict(size=6),
            ))

    fig.update_layout(
        title=title,
        xaxis=dict(title="Date", tickangle=-45),
        yaxis=dict(title="Count", gridcolor="#eee"),
        plot_bgcolor="white",
        height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=60, r=40, t=60, b=80),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=chart_id)


def create_metric_chart(data: dict, metric: str, chart_id: str) -> str:
    """Create single metric chart."""
    if not data or not data.get("dates"):
        return ""

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data["dates"],
        y=data.get(metric, []),
        mode="lines+markers",
        fill="tozeroy",
        line=dict(color=COLORS.get(metric, "#333"), width=2),
        marker=dict(size=6),
    ))

    fig.update_layout(
        title=f"{METRIC_LABELS.get(metric, metric)}",
        xaxis=dict(tickangle=-45),
        yaxis=dict(gridcolor="#eee"),
        plot_bgcolor="white",
        height=220,
        margin=dict(l=50, r=30, t=40, b=60),
        showlegend=False,
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=chart_id)


# =============================================================================
# HTML Generation
# =============================================================================

def generate_entity_table(items: list[dict], entity_type: str) -> str:
    """Generate HTML table for entities."""
    if not items:
        return "<p>No data available</p>"

    sorted_items = sorted(items, key=lambda x: x["totals"].get("SPEND_IN_DOLLAR", 0), reverse=True)

    rows = ""
    for item in sorted_items:
        name = item["name"][:45] if item["name"] else "Unknown"
        status_class = "status-active" if item["status"] == "ACTIVE" else "status-paused"
        rows += f"""
        <tr>
            <td title="{item['name']}">{name}</td>
            <td><span class="{status_class}">{item['status']}</span></td>
            <td class="value">{item['totals'].get('TOTAL_IMPRESSION', 0):,.0f}</td>
            <td class="value">{item['totals'].get('TOTAL_CLICKTHROUGH', 0):,.0f}</td>
            <td class="value">${item['totals'].get('SPEND_IN_DOLLAR', 0):,.2f}</td>
            <td class="value">{item['totals'].get('CTR', 0):.2f}%</td>
            <td class="value">${item['totals'].get('ECPC_IN_DOLLAR', 0):.2f}</td>
        </tr>"""

    return f"""
    <table class="leaderboard">
        <thead>
            <tr>
                <th>{entity_type}</th><th>Status</th><th>Impressions</th>
                <th>Clicks</th><th>Spend</th><th>CTR</th><th>CPC</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>"""


def generate_organic_leaderboard(results: list[dict], metric: str, limit: int = 10) -> str:
    """Generate HTML table for top pins by metric."""
    sorted_pins = sorted(results, key=lambda x: x["totals"].get(metric, 0), reverse=True)[:limit]

    rows = ""
    for i, pin in enumerate(sorted_pins, 1):
        title = pin["title"][:50] if pin["title"] else "Untitled"
        value = pin["totals"].get(metric, 0)
        pin_id = pin["pin_id"]
        rows += f"""
        <tr>
            <td>{i}</td>
            <td title="{pin['title']}">{title}</td>
            <td class="value">{value:,.0f}</td>
            <td><a href="https://pinterest.com/pin/{pin_id}" target="_blank">View</a></td>
        </tr>"""

    return f"""
    <table class="leaderboard">
        <thead>
            <tr><th>#</th><th>Pin</th><th>{METRIC_LABELS.get(metric, metric)}</th><th>Link</th></tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>"""


def calculate_totals(items: list[dict]) -> dict:
    """Calculate totals from items."""
    totals = {
        "TOTAL_IMPRESSION": sum(item["totals"].get("TOTAL_IMPRESSION", 0) for item in items),
        "TOTAL_CLICKTHROUGH": sum(item["totals"].get("TOTAL_CLICKTHROUGH", 0) for item in items),
        "SPEND_IN_DOLLAR": sum(item["totals"].get("SPEND_IN_DOLLAR", 0) for item in items),
    }
    if totals["TOTAL_IMPRESSION"] > 0:
        totals["CTR"] = (totals["TOTAL_CLICKTHROUGH"] / totals["TOTAL_IMPRESSION"]) * 100
    else:
        totals["CTR"] = 0
    if totals["TOTAL_CLICKTHROUGH"] > 0:
        totals["ECPC_IN_DOLLAR"] = totals["SPEND_IN_DOLLAR"] / totals["TOTAL_CLICKTHROUGH"]
    else:
        totals["ECPC_IN_DOLLAR"] = 0
    return totals


def generate_paid_tab_content(
    tab_id: str,
    entity_type: str,
    items: list[dict],
    aggregated: dict,
    period_data: dict,
) -> str:
    """Generate content for a paid ads tab (campaigns, ad groups, ads)."""
    totals = calculate_totals(items)

    # Generate charts for each period
    charts_by_period = {}
    for period_key, period_items in period_data.items():
        agg = aggregate_metrics(period_items) if period_items else {}
        trend_chart = create_aggregate_chart(
            agg,
            ["TOTAL_IMPRESSION", "TOTAL_CLICKTHROUGH", "SPEND_IN_DOLLAR"],
            f"{entity_type} Performance",
            f"{tab_id}_{period_key}_trend"
        )
        metric_charts = ""
        for m in ["TOTAL_IMPRESSION", "TOTAL_CLICKTHROUGH", "SPEND_IN_DOLLAR", "CTR"]:
            metric_charts += f'<div class="metric-chart">{create_metric_chart(agg, m, f"{tab_id}_{period_key}_{m}")}</div>'

        charts_by_period[period_key] = {
            "trend": trend_chart,
            "metrics": metric_charts,
            "totals": calculate_totals(period_items) if period_items else totals,
            "table": generate_entity_table(period_items, entity_type) if period_items else "",
        }

    # Generate period content divs
    period_contents = ""
    for period_key in TIME_PERIODS.keys():
        pdata = charts_by_period.get(period_key, charts_by_period.get("2w", {}))
        ptotals = pdata.get("totals", totals)
        is_default = period_key == "2w"

        period_contents += f"""
        <div id="{tab_id}_{period_key}" class="period-content {'active' if is_default else ''}" data-tab="{tab_id}">
            <div class="summary">
                <div class="stat">
                    <div class="stat-value" style="color: {COLORS['TOTAL_IMPRESSION']}">{ptotals.get('TOTAL_IMPRESSION', 0):,.0f}</div>
                    <div class="stat-label">Total Impressions</div>
                </div>
                <div class="stat">
                    <div class="stat-value" style="color: {COLORS['TOTAL_CLICKTHROUGH']}">{ptotals.get('TOTAL_CLICKTHROUGH', 0):,.0f}</div>
                    <div class="stat-label">Total Clicks</div>
                </div>
                <div class="stat">
                    <div class="stat-value" style="color: {COLORS['SPEND_IN_DOLLAR']}">${ptotals.get('SPEND_IN_DOLLAR', 0):,.2f}</div>
                    <div class="stat-label">Total Spend</div>
                </div>
                <div class="stat">
                    <div class="stat-value" style="color: {COLORS['CTR']}">{ptotals.get('CTR', 0):.2f}%</div>
                    <div class="stat-label">Avg CTR</div>
                </div>
            </div>

            <h2>Trends</h2>
            <div class="aggregate-chart">{pdata.get('trend', '')}</div>
            <div class="metric-charts">{pdata.get('metrics', '')}</div>

            <h2>{entity_type} Performance</h2>
            <div class="table-section">{pdata.get('table', '')}</div>
        </div>
        """

    return period_contents


def generate_html_report(
    organic_results: list[dict],
    organic_aggregated: dict,
    campaign_data: dict,
    ad_group_data: dict,
    ad_data: dict,
    all_period_data: dict,
) -> str:
    """Generate full HTML report with tabs."""

    # Organic totals
    organic_totals = {m: sum(r["totals"].get(m, 0) for r in organic_results) for m in ORGANIC_METRICS}

    # Organic charts
    organic_trend_chart = create_aggregate_chart(
        organic_aggregated, ORGANIC_METRICS, "Organic Performance", "organic_trend"
    ) if organic_aggregated else ""

    organic_metric_charts = ""
    for m in ORGANIC_METRICS:
        if organic_aggregated:
            organic_metric_charts += f'<div class="metric-chart">{create_metric_chart(organic_aggregated, m, f"organic_{m}")}</div>'

    # Organic leaderboards
    organic_leaderboards = ""
    for m in ORGANIC_METRICS:
        organic_leaderboards += f"""
        <div class="leaderboard-section">
            <h3 style="color: {COLORS.get(m, '#333')}">Top 10 by {METRIC_LABELS.get(m, m)}</h3>
            {generate_organic_leaderboard(organic_results, m)}
        </div>"""

    # Generate paid tab contents
    campaigns_content = generate_paid_tab_content(
        "campaigns", "Campaign",
        campaign_data.get("items", []),
        campaign_data.get("aggregated", {}),
        all_period_data.get("campaigns", {}),
    )

    ad_groups_content = generate_paid_tab_content(
        "ad_groups", "Ad Group",
        ad_group_data.get("items", []),
        ad_group_data.get("aggregated", {}),
        all_period_data.get("ad_groups", {}),
    )

    ads_content = generate_paid_tab_content(
        "ads", "Ad",
        ad_data.get("items", []),
        ad_data.get("aggregated", {}),
        all_period_data.get("ads", {}),
    )

    num_campaigns = len(campaign_data.get("items", []))
    num_ad_groups = len(ad_group_data.get("items", []))
    num_ads = len(ad_data.get("items", []))

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Pinterest Account Analytics</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; border-bottom: 2px solid #ddd; padding-bottom: 10px; margin-top: 30px; }}
        .meta {{ color: #666; margin-bottom: 20px; }}

        /* Tabs */
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }}
        .tab {{
            padding: 12px 24px;
            background: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            color: #666;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: all 0.2s;
        }}
        .tab:hover {{ background: #f0f0f0; }}
        .tab.active {{
            background: #1f77b4;
            color: white;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}

        /* Period Toggle */
        .period-toggle {{
            display: flex;
            gap: 5px;
            margin-bottom: 25px;
            background: white;
            padding: 5px;
            border-radius: 8px;
            width: fit-content;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .period-btn {{
            padding: 8px 16px;
            border: none;
            background: transparent;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            color: #666;
            transition: all 0.2s;
        }}
        .period-btn:hover {{ background: #f0f0f0; }}
        .period-btn.active {{
            background: #e3f2fd;
            color: #1f77b4;
        }}
        .period-content {{
            display: none;
        }}
        .period-content.active {{
            display: block;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .stat-value {{ font-size: 32px; font-weight: bold; }}
        .stat-label {{ color: #666; font-size: 14px; margin-top: 5px; }}

        .aggregate-chart {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        .metric-charts {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-chart {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .leaderboards {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }}
        .leaderboard-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .leaderboard {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        .leaderboard th, .leaderboard td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .leaderboard th {{ font-weight: 600; color: #555; }}
        .leaderboard .value {{ font-weight: bold; }}
        .leaderboard a {{ color: #1f77b4; text-decoration: none; }}
        .leaderboard a:hover {{ text-decoration: underline; }}

        .table-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            overflow-x: auto;
        }}

        .status-active {{ color: #2ca02c; font-weight: bold; }}
        .status-paused {{ color: #999; }}

        .footer {{ margin-top: 30px; color: #999; font-size: 12px; text-align: center; }}
    </style>
</head>
<body>
    <h1>Pinterest Account Analytics</h1>
    <div class="meta">
        {len(organic_results)} pins | {num_campaigns} campaigns | {num_ad_groups} ad groups | {num_ads} ads | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
    </div>

    <div class="tabs">
        <button class="tab active" onclick="showTab('organic')">Organic</button>
        <button class="tab" onclick="showTab('campaigns')">Campaigns</button>
        <button class="tab" onclick="showTab('ad_groups')">Ad Groups</button>
        <button class="tab" onclick="showTab('ads')">Ads</button>
    </div>

    <!-- Organic Tab -->
    <div id="organic" class="tab-content active">
        <div class="summary">
            <div class="stat">
                <div class="stat-value" style="color: {COLORS['IMPRESSION']}">{organic_totals.get('IMPRESSION', 0):,.0f}</div>
                <div class="stat-label">Total Impressions</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: {COLORS['SAVE']}">{organic_totals.get('SAVE', 0):,.0f}</div>
                <div class="stat-label">Total Saves</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: {COLORS['PIN_CLICK']}">{organic_totals.get('PIN_CLICK', 0):,.0f}</div>
                <div class="stat-label">Total Pin Clicks</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: {COLORS['OUTBOUND_CLICK']}">{organic_totals.get('OUTBOUND_CLICK', 0):,.0f}</div>
                <div class="stat-label">Total Outbound Clicks</div>
            </div>
        </div>

        <h2>Trends</h2>
        <div class="aggregate-chart">{organic_trend_chart}</div>
        <div class="metric-charts">{organic_metric_charts}</div>

        <h2>Leaderboards</h2>
        <div class="leaderboards">{organic_leaderboards}</div>
    </div>

    <!-- Campaigns Tab -->
    <div id="campaigns" class="tab-content">
        <div class="period-toggle">
            <button class="period-btn" onclick="showPeriod('campaigns', '1w')">1 Week</button>
            <button class="period-btn active" onclick="showPeriod('campaigns', '2w')">2 Weeks</button>
            <button class="period-btn" onclick="showPeriod('campaigns', '1m')">1 Month</button>
            <button class="period-btn" onclick="showPeriod('campaigns', '3m')">3 Months</button>
        </div>
        {campaigns_content}
    </div>

    <!-- Ad Groups Tab -->
    <div id="ad_groups" class="tab-content">
        <div class="period-toggle">
            <button class="period-btn" onclick="showPeriod('ad_groups', '1w')">1 Week</button>
            <button class="period-btn active" onclick="showPeriod('ad_groups', '2w')">2 Weeks</button>
            <button class="period-btn" onclick="showPeriod('ad_groups', '1m')">1 Month</button>
            <button class="period-btn" onclick="showPeriod('ad_groups', '3m')">3 Months</button>
        </div>
        {ad_groups_content}
    </div>

    <!-- Ads Tab -->
    <div id="ads" class="tab-content">
        <div class="period-toggle">
            <button class="period-btn" onclick="showPeriod('ads', '1w')">1 Week</button>
            <button class="period-btn active" onclick="showPeriod('ads', '2w')">2 Weeks</button>
            <button class="period-btn" onclick="showPeriod('ads', '1m')">1 Month</button>
            <button class="period-btn" onclick="showPeriod('ads', '3m')">3 Months</button>
        </div>
        {ads_content}
    </div>

    <div class="footer">Pinterest Account Analytics Tool</div>

    <script>
        function showTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
            window.dispatchEvent(new Event('resize'));
        }}

        function showPeriod(tabId, period) {{
            // Hide all period content for this tab
            document.querySelectorAll(`.period-content[data-tab="${{tabId}}"]`).forEach(el => el.classList.remove('active'));
            // Show selected period
            document.getElementById(`${{tabId}}_${{period}}`).classList.add('active');
            // Update buttons
            const toggle = event.target.parentElement;
            toggle.querySelectorAll('.period-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            window.dispatchEvent(new Event('resize'));
        }}
    </script>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(description="Generate Pinterest account analytics report")
    parser.add_argument("--days", type=int, default=14, help="Number of days (default: 14)")
    parser.add_argument("--limit", type=int, help="Limit number of pins to analyze")
    parser.add_argument("--open", action="store_true", help="Open report in browser")
    parser.add_argument("--skip-organic", action="store_true", help="Skip organic data")
    parser.add_argument("--skip-paid", action="store_true", help="Skip paid/campaign data")
    args = parser.parse_args()

    try:
        access_token = get_access_token()
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    organic_results = []
    organic_aggregated = {}
    campaign_data = {"items": [], "aggregated": {}}
    ad_group_data = {"items": [], "aggregated": {}}
    ad_data = {"items": [], "aggregated": {}}
    all_period_data = {"campaigns": {}, "ad_groups": {}, "ads": {}}

    # Fetch organic data
    if not args.skip_organic:
        pins = fetch_all_pins(access_token)

        if pins:
            if args.limit:
                pins = pins[:args.limit]
                print(f"Limiting to {args.limit} pins")

            print(f"\nFetching organic analytics for {len(pins)} pins...")
            organic_results = collect_organic_analytics(access_token, pins, args.days)
            organic_aggregated = aggregate_organic_metrics(organic_results)
            print(f"Collected organic data for {len(organic_results)} pins")

    # Fetch paid data
    if not args.skip_paid:
        ad_accounts = fetch_ad_accounts(access_token)
        if ad_accounts:
            ad_account_id = ad_accounts[0]["id"]
            print(f"\nUsing ad account: {ad_account_id}")

            # Fetch data for each time period
            for period_key, days in TIME_PERIODS.items():
                print(f"\nFetching {period_key} data ({days} days)...")

                # Campaigns
                cdata = collect_campaign_data(access_token, ad_account_id, days)
                all_period_data["campaigns"][period_key] = cdata.get("items", [])
                if period_key == "2w":
                    campaign_data = cdata

                # Ad Groups
                agdata = collect_ad_group_data(access_token, ad_account_id, days)
                all_period_data["ad_groups"][period_key] = agdata.get("items", [])
                if period_key == "2w":
                    ad_group_data = agdata

                # Ads
                adata = collect_ad_data(access_token, ad_account_id, days)
                all_period_data["ads"][period_key] = adata.get("items", [])
                if period_key == "2w":
                    ad_data = adata

                time.sleep(0.5)

            print(f"\nCollected: {len(campaign_data.get('items', []))} campaigns, "
                  f"{len(ad_group_data.get('items', []))} ad groups, "
                  f"{len(ad_data.get('items', []))} ads")

    if not organic_results and not campaign_data.get("items"):
        print("No data collected")
        sys.exit(1)

    html = generate_html_report(
        organic_results,
        organic_aggregated,
        campaign_data,
        ad_group_data,
        ad_data,
        all_period_data,
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = OUTPUT_DIR / f"account_analytics_{timestamp}.html"
    output_file.write_text(html)

    print(f"\nReport saved: {output_file}")

    if args.open:
        import webbrowser
        webbrowser.open(f"file://{output_file.absolute()}")


if __name__ == "__main__":
    main()
