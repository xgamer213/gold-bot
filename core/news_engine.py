"""
ForexFactory & Macroeconomic News Engine.
Fetches high-impact economic calendar events (CPI, NFP, FOMC, PPI, Retail Sales, etc.),
enforces strict pre-news freeze windows to prevent slippage/stop-hunts, and determines
fundamental bias for XAU/USD (Gold) and USD pairs based on actual vs forecast numbers.
"""

import time
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
import requests

from core.config import settings

logger = logging.getLogger("NewsEngine")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

FOREX_FACTORY_CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

# Key High-Impact USD Events that move Gold (XAU/USD) violently
TIER_1_USD_EVENTS = [
    "CPI", "CORE CPI", "CONSUMER PRICE INDEX",
    "NON-FARM EMPLOYMENT CHANGE", "NON-FARM PAYROLLS", "NFP",
    "UNEMPLOYMENT RATE", "FED INTEREST RATE DECISION", "FOMC STATEMENT",
    "FOMC PRESS CONFERENCE", "PPI", "PRODUCER PRICE INDEX",
    "RETAIL SALES", "CORE RETAIL SALES", "GDP", "ADVANCE GDP",
    "FED CHAIR POWELL TESTIFIES", "ISM MANUFACTURING PMI", "ISM SERVICES PMI"
]


class EconomicEvent:
    def __init__(self, data: Dict[str, Any]):
        self.title = data.get("title", "").strip()
        self.country = data.get("country", "").strip().upper()
        self.date_str = data.get("date", "")
        self.impact = data.get("impact", "").strip().capitalize()
        self.forecast = data.get("forecast", "").strip()
        self.previous = data.get("previous", "").strip()
        self.actual = data.get("actual", "").strip()
        
        # Parse datetime
        self.timestamp = self._parse_datetime(self.date_str)
        self.is_tier_1 = self._check_tier_1()

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        try:
            # ForexFactory formats: "2026-10-15T08:30:00-04:00"
            return datetime.fromisoformat(date_str)
        except Exception:
            try:
                # Fallback format
                return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
            except Exception:
                return None

    def _check_tier_1(self) -> bool:
        title_upper = self.title.upper()
        for t1 in TIER_1_USD_EVENTS:
            if t1 in title_upper:
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "country": self.country,
            "date": self.date_str,
            "impact": self.impact,
            "forecast": self.forecast,
            "previous": self.previous,
            "actual": self.actual,
            "is_tier_1": self.is_tier_1
        }


import json
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent / "data"
CACHE_FILE = CACHE_DIR / "calendar_cache.json"


class NewsEngine:
    def __init__(self):
        self.events: List[EconomicEvent] = []
        self.last_fetch_time: float = 0
        self.cache_ttl_seconds: int = 3600  # 1 hour cache to prevent HTTP 429
        self.notified_30min_events = set()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._load_from_disk_cache()
        self.refresh_calendar()

    def _load_from_disk_cache(self) -> bool:
        """Loads events from local disk cache if available."""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    raw_events = json.load(f)
                    if isinstance(raw_events, list) and raw_events:
                        self.events = [EconomicEvent(item) for item in raw_events if isinstance(item, dict)]
                        self.last_fetch_time = CACHE_FILE.stat().st_mtime
                        logger.info(f"Loaded {len(self.events)} events from local disk cache.")
                        return True
            except Exception as e:
                logger.warning(f"Error reading local calendar cache: {e}")
        return False

    def _save_to_disk_cache(self, raw_events: list):
        """Saves events to local disk cache."""
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(raw_events, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write calendar cache to disk: {e}")

    def refresh_calendar(self, force: bool = False) -> bool:
        """Fetches the latest economic calendar with rate-limit protection and disk fallback."""
        now = time.time()
        # If cache is still warm and we already have events, skip network request
        if not force and (now - self.last_fetch_time < self.cache_ttl_seconds) and self.events:
            return True

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "application/json"
            }
            response = requests.get(FOREX_FACTORY_CALENDAR_URL, headers=headers, timeout=12)
            if response.status_code == 200:
                raw_events = response.json()
                if isinstance(raw_events, list) and raw_events:
                    self.events = [EconomicEvent(item) for item in raw_events if isinstance(item, dict)]
                    self.last_fetch_time = now
                    self._save_to_disk_cache(raw_events)
                    logger.info(f"Fetched and cached {len(self.events)} events from ForexFactory.")
                    return True
            elif response.status_code == 429:
                logger.warning("ForexFactory rate limit hit (HTTP 429). Falling back to cached calendar.")
                if not self.events:
                    self._load_from_disk_cache()
                return len(self.events) > 0
            else:
                logger.warning(f"ForexFactory calendar request returned HTTP {response.status_code}. Using cache.")
                if not self.events:
                    self._load_from_disk_cache()
                return len(self.events) > 0
        except Exception as e:
            logger.error(f"Network error fetching ForexFactory: {e}. Using cache.")
            if not self.events:
                self._load_from_disk_cache()
            return len(self.events) > 0

    def get_upcoming_events(self, hours_ahead: int = 24, high_impact_only: bool = True, currency: str = "USD") -> List[EconomicEvent]:
        """Returns economic events within the next N hours."""
        self.refresh_calendar()
        now = datetime.now(timezone.utc)
        target_cutoff = now + timedelta(hours=hours_ahead)

        filtered = []
        for ev in self.events:
            if not ev.timestamp:
                continue
            # Normalize to UTC for reliable comparison
            ev_utc = ev.timestamp.astimezone(timezone.utc)
            if now <= ev_utc <= target_cutoff:
                if currency and ev.country != currency.upper():
                    continue
                if high_impact_only and ev.impact != "High":
                    continue
                filtered.append(ev)

        return filtered

    def get_recent_events(self, hours_behind: int = 4, currency: str = "USD") -> List[EconomicEvent]:
        """Returns events that took place in the last N hours."""
        self.refresh_calendar()
        now = datetime.now(timezone.utc)
        lookback = now - timedelta(hours=hours_behind)

        filtered = []
        for ev in self.events:
            if not ev.timestamp:
                continue
            ev_utc = ev.timestamp.astimezone(timezone.utc)
            if lookback <= ev_utc <= now:
                if currency and ev.country != currency.upper():
                    continue
                if ev.impact == "High" or ev.is_tier_1:
                    filtered.append(ev)

        return filtered

    def check_and_trigger_30min_alerts(self) -> List[EconomicEvent]:
        """
        Monitors economic calendar and fires a 30-minute advance warning email
        before High-Impact USD news (CPI, NFP, Unemployment, FOMC, PPI, Retail Sales).
        """
        self.refresh_calendar()
        now = datetime.now(timezone.utc)
        alerted = []

        # Window: between 15 and 35 minutes ahead
        min_window = timedelta(minutes=15)
        max_window = timedelta(minutes=35)

        for ev in self.events:
            if not ev.timestamp or ev.country != "USD":
                continue
            if ev.impact != "High" and not ev.is_tier_1:
                continue

            ev_utc = ev.timestamp.astimezone(timezone.utc)
            time_until = ev_utc - now

            if min_window <= time_until <= max_window:
                event_key = f"{ev.country}_{ev.title}_{ev.date_str}"
                if event_key not in self.notified_30min_events:
                    self.notified_30min_events.add(event_key)
                    alerted.append(ev)
                    logger.info(f"Triggering 30m pre-news alert for '{ev.title}'")
                    try:
                        from core.notifier import notifier
                        notifier.send_pre_news_alert(ev)
                    except Exception as e:
                        logger.error(f"Error dispatching 30m pre-news alert: {e}")

        return alerted

    def evaluate_gold_threat_and_bias(self) -> Dict[str, Any]:
        """
        Evaluates immediate news safety and fundamental bias for XAU/USD.
        
        Returns:
            {
               "is_safe": bool,
               "status": "CLEAR" | "RED_LOCKOUT" | "SPREAD_WAIT" | "POST_NEWS_CATALYST",
               "fundamental_bias": "BULLISH" | "BEARISH" | "NEUTRAL",
               "confluence_points": int (0 to 25),
               "reason": str,
               "relevant_event": Optional[Dict]
            }
        """
        if not settings.NEWS_FILTER_ENABLED:
            return {
                "is_safe": True,
                "status": "CLEAR",
                "fundamental_bias": "NEUTRAL",
                "confluence_points": 15,
                "reason": "News filter disabled in configuration.",
                "relevant_event": None
            }

        self.refresh_calendar()
        now = datetime.now(timezone.utc)

        freeze_window = timedelta(minutes=settings.NEWS_PRE_EVENT_FREEZE_MINS)
        spread_wait_window = timedelta(minutes=settings.NEWS_POST_EVENT_WAIT_MINS)
        catalyst_window = timedelta(minutes=settings.NEWS_CATALYST_WINDOW_MINS)

        # 1. Check for upcoming High-Impact USD news (Pre-event freeze)
        for ev in self.events:
            if not ev.timestamp or ev.country != "USD":
                continue
            if ev.impact != "High" and not ev.is_tier_1:
                continue

            ev_utc = ev.timestamp.astimezone(timezone.utc)
            time_until_event = ev_utc - now

            # If event is within 0 to PRE_EVENT_FREEZE_MINS in future
            if timedelta(0) <= time_until_event <= freeze_window:
                minutes_left = int(time_until_event.total_seconds() / 60)
                return {
                    "is_safe": False,
                    "status": "RED_LOCKOUT",
                    "fundamental_bias": "NEUTRAL",
                    "confluence_points": 0,
                    "reason": f"DANGER: High-Impact News '{ev.title}' in {minutes_left} minutes! Trading is frozen to prevent severe slippage and spread widening.",
                    "relevant_event": ev.to_dict()
                }

        # 2. Check for recent news that just dropped
        for ev in self.events:
            if not ev.timestamp or ev.country != "USD":
                continue
            if ev.impact != "High" and not ev.is_tier_1:
                continue

            ev_utc = ev.timestamp.astimezone(timezone.utc)
            time_since_event = now - ev_utc

            # A: If news released within 0 to POST_EVENT_WAIT_MINS (e.g., 0-10 mins)
            if timedelta(0) <= time_since_event <= spread_wait_window:
                mins_ago = int(time_since_event.total_seconds() / 60)
                return {
                    "is_safe": False,
                    "status": "SPREAD_WAIT",
                    "fundamental_bias": "NEUTRAL",
                    "confluence_points": 0,
                    "reason": f"STABILIZING: '{ev.title}' released {mins_ago}m ago. Waiting for institutional spread and initial spike to settle before entry.",
                    "relevant_event": ev.to_dict()
                }

            # B: If news released within 10m to 120m ago (The Prime Catalyst Window!)
            if spread_wait_window < time_since_event <= catalyst_window:
                bias, bias_reason, pts = self._analyze_event_bias(ev)
                mins_ago = int(time_since_event.total_seconds() / 60)
                return {
                    "is_safe": True,
                    "status": "POST_NEWS_CATALYST",
                    "fundamental_bias": bias,
                    "confluence_points": pts,
                    "reason": f"POST-NEWS CONFLUENCE: '{ev.title}' released {mins_ago}m ago. {bias_reason}",
                    "relevant_event": ev.to_dict()
                }

        # 3. Market is clear of immediate high-impact red-folder shocks
        return {
            "is_safe": True,
            "status": "CLEAR",
            "fundamental_bias": "NEUTRAL",
            "confluence_points": 15,  # Neutral baseline
            "reason": "Market is clear of immediate high-impact USD economic releases. Technical structure is active.",
            "relevant_event": None
        }

    def _analyze_event_bias(self, ev: EconomicEvent) -> Tuple[str, str, int]:
        """
        Calculates bullish or bearish bias for Gold based on Actual vs Forecast.
        Economics 101 for Gold (XAU/USD):
        - Hot Inflation (CPI/PPI) or strong employment (NFP) -> Fed stays hawkish -> USD Rallies -> GOLD FALLS (BEARISH).
        - Weak Inflation or weak employment -> Fed rate cuts / dovish -> USD Drops -> GOLD ROCKETS (BULLISH).
        - Higher Unemployment Rate -> Bad for USD -> GOLD BULLISH.
        """
        title_upper = ev.title.upper()
        actual = self._clean_number(ev.actual)
        forecast = self._clean_number(ev.forecast)

        if actual is None or forecast is None:
            # Cannot mathematically compare, default to neutral
            return "NEUTRAL", f"Actual ({ev.actual}) vs Forecast ({ev.forecast}) not quantifiable.", 15

        diff = actual - forecast

        # Unemployment Rate: higher is bad for USD, good for Gold
        if "UNEMPLOYMENT RATE" in title_upper or "JOBLESS CLAIMS" in title_upper:
            if diff > 0.05:  # Higher unemployment
                return "BULLISH", f"Unemployment came in higher ({ev.actual} vs {ev.forecast} exp), weakening USD. Strong Bullish catalyst for Gold.", 25
            elif diff < -0.05:
                return "BEARISH", f"Unemployment came in lower ({ev.actual} vs {ev.forecast} exp), strengthening USD. Bearish pressure on Gold.", 25
            else:
                return "NEUTRAL", f"Unemployment in line with expectations ({ev.actual}).", 15

        # CPI, NFP, PPI, Retail Sales: higher is good for USD, bad for Gold
        if any(term in title_upper for term in ["CPI", "NON-FARM", "NFP", "PAYROLLS", "PPI", "RETAIL SALES"]):
            if diff > 0.01:
                return "BEARISH", f"{ev.title} beat expectations ({ev.actual} vs {ev.forecast} exp), boosting USD. Bearish catalyst for Gold.", 25
            elif diff < -0.01:
                return "BULLISH", f"{ev.title} missed expectations ({ev.actual} vs {ev.forecast} exp), weighing down USD. Strong Bullish catalyst for Gold.", 25
            else:
                return "NEUTRAL", f"{ev.title} met expectations ({ev.actual}).", 15

        return "NEUTRAL", "Event deviation within normal variance.", 15

    def _clean_number(self, val_str: str) -> Optional[float]:
        """Strips %, K, M, B and converts to float."""
        if not val_str:
            return None
        cleaned = val_str.replace("%", "").replace(",", "").replace("$", "").replace("K", "e3").replace("M", "e6").replace("B", "e9").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None


# Global instance
news_engine = NewsEngine()
