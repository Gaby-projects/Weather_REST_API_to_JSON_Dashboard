from pathlib import Path

MAX_TEMP_SCALE = 40  # °C used as the 100% reference for the bar visualization


def _latest_snapshot(
    history: list[dict], city_order: list[str]
) -> tuple[str | None, dict[str, list[dict]]]:
    if not history:
        return None, {}

    latest_fetched_at = max(record["fetched_at"] for record in history)
    latest_records = [r for r in history if r["fetched_at"] == latest_fetched_at]

    by_city = {city: [] for city in city_order}
    for record in latest_records:
        by_city.setdefault(record["city"], []).append(record)
    for records in by_city.values():
        records.sort(key=lambda r: r["date"])

    return latest_fetched_at, by_city


def _compute_kpis(records: list[dict]) -> dict:
    temp_maxes = [r["temp_max"] for r in records]
    temp_mins = [r["temp_min"] for r in records]
    total_precip = sum(r["precipitation"] for r in records)
    rainiest_day = max(records, key=lambda r: r["precipitation"])

    return {
        "avg_max": sum(temp_maxes) / len(temp_maxes),
        "avg_min": sum(temp_mins) / len(temp_mins),
        "total_precip": total_precip,
        "rainiest_date": rainiest_day["date"],
        "rainiest_amount": rainiest_day["precipitation"],
    }


def _temp_bar_width(temp_max: float) -> float:
    return max(0.0, min(100.0, (temp_max / MAX_TEMP_SCALE) * 100))


def _render_city_card(city: str, records: list[dict], kpis: dict) -> str:
    rows = "\n".join(
        f"""
        <tr>
          <td>{r["date"]}</td>
          <td>
            <div class="bar-track"><div class="bar" style="width:{_temp_bar_width(r["temp_max"]):.0f}%"></div></div>
            {r["temp_max"]:.1f}&deg;C
          </td>
          <td>{r["temp_min"]:.1f}&deg;C</td>
          <td>{r["precipitation"]:.1f}mm</td>
        </tr>"""
        for r in records
    )

    return f"""
    <section class="card">
      <h2>{city}</h2>
      <div class="kpis">
        <div class="kpi"><span class="kpi-value">{kpis["avg_max"]:.1f}&deg;C</span><span class="kpi-label">avg max</span></div>
        <div class="kpi"><span class="kpi-value">{kpis["avg_min"]:.1f}&deg;C</span><span class="kpi-label">avg min</span></div>
        <div class="kpi"><span class="kpi-value">{kpis["total_precip"]:.1f}mm</span><span class="kpi-label">total precipitation</span></div>
        <div class="kpi"><span class="kpi-value">{kpis["rainiest_amount"]:.1f}mm</span><span class="kpi-label">rainiest day ({kpis["rainiest_date"]})</span></div>
      </div>
      <table>
        <thead>
          <tr><th>Date</th><th>Max</th><th>Min</th><th>Precip.</th></tr>
        </thead>
        <tbody>{rows}
        </tbody>
      </table>
    </section>"""


STYLE = """
  :root { color-scheme: light; }
  body { margin: 0; padding: 32px; background: #f4f6f8; color: #1a1a1a; font-family: system-ui, sans-serif; }
  h1 { font-size: 1.4rem; margin-bottom: 4px; }
  .subtitle { color: #555; margin-top: 0; margin-bottom: 24px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
  .card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); }
  .card h2 { margin-top: 0; margin-bottom: 12px; font-size: 1.15rem; }
  .kpis { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 16px; }
  .kpi { background: #f0f2f5; border-radius: 8px; padding: 8px 10px; display: flex; flex-direction: column; }
  .kpi-value { font-size: 1.1rem; font-weight: 600; }
  .kpi-label { font-size: 0.72rem; color: #666; }
  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  th, td { text-align: left; padding: 6px 4px; border-bottom: 1px solid #eee; }
  .bar-track { background: #e8e8e8; border-radius: 4px; height: 6px; margin-bottom: 3px; }
  .bar { background: #3d7bd9; height: 6px; border-radius: 4px; }
"""


def generate_dashboard(
    history: list[dict], output_path: Path, city_order: list[str]
) -> None:
    fetched_at, by_city = _latest_snapshot(history, city_order)

    if fetched_at is None:
        body = "<h1>Weather forecast dashboard</h1><p class='subtitle'>No data yet — run the script first.</p>"
    else:
        cards = "\n".join(
            _render_city_card(city, records, _compute_kpis(records))
            for city, records in by_city.items()
            if records
        )
        body = (
            "<h1>Weather forecast dashboard</h1>"
            f"<p class='subtitle'>Latest snapshot: {fetched_at}</p>"
            f"<div class='grid'>{cards}</div>"
        )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Weather Dashboard</title>
<style>{STYLE}</style>
</head>
<body>
{body}
</body>
</html>
"""

    with output_path.open("w", encoding="utf-8") as f:
        f.write(html)
