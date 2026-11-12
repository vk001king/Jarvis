"""Small, read-only adapters for public orbital, space-weather, and market feeds."""
from __future__ import annotations

import json
import math
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

_MAX_RESPONSE_BYTES = 2_000_000
NASA_LIVE_URL = "https://www.nasa.gov/live/"
NASA_YOUTUBE_LIVE_URL = "https://www.youtube.com/@NASA/live"
NASA_ISS_STREAMS_URL = (
    "https://www.youtube.com/playlist?list=PL2aBZuCeDwlQMf6xMgQAUAY_nbHAgW5jz"
)
_ISS_URL = "https://api.wheretheiss.at/v1/satellites/25544"
_KP_URL = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
_XRAY_URL = "https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json"
_YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}"


def _read_json(url: str, *, timeout: float = 8.0):
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "JARVIS Observatory/1.0",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        body = response.read(_MAX_RESPONSE_BYTES + 1)
    if len(body) > _MAX_RESPONSE_BYTES:
        raise ValueError("Public data response exceeded the size limit.")
    return json.loads(body.decode("utf-8"))


def _finite_number(value, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Feed returned an invalid {name}.") from exc
    if not math.isfinite(result):
        raise ValueError(f"Feed returned an invalid {name}.")
    return result


def fetch_iss_position() -> dict:
    """Fetch the public ISS position and basic orbital telemetry."""
    data = _read_json(_ISS_URL)
    latitude = _finite_number(data.get("latitude"), "latitude")
    longitude = _finite_number(data.get("longitude"), "longitude")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Feed returned an out-of-range ISS position.")
    return {
        "latitude": latitude,
        "longitude": longitude,
        "altitude_km": _finite_number(data.get("altitude"), "altitude"),
        "velocity_kmh": _finite_number(data.get("velocity"), "velocity"),
        "footprint_km": _finite_number(data.get("footprint"), "footprint"),
        "visibility": str(data.get("visibility") or "unknown"),
        "timestamp": int(_finite_number(data.get("timestamp"), "timestamp")),
    }


def fetch_kp_index() -> dict:
    """Fetch NOAA's one-minute planetary K-index estimate."""
    rows = _read_json(_KP_URL)
    if not isinstance(rows, list) or not rows:
        raise ValueError("NOAA returned no planetary K-index readings.")
    latest = max(
        (row for row in rows if isinstance(row, dict)),
        key=lambda row: str(row.get("time_tag") or ""),
        default=None,
    )
    if latest is None:
        raise ValueError("NOAA returned no valid planetary K-index readings.")
    index = _finite_number(
        latest.get("estimated_kp", latest.get("kp_index")), "K-index"
    )
    if not 0 <= index <= 9:
        raise ValueError("NOAA returned an out-of-range K-index.")
    return {"index": index, "time": str(latest.get("time_tag") or "")}


def fetch_xray_flux() -> dict:
    """Fetch NOAA GOES short-wave X-ray flux and derive its standard class."""
    rows = _read_json(_XRAY_URL)
    if not isinstance(rows, list):
        raise ValueError("NOAA returned an invalid X-ray feed.")
    candidates = [
        row for row in rows
        if (isinstance(row, dict) and row.get("energy") == "0.1-0.8nm"
            and row.get("flux") is not None)
    ]
    latest = max(
        candidates,
        key=lambda row: str(row.get("time_tag") or ""),
        default=None,
    )
    if latest is None:
        raise ValueError("NOAA returned no GOES X-ray readings.")
    flux = _finite_number(latest.get("flux"), "X-ray flux")
    if flux < 0:
        raise ValueError("NOAA returned a negative X-ray flux.")
    if flux < 1e-7:
        letter, base = "A", 1e-8
    elif flux < 1e-6:
        letter, base = "B", 1e-7
    elif flux < 1e-5:
        letter, base = "C", 1e-6
    elif flux < 1e-4:
        letter, base = "M", 1e-5
    else:
        letter, base = "X", 1e-4
    return {
        "flux": flux,
        "class": f"{letter}{flux / base:.1f}",
        "time": str(latest.get("time_tag") or ""),
        "satellite": latest.get("satellite"),
    }


def fetch_market_history(symbol: str) -> dict:
    """Fetch a one-day five-minute market chart; this is informational only."""
    ticker = str(symbol or "").strip().upper()
    if not re.fullmatch(r"[A-Z0-9.^=-]{1,20}", ticker):
        raise ValueError("Enter a ticker using letters, numbers, '.', '^', '-' or '='.")

    url = _YAHOO_CHART_URL.format(quote(ticker, safe="")) + "?range=1d&interval=5m"
    payload = _read_json(url)
    chart = payload.get("chart") if isinstance(payload, dict) else None
    error = chart.get("error") if isinstance(chart, dict) else None
    if error:
        description = str(error.get("description") or "Market feed rejected this ticker.")
        raise ValueError(description[:180])
    results = chart.get("result") if isinstance(chart, dict) else None
    if not results or not isinstance(results[0], dict):
        raise ValueError("Market feed returned no chart for this ticker.")

    result = results[0]
    meta = result.get("meta") or {}
    quote_data = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    closes = [
        _finite_number(value, "market price")
        for value in (quote_data.get("close") or [])
        if value is not None
    ]
    if not closes:
        raise ValueError("Market feed returned no usable price history.")

    raw_price = meta.get("regularMarketPrice")
    price = _finite_number(
        raw_price if raw_price is not None else closes[-1], "market price"
    )
    previous = meta.get("chartPreviousClose", meta.get("previousClose"))
    previous_close = (
        _finite_number(previous, "previous close") if previous is not None else None
    )
    change_pct = meta.get("regularMarketChangePercent")
    if change_pct is None and previous_close:
        change_pct = (price - previous_close) / previous_close * 100
    change_pct = _finite_number(change_pct or 0, "market change")

    volumes = quote_data.get("volume") or []
    volume = next((value for value in reversed(volumes) if value is not None), None)
    return {
        "symbol": ticker,
        "name": str(meta.get("shortName") or meta.get("longName") or ticker)[:80],
        "currency": str(meta.get("currency") or ""),
        "price": price,
        "change_pct": change_pct,
        "previous_close": previous_close,
        "high": _finite_number(
            meta.get("regularMarketDayHigh")
            if meta.get("regularMarketDayHigh") is not None else max(closes),
            "day high",
        ),
        "low": _finite_number(
            meta.get("regularMarketDayLow")
            if meta.get("regularMarketDayLow") is not None else min(closes),
            "day low",
        ),
        "volume": int(volume) if volume is not None else None,
        "history": closes[-78:],
        "timestamp": meta.get("regularMarketTime"),
    }
