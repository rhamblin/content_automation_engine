"""Generate account-wide Pinterest analytics report with leaderboard and trends."""

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

METRICS = ["IMPRESSION", "SAVE", "PIN_CLICK", "OUTBOUND_CLICK"]
METRIC_LABELS = {
    "IMPRESSION": "Impressions",
    "SAVE": "Saves",
    "PIN_CLICK": "Pin Clicks",
    "OUTBOUND_CLICK": "Outbound Clicks",
}
COLORS = {
    "IMPRESSION": "#1f77b4",
    "SAVE": "#2ca02c",
    "PIN_CLICK": "#ff7f0e",
    "OUTBOUND_CLICK": "#d62728",
}


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
        "metric_types": ",".join(METRICS),
    }

    response = requests.get(
        f"{PINTEREST_API_URL}/pins/{pin_id}/analytics",
        headers=headers,
        params=params,
    )

    if not response.ok:
        return None

    return response.json()


def collect_all_analytics(access_token: str, pins: list[dict], days: int = 14) -> list[dict]:
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
            totals = {m: 0 for m in METRICS}
            daily_data = {m: [] for m in METRICS}
            dates = []

            for day in daily:
                dates.append(day.get("date", ""))
                for m in METRICS:
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

        # Rate limiting: ~2 requests per second
        time.sleep(0.5)

    return results


def aggregate_daily_metrics(results: list[dict]) -> dict:
    """Aggregate daily metrics across all pins."""
    if not results:
        return {}

    # Use dates from first result with data
    dates = []
    for r in results:
        if r.get("dates"):
            dates = r["dates"]
            break

    if not dates:
        return {}

    aggregated = {"dates": dates}
    for m in METRICS:
        aggregated[m] = [0] * len(dates)

    for r in results:
        for m in METRICS:
            daily = r.get("daily", {}).get(m, [])
            for i, val in enumerate(daily):
                if i < len(aggregated[m]):
                    aggregated[m][i] += val

    return aggregated


def create_aggregate_chart(data: dict) -> str:
    """Create aggregate line chart for all metrics."""
    fig = go.Figure()

    for m in METRICS:
        fig.add_trace(go.Scatter(
            x=data["dates"],
            y=data[m],
            mode="lines+markers",
            name=METRIC_LABELS[m],
            line=dict(color=COLORS[m], width=2),
            marker=dict(size=6),
        ))

    fig.update_layout(
        title="Account Totals - Last 14 Days",
        xaxis=dict(title="Date", tickangle=-45),
        yaxis=dict(title="Count", gridcolor="#eee"),
        plot_bgcolor="white",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=60, r=40, t=80, b=80),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False)


def create_metric_chart(data: dict, metric: str) -> str:
    """Create single metric aggregate chart."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data["dates"],
        y=data[metric],
        mode="lines+markers",
        fill="tozeroy",
        line=dict(color=COLORS[metric], width=2),
        marker=dict(size=6),
    ))

    fig.update_layout(
        title=f"Total {METRIC_LABELS[metric]}",
        xaxis=dict(tickangle=-45),
        yaxis=dict(gridcolor="#eee"),
        plot_bgcolor="white",
        height=250,
        margin=dict(l=50, r=30, t=50, b=60),
        showlegend=False,
    )

    return fig.to_html(full_html=False, include_plotlyjs=False)


def generate_leaderboard_html(results: list[dict], metric: str, limit: int = 10) -> str:
    """Generate HTML table for top pins by metric."""
    sorted_pins = sorted(results, key=lambda x: x["totals"][metric], reverse=True)[:limit]

    rows = ""
    for i, pin in enumerate(sorted_pins, 1):
        title = pin["title"][:50] if pin["title"] else "Untitled"
        value = pin["totals"][metric]
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
            <tr>
                <th>#</th>
                <th>Pin</th>
                <th>{METRIC_LABELS[metric]}</th>
                <th>Link</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>"""


def generate_html_report(results: list[dict], aggregated: dict) -> str:
    """Generate full HTML report."""
    # Account totals
    account_totals = {m: sum(r["totals"][m] for r in results) for m in METRICS}

    # Charts
    aggregate_chart = create_aggregate_chart(aggregated) if aggregated else ""
    metric_charts = ""
    for m in METRICS:
        if aggregated:
            metric_charts += f'<div class="metric-chart">{create_metric_chart(aggregated, m)}</div>'

    # Leaderboards
    leaderboards = ""
    for m in METRICS:
        leaderboards += f"""
        <div class="leaderboard-section">
            <h3 style="color: {COLORS[m]}">Top 10 by {METRIC_LABELS[m]}</h3>
            {generate_leaderboard_html(results, m)}
        </div>"""

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
        .meta {{ color: #666; margin-bottom: 30px; }}

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

        .footer {{ margin-top: 30px; color: #999; font-size: 12px; text-align: center; }}
    </style>
</head>
<body>
    <h1>Pinterest Account Analytics</h1>
    <div class="meta">
        {len(results)} pins analyzed | Last 14 days | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
    </div>

    <div class="summary">
        <div class="stat">
            <div class="stat-value" style="color: {COLORS['IMPRESSION']}">{account_totals['IMPRESSION']:,.0f}</div>
            <div class="stat-label">Total Impressions</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: {COLORS['SAVE']}">{account_totals['SAVE']:,.0f}</div>
            <div class="stat-label">Total Saves</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: {COLORS['PIN_CLICK']}">{account_totals['PIN_CLICK']:,.0f}</div>
            <div class="stat-label">Total Pin Clicks</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: {COLORS['OUTBOUND_CLICK']}">{account_totals['OUTBOUND_CLICK']:,.0f}</div>
            <div class="stat-label">Total Outbound Clicks</div>
        </div>
    </div>

    <h2>Trends</h2>
    <div class="aggregate-chart">
        {aggregate_chart}
    </div>

    <div class="metric-charts">
        {metric_charts}
    </div>

    <h2>Leaderboards</h2>
    <div class="leaderboards">
        {leaderboards}
    </div>

    <div class="footer">
        Pinterest Account Analytics Tool
    </div>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(description="Generate Pinterest account analytics report")
    parser.add_argument("--days", type=int, default=14, help="Number of days (default: 14)")
    parser.add_argument("--limit", type=int, help="Limit number of pins to analyze")
    parser.add_argument("--open", action="store_true", help="Open report in browser")
    args = parser.parse_args()

    try:
        access_token = get_access_token()
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    pins = fetch_all_pins(access_token)

    if not pins:
        print("No pins found")
        sys.exit(1)

    if args.limit:
        pins = pins[:args.limit]
        print(f"Limiting to {args.limit} pins")

    print(f"\nFetching analytics for {len(pins)} pins...")
    results = collect_all_analytics(access_token, pins, args.days)

    if not results:
        print("No analytics data collected")
        sys.exit(1)

    print(f"\nCollected data for {len(results)} pins")

    aggregated = aggregate_daily_metrics(results)
    html = generate_html_report(results, aggregated)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = OUTPUT_DIR / f"account_analytics_{timestamp}.html"
    output_file.write_text(html)

    print(f"\nReport saved: {output_file}")

    if args.open:
        import webbrowser
        webbrowser.open(f"file://{output_file.absolute()}")


if __name__ == "__main__":
    main()
