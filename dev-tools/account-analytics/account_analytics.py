"""Pinterest Account Analytics - With 1w/2w/4w toggle."""

import argparse
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import plotly.graph_objects as go
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from pinterest_auth.auth import PINTEREST_API_URL, get_access_token

from config import load_config

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_DAYS = 28  # Fetch 4 weeks of data
PERIODS = {"1w": 7, "2w": 14, "4w": 28}
COLORS = {"organic": "#1f77b4", "paid": "#ff7f0e"}


def fetch_account_info(access_token: str) -> dict:
    """Fetch account info to get account name."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{PINTEREST_API_URL}/user_account", headers=headers)
    return response.json() if response.ok else {}


def fetch_all_pins(access_token: str) -> list[dict]:
    """Fetch all pins from the account."""
    pins = []
    headers = {"Authorization": f"Bearer {access_token}"}
    bookmark = None

    while True:
        params = {"page_size": 100}
        if bookmark:
            params["bookmark"] = bookmark

        response = requests.get(
            f"{PINTEREST_API_URL}/pins", headers=headers, params=params
        )
        if not response.ok:
            break

        data = response.json()
        pins.extend(data.get("items", []))
        bookmark = data.get("bookmark")
        if not bookmark:
            break

    return pins


def fetch_pin_analytics(access_token: str, pin_id: str) -> dict | None:
    """Fetch analytics for a single pin (28 days)."""
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=MAX_DAYS - 1)

    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "metric_types": "IMPRESSION,SAVE,PIN_CLICK,OUTBOUND_CLICK",
    }

    response = requests.get(
        f"{PINTEREST_API_URL}/pins/{pin_id}/analytics", headers=headers, params=params
    )
    return response.json() if response.ok else None


def collect_organic_data(access_token: str, pins: list[dict]) -> tuple[dict, dict]:
    """Collect organic analytics for all pins. Returns (pin_daily, daily_totals)."""
    pin_daily = {}  # {pin_id: {"title": ..., "link": ..., dates: {date: {metrics}}}}
    daily_totals = {}

    for i, pin in enumerate(pins):
        pin_id = pin.get("id")
        print(f"  [{i+1}/{len(pins)}] {pin_id}")

        analytics = fetch_pin_analytics(access_token, pin_id)
        if not analytics:
            time.sleep(0.3)
            continue

        daily = analytics.get("all", {}).get("daily_metrics", [])
        pin_daily[pin_id] = {
            "title": pin.get("title", "Untitled"),
            "link": pin.get("link", ""),
            "dates": {},
        }

        for day in daily:
            date = day.get("date", "")
            metrics = day.get("metrics", {})
            pin_daily[pin_id]["dates"][date] = {
                "IMPRESSION": metrics.get("IMPRESSION", 0),
                "SAVE": metrics.get("SAVE", 0),
                "OUTBOUND_CLICK": metrics.get("OUTBOUND_CLICK", 0),
            }

            if date not in daily_totals:
                daily_totals[date] = {"IMPRESSION": 0, "SAVE": 0, "OUTBOUND_CLICK": 0}
            for m in daily_totals[date]:
                daily_totals[date][m] += metrics.get(m, 0)

        time.sleep(0.3)

    return pin_daily, daily_totals


def fetch_ad_accounts(access_token: str) -> list[dict]:
    """Fetch ad accounts."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{PINTEREST_API_URL}/ad_accounts", headers=headers)
    return response.json().get("items", []) if response.ok else []


def fetch_campaigns(access_token: str, ad_account_id: str) -> list[dict]:
    """Fetch all campaigns for an ad account."""
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"entity_statuses": "ACTIVE,PAUSED,ARCHIVED"}
    response = requests.get(
        f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns",
        headers=headers,
        params=params,
    )
    return response.json().get("items", []) if response.ok else []


def fetch_campaign_analytics(
    access_token: str, ad_account_id: str, campaign_ids: list[str]
) -> dict:
    """Fetch spend analytics for campaigns (last 7 days)."""
    if not campaign_ids:
        return {}

    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=6)

    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "campaign_ids": ",".join(campaign_ids),
        "columns": "CAMPAIGN_NAME,TOTAL_IMPRESSION,TOTAL_CLICKTHROUGH,SPEND_IN_DOLLAR",
        "granularity": "TOTAL",
    }

    response = requests.get(
        f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/campaigns/analytics",
        headers=headers,
        params=params,
    )

    if not response.ok:
        return {}

    result = {}
    for item in response.json():
        cid = item.get("CAMPAIGN_ID")
        if cid:
            result[cid] = {
                "impressions": item.get("TOTAL_IMPRESSION", 0) or 0,
                "clicks": item.get("TOTAL_CLICKTHROUGH", 0) or 0,
                "spend": item.get("SPEND_IN_DOLLAR", 0) or 0,
            }
    return result


def _parse_timestamp(value) -> datetime | None:
    """Parse a Pinterest API timestamp (unix epoch int/str or ISO string)."""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    if isinstance(value, str):
        if value.isdigit():
            return datetime.fromtimestamp(int(value))
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    return None


def collect_recently_ended(access_token: str, ad_account_id: str) -> list[dict]:
    """Find campaigns that ended in the last 48 hours with reason."""
    campaigns = fetch_campaigns(access_token, ad_account_id)
    if not campaigns:
        return []

    cutoff = datetime.now() - timedelta(hours=48)
    candidates = []

    for c in campaigns:
        end_time_raw = c.get("end_time")
        status = c.get("status", "")
        lifetime_cap = c.get("lifetime_spend_cap", 0) / 1_000_000  # microdollars -> dollars

        ended = False
        end_dt = None

        # Check if campaign has an end_time in the last 48 hours
        # Pinterest API returns timestamps as unix epoch (int) or ISO string
        if end_time_raw:
            try:
                end_dt = _parse_timestamp(end_time_raw)
                if end_dt and cutoff <= end_dt <= datetime.now():
                    ended = True
            except (ValueError, TypeError, OSError):
                pass

        # Check if campaign was recently paused/archived (no end_time but status changed)
        if not ended and status in ("PAUSED", "ARCHIVED"):
            updated_raw = c.get("updated_time")
            if updated_raw:
                try:
                    updated_dt = _parse_timestamp(updated_raw)
                    if updated_dt and cutoff <= updated_dt <= datetime.now():
                        ended = True
                        end_dt = updated_dt
                except (ValueError, TypeError, OSError):
                    pass

        if not ended:
            continue

        candidates.append({
            "id": c.get("id"),
            "name": c.get("name", "Unknown"),
            "status": status,
            "end_time": end_dt,
            "lifetime_spend_cap": lifetime_cap,
            "daily_spend_cap": c.get("daily_spend_cap", 0) / 1_000_000,
        })

    if not candidates:
        return []

    # Fetch spend analytics to determine reason
    campaign_ids = [c["id"] for c in candidates]
    analytics = fetch_campaign_analytics(access_token, ad_account_id, campaign_ids)

    results = []
    for c in candidates:
        spend = analytics.get(c["id"], {}).get("spend", 0)
        impressions = analytics.get(c["id"], {}).get("impressions", 0)
        clicks = analytics.get(c["id"], {}).get("clicks", 0)

        # Determine reason
        if c["lifetime_spend_cap"] > 0 and spend >= c["lifetime_spend_cap"] * 0.95:
            reason = "Budget Exhausted"
        else:
            reason = "Campaign Ended"

        results.append({
            "name": c["name"],
            "status": c["status"],
            "ended_at": c["end_time"].strftime("%Y-%m-%d %H:%M") if c["end_time"] else "Unknown",
            "reason": reason,
            "spend": spend,
            "lifetime_cap": c["lifetime_spend_cap"],
            "impressions": impressions,
            "clicks": clicks,
        })

    return results


def fetch_ads(access_token: str, ad_account_id: str) -> list[dict]:
    """Fetch all ads."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/ads", headers=headers
    )
    return response.json().get("items", []) if response.ok else []


def fetch_ad_analytics(
    access_token: str, ad_account_id: str, ad_ids: list[str]
) -> list[dict]:
    """Fetch analytics for ads (28 days)."""
    if not ad_ids:
        return []

    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=MAX_DAYS - 1)

    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "ad_ids": ",".join(ad_ids),
        "columns": "TOTAL_IMPRESSION,TOTAL_CLICKTHROUGH,REPIN_1,SPEND_IN_DOLLAR,CTR,ECPC_IN_DOLLAR",
        "granularity": "DAY",
    }

    response = requests.get(
        f"{PINTEREST_API_URL}/ad_accounts/{ad_account_id}/ads/analytics",
        headers=headers,
        params=params,
    )

    return response.json() if response.ok else []


def collect_paid_data(access_token: str, ad_account_id: str) -> tuple[dict, dict]:
    """Collect paid ads analytics. Returns (ad_daily, daily_totals)."""
    ads = fetch_ads(access_token, ad_account_id)
    if not ads:
        return {}, {}

    ad_map = {a["id"]: a for a in ads}
    ad_ids = list(ad_map.keys())

    analytics = fetch_ad_analytics(access_token, ad_account_id, ad_ids)

    ad_daily = {}  # {ad_id: {"name": ..., "pin_id": ..., dates: {date: {metrics}}}}
    daily_totals = {}

    for row in analytics:
        ad_id = row.get("AD_ID")
        date = row.get("DATE", "")

        if ad_id not in ad_daily:
            ad_info = ad_map.get(ad_id, {})
            ad_daily[ad_id] = {
                "name": ad_info.get("name", "Unknown"),
                "pin_id": ad_info.get("pin_id", ""),
                "dates": {},
            }

        imp = row.get("TOTAL_IMPRESSION", 0) or 0
        clk = row.get("TOTAL_CLICKTHROUGH", 0) or 0
        sav = row.get("REPIN_1", 0) or 0
        spd = row.get("SPEND_IN_DOLLAR", 0) or 0

        if date:
            ad_daily[ad_id]["dates"][date] = {
                "IMPRESSION": imp,
                "CLICK": clk,
                "SAVE": sav,
                "SPEND": spd,
            }

            if date not in daily_totals:
                daily_totals[date] = {
                    "IMPRESSION": 0,
                    "CLICK": 0,
                    "SAVE": 0,
                    "SPEND": 0,
                }
            daily_totals[date]["IMPRESSION"] += imp
            daily_totals[date]["CLICK"] += clk
            daily_totals[date]["SAVE"] += sav
            daily_totals[date]["SPEND"] += spd

    return ad_daily, daily_totals


def filter_daily_by_period(daily: dict, days: int) -> dict:
    """Filter daily data to last N days."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return {d: v for d, v in daily.items() if d >= cutoff}


def calc_totals_from_daily(daily: dict, is_paid: bool = False) -> dict:
    """Calculate totals from daily data."""
    if is_paid:
        impressions = sum(v.get("IMPRESSION", 0) for v in daily.values())
        clicks = sum(v.get("CLICK", 0) for v in daily.values())
        saves = sum(v.get("SAVE", 0) for v in daily.values())
        spend = sum(v.get("SPEND", 0) for v in daily.values())
    else:
        impressions = sum(v.get("IMPRESSION", 0) for v in daily.values())
        clicks = sum(v.get("OUTBOUND_CLICK", 0) for v in daily.values())
        saves = sum(v.get("SAVE", 0) for v in daily.values())
        spend = 0

    ctr = (clicks / impressions * 100) if impressions > 0 else 0
    cpc = (spend / clicks) if clicks > 0 else 0

    return {
        "impressions": impressions,
        "clicks": clicks,
        "saves": saves,
        "spend": spend,
        "ctr": ctr,
        "cpc": cpc,
    }


def organic_leaderboard_for_period(pin_daily: dict, days: int) -> list[dict]:
    """Compute organic leaderboard from per-pin daily data filtered by period."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    results = []
    for pin_id, info in pin_daily.items():
        totals = {"IMPRESSION": 0, "SAVE": 0, "OUTBOUND_CLICK": 0}
        for date, metrics in info["dates"].items():
            if date >= cutoff:
                for m in totals:
                    totals[m] += metrics.get(m, 0)
        ctr = (
            (totals["OUTBOUND_CLICK"] / totals["IMPRESSION"] * 100)
            if totals["IMPRESSION"] > 0
            else 0
        )
        results.append(
            {
                "pin_id": pin_id,
                "title": info.get("title", "Untitled"),
                "impressions": totals["IMPRESSION"],
                "clicks": totals["OUTBOUND_CLICK"],
                "saves": totals["SAVE"],
                "ctr": ctr,
            }
        )
    return results


def paid_leaderboard_for_period(ad_daily: dict, days: int) -> list[dict]:
    """Compute paid leaderboard from per-ad daily data filtered by period."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    results = []
    for ad_id, info in ad_daily.items():
        totals = {"IMPRESSION": 0, "CLICK": 0, "SAVE": 0, "SPEND": 0}
        for date, metrics in info["dates"].items():
            if date >= cutoff:
                for m in totals:
                    totals[m] += metrics.get(m, 0)
        ctr = (
            (totals["CLICK"] / totals["IMPRESSION"] * 100)
            if totals["IMPRESSION"] > 0
            else 0
        )
        cpc = (totals["SPEND"] / totals["CLICK"]) if totals["CLICK"] > 0 else 0
        results.append(
            {
                "ad_id": ad_id,
                "name": info.get("name", "Unknown"),
                "pin_id": info.get("pin_id", ""),
                "impressions": totals["IMPRESSION"],
                "clicks": totals["CLICK"],
                "saves": totals["SAVE"],
                "spend": totals["SPEND"],
                "ctr": ctr,
                "cpc": cpc,
            }
        )
    return results


def create_comparison_chart(
    organic_daily: dict, paid_daily: dict, metric: str, title: str, chart_id: str
) -> str:
    """Create chart comparing organic vs paid."""
    fig = go.Figure()

    all_dates = sorted(set(list(organic_daily.keys()) + list(paid_daily.keys())))
    if not all_dates:
        return "<p>No data</p>"

    organic_values = [organic_daily.get(d, {}).get(metric, 0) for d in all_dates]
    fig.add_trace(
        go.Scatter(
            x=all_dates,
            y=organic_values,
            mode="lines+markers",
            name="Organic",
            line=dict(color=COLORS["organic"], width=2),
        )
    )

    paid_metric = {
        "IMPRESSION": "IMPRESSION",
        "OUTBOUND_CLICK": "CLICK",
        "SAVE": "SAVE",
    }.get(metric, metric)
    paid_values = [paid_daily.get(d, {}).get(paid_metric, 0) for d in all_dates]
    fig.add_trace(
        go.Scatter(
            x=all_dates,
            y=paid_values,
            mode="lines+markers",
            name="Paid",
            line=dict(color=COLORS["paid"], width=2),
        )
    )

    fig.update_layout(
        title=title,
        xaxis=dict(
            tickangle=-45,
            showspikes=True,
            spikemode="across",
            spikethickness=1,
            spikecolor="#999",
            spikedash="dot",
        ),
        yaxis=dict(gridcolor="#eee"),
        plot_bgcolor="white",
        height=280,
        margin=dict(l=50, r=30, t=50, b=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x",
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=chart_id)


def create_single_chart(
    daily: dict,
    metric: str,
    title: str,
    chart_id: str,
    color: str,
    is_currency: bool = False,
) -> str:
    """Create single metric chart."""
    dates = sorted(daily.keys())
    if not dates:
        return "<p>No data</p>"

    values = [daily.get(d, {}).get(metric, 0) for d in dates]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            fill="tozeroy",
            line=dict(color=color, width=2),
        )
    )

    fig.update_layout(
        title=title,
        xaxis=dict(
            tickangle=-45,
            showspikes=True,
            spikemode="across",
            spikethickness=1,
            spikecolor="#999",
            spikedash="dot",
        ),
        yaxis=dict(gridcolor="#eee", tickprefix="$" if is_currency else ""),
        plot_bgcolor="white",
        height=280,
        margin=dict(l=50, r=30, t=50, b=60),
        showlegend=False,
        hovermode="x",
    )

    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=chart_id)


def generate_period_content(
    period_key: str,
    days: int,
    organic_daily: dict,
    paid_daily: dict,
    pin_daily: dict,
    ad_daily: dict,
    recently_ended: list[dict] | None = None,
) -> str:
    """Generate content for a specific time period."""
    # Filter daily data
    org_daily = filter_daily_by_period(organic_daily, days)
    pd_daily = filter_daily_by_period(paid_daily, days)

    # Calculate totals
    org_totals = calc_totals_from_daily(org_daily, is_paid=False)
    pd_totals = calc_totals_from_daily(pd_daily, is_paid=True)

    total_impressions = org_totals["impressions"] + pd_totals["impressions"]
    total_clicks = org_totals["clicks"] + pd_totals["clicks"]
    total_saves = org_totals["saves"] + pd_totals["saves"]
    total_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0

    # Generate charts
    impressions_chart = create_comparison_chart(
        org_daily, pd_daily, "IMPRESSION", "Impressions", f"chart_imp_{period_key}"
    )
    clicks_chart = create_comparison_chart(
        org_daily, pd_daily, "OUTBOUND_CLICK", "Clicks", f"chart_clk_{period_key}"
    )
    saves_chart = create_comparison_chart(
        org_daily, pd_daily, "SAVE", "Saves", f"chart_sav_{period_key}"
    )

    # CTR chart
    ctr_org = {
        d: {
            "CTR": (
                (v.get("OUTBOUND_CLICK", 0) / v.get("IMPRESSION", 1) * 100)
                if v.get("IMPRESSION", 0) > 0
                else 0
            )
        }
        for d, v in org_daily.items()
    }
    ctr_pd = {
        d: {
            "CTR": (
                (v.get("CLICK", 0) / v.get("IMPRESSION", 1) * 100)
                if v.get("IMPRESSION", 0) > 0
                else 0
            )
        }
        for d, v in pd_daily.items()
    }
    ctr_chart = create_comparison_chart(
        ctr_org, ctr_pd, "CTR", "CTR (%)", f"chart_ctr_{period_key}"
    )

    # CPC and Spend charts (paid only)
    cpc_daily = {
        d: {
            "CPC": (
                (v.get("SPEND", 0) / v.get("CLICK", 1)) if v.get("CLICK", 0) > 0 else 0
            )
        }
        for d, v in pd_daily.items()
    }
    cpc_chart = create_single_chart(
        cpc_daily,
        "CPC",
        "CPC ($) - Paid",
        f"chart_cpc_{period_key}",
        COLORS["paid"],
        is_currency=True,
    )
    spend_chart = create_single_chart(
        pd_daily,
        "SPEND",
        "Spend ($) - Paid",
        f"chart_spd_{period_key}",
        COLORS["paid"],
        is_currency=True,
    )

    # Leaderboards filtered by period
    paid_sorted = sorted(
        paid_leaderboard_for_period(ad_daily, days),
        key=lambda x: x["ctr"],
        reverse=True,
    )[:10]
    paid_rows = ""
    for r in paid_sorted:
        link = f"https://pinterest.com/pin/{r['pin_id']}" if r["pin_id"] else "#"
        paid_rows += f"""<tr>
            <td title="{r['name']}">{r['name'][:40]}</td>
            <td class="num">{r['impressions']:,}</td>
            <td class="num">{r['clicks']:,}</td>
            <td class="num">{r['ctr']:.2f}%</td>
            <td class="num">${r['spend']:.2f}</td>
            <td><a href="{link}" target="_blank">View</a></td>
        </tr>"""

    organic_sorted = sorted(
        organic_leaderboard_for_period(pin_daily, days),
        key=lambda x: x["ctr"],
        reverse=True,
    )[:10]
    organic_rows = ""
    for r in organic_sorted:
        link = f"https://pinterest.com/pin/{r['pin_id']}"
        organic_rows += f"""<tr>
            <td title="{r['title']}">{r['title'][:40] if r['title'] else 'Untitled'}</td>
            <td class="num">{r['impressions']:,}</td>
            <td class="num">{r['clicks']:,}</td>
            <td class="num">{r['saves']:,}</td>
            <td class="num">{r['ctr']:.2f}%</td>
            <td><a href="{link}" target="_blank">View</a></td>
        </tr>"""

    return f"""
    <div class="summary">
        <div class="stat">
            <div class="stat-value">{total_impressions:,}</div>
            <div class="stat-label">Impressions</div>
            <div class="stat-breakdown">Organic: {org_totals['impressions']:,} | Paid: {pd_totals['impressions']:,}</div>
        </div>
        <div class="stat">
            <div class="stat-value">{total_clicks:,}</div>
            <div class="stat-label">Clicks</div>
            <div class="stat-breakdown">Organic: {org_totals['clicks']:,} | Paid: {pd_totals['clicks']:,}</div>
        </div>
        <div class="stat">
            <div class="stat-value">{total_ctr:.2f}%</div>
            <div class="stat-label">CTR</div>
            <div class="stat-breakdown">Organic: {org_totals['ctr']:.2f}% | Paid: {pd_totals['ctr']:.2f}%</div>
        </div>
        <div class="stat">
            <div class="stat-value">{total_saves:,}</div>
            <div class="stat-label">Saves</div>
            <div class="stat-breakdown">Organic: {org_totals['saves']:,} | Paid: {pd_totals['saves']:,}</div>
        </div>
        <div class="stat">
            <div class="stat-value">${pd_totals['spend']:.2f}</div>
            <div class="stat-label">Spend</div>
            <div class="stat-breakdown">Paid only</div>
        </div>
        <div class="stat">
            <div class="stat-value">${pd_totals['cpc']:.2f}</div>
            <div class="stat-label">CPC</div>
            <div class="stat-breakdown">Paid only</div>
        </div>
    </div>

    <h2>Trends</h2>
    <div class="source-toggle">
        <button class="source-btn active" data-source="both" onclick="toggleSource('both', '{period_key}')">Both</button>
        <button class="source-btn" data-source="organic" onclick="toggleSource('organic', '{period_key}')">
            <span class="legend-dot" style="background:{COLORS['organic']}"></span> Organic
        </button>
        <button class="source-btn" data-source="paid" onclick="toggleSource('paid', '{period_key}')">
            <span class="legend-dot" style="background:{COLORS['paid']}"></span> Paid
        </button>
    </div>
    <div class="charts">
        <div class="chart">{impressions_chart}</div>
        <div class="chart">{clicks_chart}</div>
        <div class="chart">{ctr_chart}</div>
        <div class="chart">{saves_chart}</div>
        <div class="chart">{cpc_chart}</div>
        <div class="chart">{spend_chart}</div>
    </div>

    <h2>Paid Ads Leaderboard (Top 10 by CTR)</h2>
    <table>
        <thead><tr><th>Ad Name</th><th class="num">Impressions</th><th class="num">Clicks</th><th class="num">CTR</th><th class="num">Spend</th><th>Link</th></tr></thead>
        <tbody>{paid_rows if paid_rows else '<tr><td colspan="6">No paid ads data</td></tr>'}</tbody>
    </table>

    {generate_recently_ended_html(recently_ended or [])}

    <h2>Organic Leaderboard (Top 10 by Impressions)</h2>
    <table>
        <thead><tr><th>Pin Title</th><th class="num">Impressions</th><th class="num">Clicks</th><th class="num">Saves</th><th class="num">CTR</th><th>Link</th></tr></thead>
        <tbody>{organic_rows if organic_rows else '<tr><td colspan="6">No organic data</td></tr>'}</tbody>
    </table>
    """


def generate_recently_ended_html(recently_ended: list[dict]) -> str:
    """Generate HTML section for recently ended campaigns."""
    if not recently_ended:
        return ""

    rows = ""
    for c in recently_ended:
        reason_class = "reason-budget" if c["reason"] == "Budget Exhausted" else "reason-ended"
        cap_display = f"${c['lifetime_cap']:.2f}" if c["lifetime_cap"] > 0 else "-"
        rows += f"""<tr>
            <td title="{c['name']}">{c['name'][:45]}</td>
            <td>{c['status']}</td>
            <td>{c['ended_at']}</td>
            <td><span class="reason-badge {reason_class}">{c['reason']}</span></td>
            <td class="num">${c['spend']:.2f}</td>
            <td class="num">{cap_display}</td>
            <td class="num">{c['impressions']:,}</td>
            <td class="num">{c['clicks']:,}</td>
        </tr>"""

    return f"""
    <div class="recently-ended">
        <h2>Recently Ended (Last 48 Hours)</h2>
        <table>
            <thead><tr>
                <th>Campaign</th><th>Status</th><th>Ended At</th><th>Reason</th>
                <th class="num">Spend</th><th class="num">Lifetime Cap</th>
                <th class="num">Impressions</th><th class="num">Clicks</th>
            </tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    """


def generate_html(
    account_name: str,
    pin_daily: dict,
    organic_daily: dict,
    ad_daily: dict,
    paid_daily: dict,
    recently_ended: list[dict] | None = None,
) -> str:
    """Generate HTML report with period toggle."""

    # Generate content for each period
    period_contents = ""
    for period_key, days in PERIODS.items():
        is_default = period_key == "1w"
        content = generate_period_content(
            period_key, days, organic_daily, paid_daily, pin_daily, ad_daily, recently_ended
        )
        period_contents += f'<div id="period_{period_key}" class="period-content {"active" if is_default else ""}">{content}</div>\n'

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{account_name} - Pinterest Analytics</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{ color: #333; margin-bottom: 5px; }}
        .meta {{ color: #666; margin-bottom: 15px; }}
        h2 {{ color: #555; border-bottom: 2px solid #ddd; padding-bottom: 10px; margin-top: 30px; }}

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
            padding: 10px 20px;
            border: none;
            background: transparent;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            color: #666;
            transition: all 0.2s;
        }}
        .period-btn:hover {{ background: #f0f0f0; }}
        .period-btn.active {{
            background: #1f77b4;
            color: white;
        }}
        .period-content {{ display: none; }}
        .period-content.active {{ display: block; }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(6, 1fr);
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
        .stat-value {{ font-size: 28px; font-weight: bold; color: #333; }}
        .stat-label {{ color: #666; font-size: 13px; margin-top: 5px; }}
        .stat-breakdown {{ font-size: 11px; color: #999; margin-top: 8px; }}

        .charts {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .chart {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .source-toggle {{
            display: flex;
            gap: 5px;
            justify-content: center;
            margin-bottom: 20px;
            background: white;
            padding: 5px;
            border-radius: 8px;
            width: fit-content;
            margin-left: auto;
            margin-right: auto;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .source-btn {{
            padding: 8px 18px;
            border: none;
            background: transparent;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            color: #666;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .source-btn:hover {{ background: #f0f0f0; }}
        .source-btn.active {{ background: #1f77b4; color: white; }}
        .source-btn.active .legend-dot {{ border: 1px solid white; }}
        .legend-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{ background: #fafafa; font-weight: 600; color: #555; }}
        .num {{ text-align: right; font-weight: 500; }}
        a {{ color: #1f77b4; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}

        .footer {{ margin-top: 30px; color: #999; font-size: 12px; text-align: center; }}

        .recently-ended {{ margin-bottom: 30px; }}
        .reason-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            white-space: nowrap;
        }}
        .reason-budget {{
            background: #fff3cd;
            color: #856404;
        }}
        .reason-ended {{
            background: #d4edda;
            color: #155724;
        }}
    </style>
</head>
<body>
    <h1>{account_name} Pinterest Analytics</h1>
    <div class="meta">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>

    <div class="period-toggle">
        <button class="period-btn active" onclick="showPeriod('1w')">1 Week</button>
        <button class="period-btn" onclick="showPeriod('2w')">2 Weeks</button>
        <button class="period-btn" onclick="showPeriod('4w')">4 Weeks</button>
    </div>

    {period_contents}

    <div class="footer">Pinterest Account Analytics</div>

    <script>
        function showPeriod(period) {{
            document.querySelectorAll('.period-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.period-btn').forEach(el => el.classList.remove('active'));
            document.getElementById('period_' + period).classList.add('active');
            event.target.classList.add('active');
            window.dispatchEvent(new Event('resize'));
        }}

        function toggleSource(source, periodKey) {{
            // Update button state within the active period
            var container = document.getElementById('period_' + periodKey);
            container.querySelectorAll('.source-btn').forEach(function(b) {{ b.classList.remove('active'); }});
            container.querySelector('[data-source="' + source + '"]').classList.add('active');

            // Chart prefixes for comparison charts (have Organic/Paid traces)
            var compPrefixes = ['chart_imp_', 'chart_clk_', 'chart_ctr_', 'chart_sav_'];
            compPrefixes.forEach(function(prefix) {{
                var divId = prefix + periodKey;
                var gd = document.getElementById(divId);
                if (!gd || !gd.data) return;
                var update = {{}};
                gd.data.forEach(function(trace, i) {{
                    if (trace.name === 'Organic') {{
                        update['visible'] = update['visible'] || [];
                        update['visible'][i] = (source === 'both' || source === 'organic');
                    }} else if (trace.name === 'Paid') {{
                        update['visible'] = update['visible'] || [];
                        update['visible'][i] = (source === 'both' || source === 'paid');
                    }}
                }});
                if (update['visible']) {{
                    Plotly.restyle(gd, {{'visible': update['visible']}});
                }}
            }});
        }}

        // Synchronized crosshair across all charts
        function setupCrosshairSync() {{
            var allChartIds = [];
            document.querySelectorAll('.plotly-graph-div').forEach(function(el) {{
                if (el.id) allChartIds.push(el.id);
            }});

            allChartIds.forEach(function(srcId) {{
                var srcEl = document.getElementById(srcId);
                if (!srcEl) return;

                srcEl.on('plotly_hover', function(data) {{
                    if (!data.points || !data.points.length) return;
                    var xVal = data.points[0].x;
                    var period = srcId.split('_').pop();
                    allChartIds.forEach(function(tgtId) {{
                        if (tgtId === srcId) return;
                        if (tgtId.split('_').pop() !== period) return;
                        var tgtEl = document.getElementById(tgtId);
                        if (!tgtEl || !tgtEl.data) return;
                        var pts = [];
                        tgtEl.data.forEach(function(trace, ti) {{
                            if (trace.visible === false || trace.visible === 'legendonly') return;
                            if (!trace.x) return;
                            for (var xi = 0; xi < trace.x.length; xi++) {{
                                if (trace.x[xi] === xVal) {{
                                    pts.push({{curveNumber: ti, pointNumber: xi}});
                                    break;
                                }}
                            }}
                        }});
                        if (pts.length) Plotly.Fx.hover(tgtId, pts);
                    }});
                }});

                srcEl.on('plotly_unhover', function() {{
                    var period = srcId.split('_').pop();
                    allChartIds.forEach(function(tgtId) {{
                        if (tgtId === srcId) return;
                        if (tgtId.split('_').pop() !== period) return;
                        Plotly.Fx.unhover(tgtId);
                    }});
                }});
            }});
        }}

        // Run sync setup after charts render
        window.addEventListener('load', function() {{
            setTimeout(setupCrosshairSync, 500);
        }});
    </script>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(description="Pinterest Account Analytics")
    parser.add_argument("--limit", type=int, help="Limit pins to analyze")
    parser.add_argument("--open", action="store_true", help="Open in browser")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent / "data" / "input.json",
        help="Path to config data file (default: data/input.json)",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    print(f"Niche: {config.niche} | Tenant: {config.tenant}")

    try:
        access_token = get_access_token(tenant=config.tenant, niche=config.niche)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("Fetching account info...")
    account_info = fetch_account_info(access_token)
    username = account_info.get("username", "Pinterest Account")
    account_name = f"{config.brand_name} - {username}" if config.brand_name else username

    print("Fetching pins...")
    pins = fetch_all_pins(access_token)
    if args.limit:
        pins = pins[: args.limit]
    print(f"Found {len(pins)} pins")

    print("Fetching organic analytics (28 days)...")
    pin_daily, organic_daily = collect_organic_data(access_token, pins)
    print(f"Collected organic data for {len(pin_daily)} pins")

    print("Fetching paid ads data...")
    ad_accounts = fetch_ad_accounts(access_token)
    ad_daily, paid_daily = {}, {}
    recently_ended = []
    if ad_accounts:
        ad_account_id = ad_accounts[0]["id"]
        ad_daily, paid_daily = collect_paid_data(access_token, ad_account_id)
        print(f"Collected paid data for {len(ad_daily)} ads")

        print("Checking for recently ended campaigns (last 48h)...")
        recently_ended = collect_recently_ended(access_token, ad_account_id)
        print(f"Found {len(recently_ended)} recently ended campaign(s)")
    else:
        print("No ad accounts found")

    html = generate_html(account_name, pin_daily, organic_daily, ad_daily, paid_daily, recently_ended)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = OUTPUT_DIR / f"account_analytics_{timestamp}.html"
    output_file.write_text(html)

    print(f"\nReport saved: {output_file}")

    if args.open:
        import webbrowser

        webbrowser.open(f"file://{output_file.absolute()}")


if __name__ == "__main__":
    main()
