"""Generate HTML report with 14-day analytics charts for a Pinterest pin."""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

import plotly.graph_objects as go
import requests

from auth import PINTEREST_API_URL, get_access_token

OUTPUT_DIR = Path(__file__).parent / "output" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

METRICS = ["IMPRESSION", "SAVE", "PIN_CLICK", "OUTBOUND_CLICK"]


def fetch_pin_analytics(access_token: str, pin_id: str, days: int = 14) -> dict | None:
    """Fetch analytics for a pin for the last N days."""
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
        print(f"Failed to fetch analytics: {response.status_code} - {response.text}")
        return None

    return response.json()


def fetch_pin_details(access_token: str, pin_id: str) -> dict | None:
    """Fetch pin details."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{PINTEREST_API_URL}/pins/{pin_id}", headers=headers)

    if not response.ok:
        return None

    return response.json()


def parse_daily_metrics(analytics: dict) -> dict:
    """Parse analytics response into plottable format."""
    data = {"dates": []}
    for metric in METRICS:
        data[metric] = []

    daily = analytics.get("all", {}).get("daily_metrics", [])

    for day in daily:
        data["dates"].append(day.get("date", ""))
        for metric in METRICS:
            data[metric].append(day.get(metric, 0))

    return data


def create_chart(dates: list, values: list, metric: str, color: str) -> str:
    """Create a single plotly chart and return as HTML div."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode="lines+markers",
        name=metric,
        line=dict(color=color, width=2),
        marker=dict(size=8),
        hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text=metric.replace("_", " ").title(), font=dict(size=18)),
        xaxis=dict(title="Date", tickangle=-45),
        yaxis=dict(title="Count", gridcolor="#eee"),
        plot_bgcolor="white",
        margin=dict(l=60, r=40, t=60, b=80),
        height=300,
    )

    return fig.to_html(full_html=False, include_plotlyjs=False)


def generate_html_report(pin_id: str, pin_details: dict | None, data: dict) -> str:
    """Generate full HTML report with all charts."""
    colors = {
        "IMPRESSION": "#1f77b4",
        "SAVE": "#2ca02c",
        "PIN_CLICK": "#ff7f0e",
        "OUTBOUND_CLICK": "#d62728",
    }

    charts_html = ""
    for metric in METRICS:
        charts_html += f'<div class="chart">{create_chart(data["dates"], data[metric], metric, colors[metric])}</div>\n'

    title = pin_details.get("title", "Untitled") if pin_details else "Unknown Pin"
    created = pin_details.get("created_at", "N/A") if pin_details else "N/A"

    # Calculate totals
    totals = {m: sum(data[m]) for m in METRICS}

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Pin Analytics: {pin_id}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{ color: #333; margin-bottom: 5px; }}
        .meta {{ color: #666; margin-bottom: 20px; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .stat-value {{ font-size: 28px; font-weight: bold; }}
        .stat-label {{ color: #666; font-size: 14px; margin-top: 5px; }}
        .charts {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }}
        .chart {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .footer {{ margin-top: 30px; color: #999; font-size: 12px; text-align: center; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="meta">
        Pin ID: {pin_id} | Created: {created} | Report: {datetime.now().strftime("%Y-%m-%d %H:%M")}
    </div>

    <div class="summary">
        <div class="stat">
            <div class="stat-value" style="color: {colors['IMPRESSION']}">{totals['IMPRESSION']:,.0f}</div>
            <div class="stat-label">Total Impressions</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: {colors['SAVE']}">{totals['SAVE']:,.0f}</div>
            <div class="stat-label">Total Saves</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: {colors['PIN_CLICK']}">{totals['PIN_CLICK']:,.0f}</div>
            <div class="stat-label">Total Pin Clicks</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: {colors['OUTBOUND_CLICK']}">{totals['OUTBOUND_CLICK']:,.0f}</div>
            <div class="stat-label">Total Outbound Clicks</div>
        </div>
    </div>

    <div class="charts">
        {charts_html}
    </div>

    <div class="footer">
        Generated by Pinterest Analytics Tool | Last 14 days
    </div>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(description="Generate Pinterest pin analytics HTML report")
    parser.add_argument("pin_id", help="Pinterest pin ID")
    parser.add_argument("--days", type=int, default=14, help="Number of days (default: 14)")
    parser.add_argument("--open", action="store_true", help="Open report in browser")
    args = parser.parse_args()

    try:
        access_token = get_access_token()
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Fetching {args.days}-day analytics for pin {args.pin_id}...")

    pin_details = fetch_pin_details(access_token, args.pin_id)
    analytics = fetch_pin_analytics(access_token, args.pin_id, args.days)

    if not analytics:
        print("No analytics data available")
        sys.exit(1)

    data = parse_daily_metrics(analytics)

    if not data["dates"]:
        print("No daily metrics found in response")
        sys.exit(1)

    html = generate_html_report(args.pin_id, pin_details, data)

    timestamp = datetime.now().strftime("%Y%m%d")
    output_file = OUTPUT_DIR / f"{args.pin_id}_{timestamp}.html"
    output_file.write_text(html)

    print(f"Report saved: {output_file}")

    if args.open:
        import webbrowser
        webbrowser.open(f"file://{output_file.absolute()}")


if __name__ == "__main__":
    main()
