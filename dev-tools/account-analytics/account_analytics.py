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
CAMPAIGN_METRICS = ["IMPRESSION", "CLICKTHROUGH", "SPEND_IN_DOLLAR", "CTR", "ECPC_IN_DOLLAR"]

METRIC_LABELS = {
    "IMPRESSION": "Impressions",
    "SAVE": "Saves",
    "PIN_CLICK": "Pin Clicks",
    "OUTBOUND_CLICK": "Outbound Clicks",
    "CLICKTHROUGH": "Clicks",
    "SPEND_IN_DOLLAR": "Spend ($)",
    "CTR": "CTR (%)",
    "ECPC_IN_DOLLAR": "CPC ($)",
}

COLORS = {
    "IMPRESSION": "#1f77b4",
    "SAVE": "#2ca02c",
    "PIN_CLICK": "#ff7f0e",
    "OUTBOUND_CLICK": "#d62728",
    "CLICKTHROUGH": "#9467bd",
    "SPEND_IN_DOLLAR": "#8c564b",
    "CTR": "#e377c2",
    "ECPC_IN_DOLLAR": "#7f7f7f",
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


def fetch_campaign_analytics(
    access_token: str, ad_account_id: str, campaign_ids: list[str], days: int = 14
) -> list[dict]:
    """Fetch analytics for campaigns."""
    if not campaign_ids:
        return []

    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=days - 1)

    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "campaign_ids": ",".join(campaign_ids),
        "columns": "CAMPAIGN_NAME,IMPRESSION,CLICKTHROUGH,SPEND_IN_DOLLAR,CTR,ECPC_IN_DOLLAR",
        "granularity": "DAY",
    }

    response = requests.get(
        f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns/analytics",
        headers=headers,
        params=params,
    )

    if not response.ok:
        print(f"Failed to fetch campaign analytics: {response.status_code} - {response.text}")
        return []

    return response.json()


def collect_campaign_data(access_token: str, days: int = 14) -> dict:
    """Collect all campaign data."""
    print("\nFetching campaign data...")

    ad_accounts = fetch_ad_accounts(access_token)
    if not ad_accounts:
        print("  No ad accounts found")
        return {"campaigns": [], "aggregated": {}}

    print(f"  Found {len(ad_accounts)} ad account(s)")

    all_campaign_data = []

    for account in ad_accounts:
        ad_account_id = account.get("id")
        print(f"  Processing ad account: {ad_account_id}")

        campaigns = fetch_campaigns(access_token, ad_account_id)
        if not campaigns:
            print("    No campaigns found")
            continue

        print(f"    Found {len(campaigns)} campaign(s)")

        campaign_ids = [c.get("id") for c in campaigns]
        campaign_map = {c.get("id"): c for c in campaigns}

        analytics = fetch_campaign_analytics(access_token, ad_account_id, campaign_ids, days)

        for item in analytics:
            campaign_id = item.get("CAMPAIGN_ID")
            campaign_info = campaign_map.get(campaign_id, {})

            daily_data = {m: [] for m in CAMPAIGN_METRICS}
            dates = []
            totals = {m: 0 for m in CAMPAIGN_METRICS}

            for day in item.get("metrics", []):
                dates.append(day.get("date", ""))
                for m in CAMPAIGN_METRICS:
                    val = day.get(m, 0) or 0
                    daily_data[m].append(val)
                    if m in ["IMPRESSION", "CLICKTHROUGH"]:
                        totals[m] += val
                    elif m == "SPEND_IN_DOLLAR":
                        totals[m] += val

            # Calculate averages for rate metrics
            if totals["IMPRESSION"] > 0:
                totals["CTR"] = (totals["CLICKTHROUGH"] / totals["IMPRESSION"]) * 100
            if totals["CLICKTHROUGH"] > 0:
                totals["ECPC_IN_DOLLAR"] = totals["SPEND_IN_DOLLAR"] / totals["CLICKTHROUGH"]

            all_campaign_data.append({
                "campaign_id": campaign_id,
                "campaign_name": campaign_info.get("name", item.get("CAMPAIGN_NAME", "Unknown")),
                "status": campaign_info.get("status", "UNKNOWN"),
                "totals": totals,
                "daily": daily_data,
                "dates": dates,
            })

        time.sleep(0.5)

    # Aggregate campaign data
    aggregated = aggregate_campaign_metrics(all_campaign_data)

    return {"campaigns": all_campaign_data, "aggregated": aggregated}


def aggregate_campaign_metrics(campaigns: list[dict]) -> dict:
    """Aggregate daily metrics across all campaigns."""
    if not campaigns:
        return {}

    dates = []
    for c in campaigns:
        if c.get("dates"):
            dates = c["dates"]
            break

    if not dates:
        return {}

    aggregated = {"dates": dates}
    for m in CAMPAIGN_METRICS:
        aggregated[m] = [0] * len(dates)

    for c in campaigns:
        for m in ["IMPRESSION", "CLICKTHROUGH", "SPEND_IN_DOLLAR"]:
            daily = c.get("daily", {}).get(m, [])
            for i, val in enumerate(daily):
                if i < len(aggregated[m]):
                    aggregated[m][i] += val or 0

    # Calculate daily CTR and CPC
    for i in range(len(dates)):
        if aggregated["IMPRESSION"][i] > 0:
            aggregated["CTR"][i] = (aggregated["CLICKTHROUGH"][i] / aggregated["IMPRESSION"][i]) * 100
        if aggregated["CLICKTHROUGH"][i] > 0:
            aggregated["ECPC_IN_DOLLAR"][i] = aggregated["SPEND_IN_DOLLAR"][i] / aggregated["CLICKTHROUGH"][i]

    return aggregated


# =============================================================================
# Organic Aggregation
# =============================================================================

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

def create_aggregate_chart(data: dict, metrics: list[str], title: str) -> str:
    """Create aggregate line chart for metrics."""
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
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=60, r=40, t=80, b=80),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False)


def create_metric_chart(data: dict, metric: str) -> str:
    """Create single metric chart."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data["dates"],
        y=data[metric],
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
        height=250,
        margin=dict(l=50, r=30, t=50, b=60),
        showlegend=False,
    )

    return fig.to_html(full_html=False, include_plotlyjs=False)


# =============================================================================
# HTML Generation
# =============================================================================

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


def generate_campaign_table(campaigns: list[dict]) -> str:
    """Generate campaign performance table."""
    sorted_campaigns = sorted(campaigns, key=lambda x: x["totals"].get("SPEND_IN_DOLLAR", 0), reverse=True)

    rows = ""
    for c in sorted_campaigns:
        name = c["campaign_name"][:40]
        status_class = "status-active" if c["status"] == "ACTIVE" else "status-paused"
        rows += f"""
        <tr>
            <td title="{c['campaign_name']}">{name}</td>
            <td><span class="{status_class}">{c['status']}</span></td>
            <td class="value">{c['totals'].get('IMPRESSION', 0):,.0f}</td>
            <td class="value">{c['totals'].get('CLICKTHROUGH', 0):,.0f}</td>
            <td class="value">${c['totals'].get('SPEND_IN_DOLLAR', 0):,.2f}</td>
            <td class="value">{c['totals'].get('CTR', 0):.2f}%</td>
            <td class="value">${c['totals'].get('ECPC_IN_DOLLAR', 0):.2f}</td>
        </tr>"""

    return f"""
    <table class="leaderboard">
        <thead>
            <tr>
                <th>Campaign</th><th>Status</th><th>Impressions</th>
                <th>Clicks</th><th>Spend</th><th>CTR</th><th>CPC</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>"""


def generate_html_report(
    organic_results: list[dict],
    organic_aggregated: dict,
    campaign_data: dict,
) -> str:
    """Generate full HTML report with tabs."""

    # Organic totals
    organic_totals = {m: sum(r["totals"].get(m, 0) for r in organic_results) for m in ORGANIC_METRICS}

    # Campaign totals
    campaigns = campaign_data.get("campaigns", [])
    campaign_aggregated = campaign_data.get("aggregated", {})
    campaign_totals = {
        "IMPRESSION": sum(c["totals"].get("IMPRESSION", 0) for c in campaigns),
        "CLICKTHROUGH": sum(c["totals"].get("CLICKTHROUGH", 0) for c in campaigns),
        "SPEND_IN_DOLLAR": sum(c["totals"].get("SPEND_IN_DOLLAR", 0) for c in campaigns),
    }
    if campaign_totals["IMPRESSION"] > 0:
        campaign_totals["CTR"] = (campaign_totals["CLICKTHROUGH"] / campaign_totals["IMPRESSION"]) * 100
    else:
        campaign_totals["CTR"] = 0
    if campaign_totals["CLICKTHROUGH"] > 0:
        campaign_totals["ECPC_IN_DOLLAR"] = campaign_totals["SPEND_IN_DOLLAR"] / campaign_totals["CLICKTHROUGH"]
    else:
        campaign_totals["ECPC_IN_DOLLAR"] = 0

    # Organic charts
    organic_trend_chart = create_aggregate_chart(organic_aggregated, ORGANIC_METRICS, "Organic Performance - Last 14 Days") if organic_aggregated else ""
    organic_metric_charts = ""
    for m in ORGANIC_METRICS:
        if organic_aggregated:
            organic_metric_charts += f'<div class="metric-chart">{create_metric_chart(organic_aggregated, m)}</div>'

    # Organic leaderboards
    organic_leaderboards = ""
    for m in ORGANIC_METRICS:
        organic_leaderboards += f"""
        <div class="leaderboard-section">
            <h3 style="color: {COLORS.get(m, '#333')}">Top 10 by {METRIC_LABELS.get(m, m)}</h3>
            {generate_organic_leaderboard(organic_results, m)}
        </div>"""

    # Campaign charts
    campaign_trend_chart = ""
    campaign_metric_charts = ""
    if campaign_aggregated:
        campaign_trend_chart = create_aggregate_chart(
            campaign_aggregated,
            ["IMPRESSION", "CLICKTHROUGH", "SPEND_IN_DOLLAR"],
            "Campaign Performance - Last 14 Days"
        )
        for m in ["IMPRESSION", "CLICKTHROUGH", "SPEND_IN_DOLLAR", "CTR"]:
            campaign_metric_charts += f'<div class="metric-chart">{create_metric_chart(campaign_aggregated, m)}</div>'

    # Campaign table
    campaign_table = generate_campaign_table(campaigns) if campaigns else "<p>No campaigns found</p>"

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
        h2 {{ color: #555; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
        .meta {{ color: #666; margin-bottom: 20px; }}

        /* Tabs */
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
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

        .campaign-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        .status-active {{ color: #2ca02c; font-weight: bold; }}
        .status-paused {{ color: #999; }}

        .footer {{ margin-top: 30px; color: #999; font-size: 12px; text-align: center; }}
    </style>
</head>
<body>
    <h1>Pinterest Account Analytics</h1>
    <div class="meta">
        {len(organic_results)} pins | {len(campaigns)} campaigns | Last 14 days | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
    </div>

    <div class="tabs">
        <button class="tab active" onclick="showTab('organic')">Organic</button>
        <button class="tab" onclick="showTab('campaigns')">Campaigns</button>
    </div>

    <!-- Organic Tab -->
    <div id="organic" class="tab-content active">
        <div class="summary">
            <div class="stat">
                <div class="stat-value" style="color: {COLORS['IMPRESSION']}">{organic_totals['IMPRESSION']:,.0f}</div>
                <div class="stat-label">Total Impressions</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: {COLORS['SAVE']}">{organic_totals['SAVE']:,.0f}</div>
                <div class="stat-label">Total Saves</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: {COLORS['PIN_CLICK']}">{organic_totals['PIN_CLICK']:,.0f}</div>
                <div class="stat-label">Total Pin Clicks</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: {COLORS['OUTBOUND_CLICK']}">{organic_totals['OUTBOUND_CLICK']:,.0f}</div>
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
        <div class="summary">
            <div class="stat">
                <div class="stat-value" style="color: {COLORS['IMPRESSION']}">{campaign_totals['IMPRESSION']:,.0f}</div>
                <div class="stat-label">Total Impressions</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: {COLORS['CLICKTHROUGH']}">{campaign_totals['CLICKTHROUGH']:,.0f}</div>
                <div class="stat-label">Total Clicks</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: {COLORS['SPEND_IN_DOLLAR']}">${campaign_totals['SPEND_IN_DOLLAR']:,.2f}</div>
                <div class="stat-label">Total Spend</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: {COLORS['CTR']}">{campaign_totals['CTR']:.2f}%</div>
                <div class="stat-label">Avg CTR</div>
            </div>
        </div>

        <h2>Trends</h2>
        <div class="aggregate-chart">{campaign_trend_chart}</div>
        <div class="metric-charts">{campaign_metric_charts}</div>

        <h2>Campaign Performance</h2>
        <div class="campaign-section">{campaign_table}</div>
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
    parser.add_argument("--skip-campaigns", action="store_true", help="Skip campaign data")
    args = parser.parse_args()

    try:
        access_token = get_access_token()
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    organic_results = []
    organic_aggregated = {}
    campaign_data = {"campaigns": [], "aggregated": {}}

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

    # Fetch campaign data
    if not args.skip_campaigns:
        campaign_data = collect_campaign_data(access_token, args.days)
        print(f"Collected data for {len(campaign_data.get('campaigns', []))} campaigns")

    if not organic_results and not campaign_data.get("campaigns"):
        print("No data collected")
        sys.exit(1)

    html = generate_html_report(organic_results, organic_aggregated, campaign_data)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = OUTPUT_DIR / f"account_analytics_{timestamp}.html"
    output_file.write_text(html)

    print(f"\nReport saved: {output_file}")

    if args.open:
        import webbrowser
        webbrowser.open(f"file://{output_file.absolute()}")


if __name__ == "__main__":
    main()
