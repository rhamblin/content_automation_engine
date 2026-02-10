"""Unified Dashboard - Multi-platform analytics dashboard."""

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from adapters import ADAPTERS, AccountMetrics

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = Path(__file__).parent / "config.json"

PLATFORM_COLORS = {
    "pinterest": "#E60023",
    "instagram": "#E1306C",
    "tiktok": "#000000",
    "reddit": "#FF4500",
}

METRIC_COLORS = {
    "impressions": "#1f77b4",
    "engagements": "#2ca02c",
    "clicks": "#ff7f0e",
    "spend": "#d62728",
}


@dataclass
class DashboardData:
    """Container for all dashboard data."""
    metrics_by_platform: dict[str, list[AccountMetrics]]
    aggregate: AccountMetrics | None = None


def load_config() -> dict:
    """Load configuration file."""
    if not CONFIG_PATH.exists():
        print(f"Config not found at {CONFIG_PATH}")
        print("Copy config.json.example to config.json and configure your accounts.")
        sys.exit(1)
    return json.loads(CONFIG_PATH.read_text())


def fetch_all_metrics(config: dict, days: int = 14) -> DashboardData:
    """Fetch metrics from all enabled platforms."""
    metrics_by_platform = {}

    for platform_name, platform_config in config.get("platforms", {}).items():
        if not platform_config.get("enabled", False):
            print(f"[{platform_name}] Skipped (disabled)")
            continue

        adapter_class = ADAPTERS.get(platform_name)
        if not adapter_class:
            print(f"[{platform_name}] No adapter found")
            continue

        platform_metrics = []

        for niche, account_config in platform_config.get("accounts", {}).items():
            print(f"[{platform_name}:{niche}] Fetching metrics...")

            adapter = adapter_class(
                credentials_path=account_config.get("credentials_path", ""),
                account_config=account_config,
            )

            metrics = adapter.fetch_metrics(niche, days)
            platform_metrics.append(metrics)

            if metrics.error:
                print(f"  Error: {metrics.error}")
            else:
                print(f"  Impressions: {metrics.impressions:,}")
                print(f"  Engagements: {metrics.engagements:,}")
                print(f"  Clicks: {metrics.clicks:,}")
                if metrics.spend > 0:
                    print(f"  Spend: ${metrics.spend:,.2f}")

        if platform_metrics:
            metrics_by_platform[platform_name] = platform_metrics

    # Create aggregate
    aggregate = create_aggregate(metrics_by_platform)

    return DashboardData(
        metrics_by_platform=metrics_by_platform,
        aggregate=aggregate,
    )


def create_aggregate(metrics_by_platform: dict[str, list[AccountMetrics]]) -> AccountMetrics:
    """Create aggregated metrics across all platforms."""
    agg = AccountMetrics(
        platform="all",
        niche="all",
        account_name="All Platforms",
    )

    for platform_metrics in metrics_by_platform.values():
        for m in platform_metrics:
            agg.impressions += m.impressions
            agg.engagements += m.engagements
            agg.clicks += m.clicks
            agg.reach += m.reach
            agg.spend += m.spend
            agg.paid_impressions += m.paid_impressions
            agg.paid_clicks += m.paid_clicks

    return agg


# =============================================================================
# Chart Generation
# =============================================================================

def create_platform_comparison_chart(data: DashboardData) -> str:
    """Create bar chart comparing platforms."""
    platforms = []
    impressions = []
    engagements = []
    clicks = []

    for platform, metrics_list in data.metrics_by_platform.items():
        total_imp = sum(m.impressions for m in metrics_list)
        total_eng = sum(m.engagements for m in metrics_list)
        total_clicks = sum(m.clicks for m in metrics_list)

        platforms.append(platform.title())
        impressions.append(total_imp)
        engagements.append(total_eng)
        clicks.append(total_clicks)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Impressions",
        x=platforms,
        y=impressions,
        marker_color=METRIC_COLORS["impressions"],
    ))
    fig.add_trace(go.Bar(
        name="Engagements",
        x=platforms,
        y=engagements,
        marker_color=METRIC_COLORS["engagements"],
    ))
    fig.add_trace(go.Bar(
        name="Clicks",
        x=platforms,
        y=clicks,
        marker_color=METRIC_COLORS["clicks"],
    ))

    fig.update_layout(
        title="Platform Comparison",
        barmode="group",
        plot_bgcolor="white",
        height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=60, r=40, t=60, b=40),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, div_id="platform_comparison")


def create_niche_breakdown_chart(data: DashboardData) -> str:
    """Create chart showing metrics by niche across platforms."""
    niche_data = {}

    for platform, metrics_list in data.metrics_by_platform.items():
        for m in metrics_list:
            if m.niche not in niche_data:
                niche_data[m.niche] = {"impressions": 0, "engagements": 0, "clicks": 0}
            niche_data[m.niche]["impressions"] += m.impressions
            niche_data[m.niche]["engagements"] += m.engagements
            niche_data[m.niche]["clicks"] += m.clicks

    niches = list(niche_data.keys())
    impressions = [niche_data[n]["impressions"] for n in niches]
    engagements = [niche_data[n]["engagements"] for n in niches]

    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "pie"}]])

    fig.add_trace(go.Pie(
        labels=niches,
        values=impressions,
        name="Impressions",
        title="Impressions by Niche",
    ), row=1, col=1)

    fig.add_trace(go.Pie(
        labels=niches,
        values=engagements,
        name="Engagements",
        title="Engagements by Niche",
    ), row=1, col=2)

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, div_id="niche_breakdown")


def create_daily_trend_chart(metrics: AccountMetrics, chart_id: str) -> str:
    """Create daily trend chart for metrics."""
    if not metrics.daily:
        return "<p>No daily data available</p>"

    dates = [d.date for d in metrics.daily]
    impressions = [d.impressions for d in metrics.daily]
    engagements = [d.engagements for d in metrics.daily]
    clicks = [d.clicks for d in metrics.daily]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates, y=impressions,
        mode="lines+markers",
        name="Impressions",
        line=dict(color=METRIC_COLORS["impressions"], width=2),
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=engagements,
        mode="lines+markers",
        name="Engagements",
        line=dict(color=METRIC_COLORS["engagements"], width=2),
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=clicks,
        mode="lines+markers",
        name="Clicks",
        line=dict(color=METRIC_COLORS["clicks"], width=2),
    ))

    fig.update_layout(
        xaxis=dict(tickangle=-45),
        yaxis=dict(gridcolor="#eee"),
        plot_bgcolor="white",
        height=300,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=50, r=30, t=40, b=60),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=chart_id)


def create_spend_chart(data: DashboardData) -> str:
    """Create spend breakdown by platform."""
    platforms = []
    spends = []
    colors = []

    for platform, metrics_list in data.metrics_by_platform.items():
        total_spend = sum(m.spend for m in metrics_list)
        if total_spend > 0:
            platforms.append(platform.title())
            spends.append(total_spend)
            colors.append(PLATFORM_COLORS.get(platform, "#666"))

    if not spends:
        return ""

    fig = go.Figure(go.Pie(
        labels=platforms,
        values=spends,
        marker_colors=colors,
        textinfo="label+percent+value",
        texttemplate="%{label}<br>$%{value:,.2f}<br>(%{percent})",
    ))

    fig.update_layout(
        title="Ad Spend by Platform",
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, div_id="spend_chart")


# =============================================================================
# HTML Generation
# =============================================================================

def generate_stat_card(value: str, label: str, color: str = "#333") -> str:
    """Generate a stat card HTML."""
    return f"""
    <div class="stat">
        <div class="stat-value" style="color: {color}">{value}</div>
        <div class="stat-label">{label}</div>
    </div>"""


def generate_platform_section(platform: str, metrics_list: list[AccountMetrics]) -> str:
    """Generate HTML section for a platform."""
    total_imp = sum(m.impressions for m in metrics_list)
    total_eng = sum(m.engagements for m in metrics_list)
    total_clicks = sum(m.clicks for m in metrics_list)
    total_spend = sum(m.spend for m in metrics_list)

    color = PLATFORM_COLORS.get(platform, "#666")

    # Account cards
    account_cards = ""
    for m in metrics_list:
        eng_rate = (m.engagements / m.impressions * 100) if m.impressions > 0 else 0
        click_rate = (m.clicks / m.impressions * 100) if m.impressions > 0 else 0

        error_badge = f'<span class="error-badge">Error</span>' if m.error else ""

        account_cards += f"""
        <div class="account-card">
            <div class="account-header">
                <span class="account-name">{m.account_name}</span>
                <span class="niche-badge">{m.niche}</span>
                {error_badge}
            </div>
            <div class="account-metrics">
                <div class="metric">
                    <span class="metric-value">{m.impressions:,}</span>
                    <span class="metric-label">Impressions</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{m.engagements:,}</span>
                    <span class="metric-label">Engagements</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{m.clicks:,}</span>
                    <span class="metric-label">Clicks</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{eng_rate:.2f}%</span>
                    <span class="metric-label">Eng Rate</span>
                </div>
            </div>
            {f'<div class="spend-row">Spend: ${m.spend:,.2f}</div>' if m.spend > 0 else ''}
        </div>"""

    # Daily chart for first account (if available)
    daily_chart = ""
    if metrics_list and metrics_list[0].daily:
        daily_chart = f"""
        <div class="chart-section">
            <h4>Daily Trend</h4>
            {create_daily_trend_chart(metrics_list[0], f"{platform}_daily")}
        </div>"""

    return f"""
    <div class="platform-section" id="platform_{platform}">
        <div class="platform-header" style="border-left: 4px solid {color}">
            <h3>{platform.title()}</h3>
            <div class="platform-summary">
                <span>{total_imp:,} impressions</span>
                <span>{total_eng:,} engagements</span>
                <span>{total_clicks:,} clicks</span>
                {f'<span>${total_spend:,.2f} spend</span>' if total_spend > 0 else ''}
            </div>
        </div>
        <div class="account-cards">{account_cards}</div>
        {daily_chart}
    </div>"""


def generate_html_report(data: DashboardData, config: dict) -> str:
    """Generate the full HTML dashboard."""
    agg = data.aggregate

    # Aggregate stats
    agg_stats = f"""
    {generate_stat_card(f"{agg.impressions:,}", "Total Impressions", METRIC_COLORS['impressions'])}
    {generate_stat_card(f"{agg.engagements:,}", "Total Engagements", METRIC_COLORS['engagements'])}
    {generate_stat_card(f"{agg.clicks:,}", "Total Clicks", METRIC_COLORS['clicks'])}
    {generate_stat_card(f"${agg.spend:,.2f}", "Total Spend", METRIC_COLORS['spend'])}
    """

    # Platform comparison chart
    platform_chart = create_platform_comparison_chart(data)

    # Niche breakdown
    niche_chart = create_niche_breakdown_chart(data)

    # Spend chart
    spend_chart = create_spend_chart(data)

    # Platform sections
    platform_sections = ""
    for platform, metrics_list in data.metrics_by_platform.items():
        platform_sections += generate_platform_section(platform, metrics_list)

    # Platform tab buttons
    platform_tabs = ""
    for platform in data.metrics_by_platform.keys():
        color = PLATFORM_COLORS.get(platform, "#666")
        platform_tabs += f"""
        <button class="platform-tab" data-platform="{platform}" style="--platform-color: {color}">
            {platform.title()}
        </button>"""

    num_platforms = len(data.metrics_by_platform)
    num_accounts = sum(len(m) for m in data.metrics_by_platform.values())

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Unified Analytics Dashboard</title>
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
        h1 {{ color: #333; margin-bottom: 5px; }}
        h2 {{ color: #555; border-bottom: 2px solid #ddd; padding-bottom: 10px; margin-top: 30px; }}
        h3 {{ margin: 0; color: #333; }}
        h4 {{ margin: 0 0 15px 0; color: #555; }}
        .meta {{ color: #666; margin-bottom: 25px; }}

        /* View Toggle */
        .view-toggle {{
            display: flex;
            gap: 10px;
            margin-bottom: 25px;
        }}
        .view-btn {{
            padding: 12px 28px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 15px;
            font-weight: 600;
            background: white;
            color: #666;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: all 0.2s;
        }}
        .view-btn:hover {{ background: #f0f0f0; }}
        .view-btn.active {{
            background: #333;
            color: white;
        }}

        /* Platform Tabs */
        .platform-tabs {{
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .platform-tab {{
            padding: 10px 20px;
            border: 2px solid var(--platform-color);
            border-radius: 6px;
            background: white;
            color: var(--platform-color);
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .platform-tab:hover, .platform-tab.active {{
            background: var(--platform-color);
            color: white;
        }}

        /* Stats */
        .stats-grid {{
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

        /* Charts */
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .chart-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .chart-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-top: 20px;
        }}

        /* Platform Sections */
        .platform-section {{
            margin-bottom: 30px;
        }}
        .platform-header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .platform-summary {{
            display: flex;
            gap: 20px;
            color: #666;
            font-size: 14px;
        }}
        .platform-summary span {{
            background: #f5f5f5;
            padding: 5px 12px;
            border-radius: 4px;
        }}

        /* Account Cards */
        .account-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }}
        .account-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .account-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }}
        .account-name {{
            font-weight: 600;
            font-size: 16px;
        }}
        .niche-badge {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }}
        .error-badge {{
            background: #ffebee;
            color: #c62828;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
        }}
        .account-metrics {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
        }}
        .metric {{
            text-align: center;
        }}
        .metric-value {{
            font-size: 18px;
            font-weight: bold;
            color: #333;
        }}
        .metric-label {{
            font-size: 11px;
            color: #666;
        }}
        .spend-row {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 14px;
        }}

        /* View Content */
        .view-content {{
            display: none;
        }}
        .view-content.active {{
            display: block;
        }}

        /* Filters for split view */
        .split-filters {{
            display: none;
            margin-bottom: 20px;
        }}
        .split-filters.active {{
            display: block;
        }}

        .footer {{
            margin-top: 30px;
            color: #999;
            font-size: 12px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <h1>Unified Analytics Dashboard</h1>
    <div class="meta">
        {num_platforms} platforms | {num_accounts} accounts | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
    </div>

    <!-- View Toggle -->
    <div class="view-toggle">
        <button class="view-btn active" onclick="showView('aggregate')">Aggregate View</button>
        <button class="view-btn" onclick="showView('split')">Platform Split</button>
    </div>

    <!-- Aggregate View -->
    <div id="aggregate-view" class="view-content active">
        <div class="stats-grid">{agg_stats}</div>

        <div class="charts-grid">
            <div class="chart-card">{platform_chart}</div>
            <div class="chart-card">{niche_chart}</div>
        </div>

        {f'<div class="chart-card" style="max-width: 400px;">{spend_chart}</div>' if spend_chart else ''}
    </div>

    <!-- Split View -->
    <div id="split-view" class="view-content">
        <div class="platform-tabs" id="platform-tabs">
            <button class="platform-tab active" data-platform="all" style="--platform-color: #333">
                All Platforms
            </button>
            {platform_tabs}
        </div>

        <div id="platforms-container">
            {platform_sections}
        </div>
    </div>

    <div class="footer">Unified Analytics Dashboard</div>

    <script>
        function showView(view) {{
            document.querySelectorAll('.view-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.view-btn').forEach(el => el.classList.remove('active'));

            document.getElementById(view + '-view').classList.add('active');
            event.target.classList.add('active');

            window.dispatchEvent(new Event('resize'));
        }}

        // Platform tab filtering
        document.querySelectorAll('.platform-tab').forEach(tab => {{
            tab.addEventListener('click', function() {{
                document.querySelectorAll('.platform-tab').forEach(t => t.classList.remove('active'));
                this.classList.add('active');

                const platform = this.dataset.platform;
                document.querySelectorAll('.platform-section').forEach(section => {{
                    if (platform === 'all' || section.id === 'platform_' + platform) {{
                        section.style.display = 'block';
                    }} else {{
                        section.style.display = 'none';
                    }}
                }});

                window.dispatchEvent(new Event('resize'));
            }});
        }});
    </script>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(description="Generate unified multi-platform analytics dashboard")
    parser.add_argument("--days", type=int, default=14, help="Number of days (default: 14)")
    parser.add_argument("--open", action="store_true", help="Open report in browser")
    parser.add_argument("--platform", help="Only fetch specific platform")
    args = parser.parse_args()

    config = load_config()

    # Filter to specific platform if requested
    if args.platform:
        if args.platform in config.get("platforms", {}):
            config["platforms"] = {args.platform: config["platforms"][args.platform]}
        else:
            print(f"Platform '{args.platform}' not found in config")
            sys.exit(1)

    print("Fetching metrics from all platforms...\n")
    data = fetch_all_metrics(config, args.days)

    if not data.metrics_by_platform:
        print("\nNo data collected from any platform")
        sys.exit(1)

    print("\nGenerating dashboard...")
    html = generate_html_report(data, config)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = OUTPUT_DIR / f"unified_dashboard_{timestamp}.html"
    output_file.write_text(html)

    print(f"Dashboard saved: {output_file}")

    if args.open:
        import webbrowser
        webbrowser.open(f"file://{output_file.absolute()}")


if __name__ == "__main__":
    main()
