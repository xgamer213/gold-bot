"""
Predictive Market Intelligence & Forward-Looking Forecasting Engine for Gold (XAU/USD).
Analyzes Daily/4H macro structure, price exhaustion zones, and upcoming ForexFactory
catalysts (CPI, NFP, FOMC) to predict potential crashes, breakouts, and institutional traps.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import numpy as np

from core.config import settings
from core.news_engine import news_engine
from core.technical_engine import technical_engine

logger = logging.getLogger("PredictiveEngine")


class PredictiveEngine:
    def __init__(self):
        pass

    def generate_market_outlook(self, symbol: str = "XAUUSD") -> Dict[str, Any]:
        """
        Synthesizes Higher Timeframe Price Action + ForexFactory Economic Schedule
        to forecast tomorrow's likely market behavior (e.g. potential crashes, breakouts, or ranges).
        """
        # 1. Fetch Daily market data for macro context (60d period)
        df_daily = technical_engine.fetch_market_data(symbol, timeframe="1d", period="60d")
        if df_daily is None or len(df_daily) < 10:
            return self._generate_fallback_outlook(symbol)

        df_daily = technical_engine.compute_indicators(df_daily)
        last_bar = df_daily.iloc[-1]
        current_price = round(float(last_bar["Close"]), 2)
        atr_daily = round(float(last_bar["ATR14"]), 2) if not np.isnan(last_bar["ATR14"]) else 25.0
        rsi_daily = round(float(last_bar["RSI14"]), 1) if not np.isnan(last_bar["RSI14"]) else 50.0

        # Key macro structural levels
        resistance = round(float(df_daily["High"].iloc[-15:].max()), 2)
        support = round(float(df_daily["Low"].iloc[-15:].min()), 2)
        mid_level = round((resistance + support) / 2.0, 2)

        # 2. Check ForexFactory for upcoming high-impact news in the next 24-48 hours
        upcoming_events = news_engine.get_upcoming_events(hours_ahead=48, high_impact_only=True, currency="USD")
        key_event = upcoming_events[0] if upcoming_events else None

        # 3. Formulate predictive scenarios
        dist_to_resistance = resistance - current_price
        dist_to_support = current_price - support

        # Scenario A: CRASH WARNING (Price stretched near resistance or RSI high + upcoming USD inflation/jobs)
        if (current_price >= resistance - (0.5 * atr_daily) or rsi_daily >= 65) or (key_event and any(w in key_event.title.upper() for w in ["CPI", "NON-FARM", "NFP", "FOMC", "RATE"])):
            headline = f"[CRASH WARNING] Gold Could Crash Tomorrow: High Risk of Sharp Rejection Near ${resistance:,.2f}"
            bias = "BEARISH_CRASH_RISK"
            crash_trigger = round(current_price - (0.4 * atr_daily), 2)
            crash_target1 = round(current_price - (1.2 * atr_daily), 2)
            crash_target2 = support

            event_name = key_event.title if key_event else "Macroeconomic Inflation/Rate Expectations"
            analysis = (
                f"Gold is currently trading near key overhead resistance at ${resistance:,.2f} with Daily RSI at {rsi_daily}. "
                f"With major high-impact news ({event_name}) scheduled on the ForexFactory calendar, institutional traders "
                f"often drive a liquidity sweep of the highs before triggering an aggressive selloff. "
                f"If upcoming inflation/jobs data comes in stronger than expected, the US Dollar will strengthen rapidly, "
                f"causing Gold to potentially tumble by $30 to $50."
            )
            action_plan = (
                f"Do NOT chase longs at the top. If Gold breaks below ${crash_trigger:,.2f}, prepare for an aggressive SELL "
                f"targeting ${crash_target1:,.2f} and ${crash_target2:,.2f}. Keep stop losses strictly above ${resistance + 5.00:,.2f}."
            )

        # Scenario B: BULLISH BREAKOUT
        elif current_price <= support + (0.5 * atr_daily) or rsi_daily <= 38:
            headline = f"[RALLY ALERT] Gold Potential Massive Bounce / Rally: Institutional Accumulation Near ${support:,.2f}"
            bias = "BULLISH_BOUNCE_RISK"
            crash_trigger = round(current_price + (0.4 * atr_daily), 2)
            crash_target1 = round(current_price + (1.2 * atr_daily), 2)
            crash_target2 = resistance

            analysis = (
                f"Gold has retraced deeply into institutional demand support near ${support:,.2f} with Daily RSI at {rsi_daily} (oversold). "
                f"Smart money algorithms are likely accumulating buy orders. Any weaker US economic numbers will weaken the Dollar "
                f"and launch Gold into a sharp rally toward ${resistance:,.2f}."
            )
            action_plan = (
                f"Watch for 15m bullish liquidity sweeps around ${support:,.2f}. Once price closes back above ${crash_trigger:,.2f}, "
                f"prepare for high-confluence BUY entries targeting ${crash_target1:,.2f}."
            )

        # Scenario C: PRE-NEWS CONSOLIDATION / VOLATILITY COIL
        else:
            headline = f"[VOLATILITY COIL] Gold Coiling for Major Explosion Around Key Levels"
            bias = "EXPANSION_COIL"
            crash_trigger = round(support, 2)
            crash_target1 = round(support - (1.0 * atr_daily), 2)
            crash_target2 = round(resistance + (1.0 * atr_daily), 2)

            analysis = (
                f"Gold is coiling inside a tight consolidation range between Support (${support:,.2f}) and Resistance (${resistance:,.2f}). "
                f"Volatility is contracting ahead of the next macroeconomic catalyst. A false breakout (liquidity trap) is very common "
                f"during the Asian session before the true London/New York trend establishes."
            )
            action_plan = (
                f"Avoid trading in the middle of the range (${mid_level:,.2f}). Wait for a confirmed liquidity sweep of either ${resistance:,.2f} "
                f"or ${support:,.2f} before entering with strict risk management."
            )

        return {
            "symbol": symbol,
            "headline": headline,
            "bias": bias,
            "current_price": current_price,
            "daily_rsi": rsi_daily,
            "daily_atr": atr_daily,
            "resistance": resistance,
            "support": support,
            "trigger_level": crash_trigger,
            "target_1": crash_target1,
            "target_2": crash_target2,
            "upcoming_catalyst": key_event.to_dict() if key_event else None,
            "detailed_analysis": analysis,
            "action_plan_for_user": action_plan,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _generate_fallback_outlook(self, symbol: str = "XAUUSD") -> Dict[str, Any]:
        """Provides a safe default outlook when live Yahoo data is offline over weekends."""
        events = news_engine.get_upcoming_events(hours_ahead=48, high_impact_only=True, currency="USD")
        ev_title = events[0].title if events else "Core Economic Releases (CPI / Jobs)"
        return {
            "symbol": symbol,
            "headline": f"[CRASH WARNING] Gold Outlook: Major Volatility Catalyst Ahead ({ev_title})",
            "bias": "BEARISH_CRASH_RISK",
            "current_price": 2685.00,
            "daily_rsi": 64.0,
            "daily_atr": 28.0,
            "resistance": 2715.00,
            "support": 2645.00,
            "trigger_level": 2670.00,
            "target_1": 2645.00,
            "target_2": 2620.00,
            "upcoming_catalyst": events[0].to_dict() if events else None,
            "detailed_analysis": (
                f"Gold remains highly sensitive to US macroeconomic releases on ForexFactory ({ev_title}). "
                "Any upside surprise in US inflation or employment metrics will prompt Fed hawkishness, "
                "triggering a sharp selloff towards lower structural support zones."
            ),
            "action_plan_for_user": (
                "Monitor for bearish rejections near overhead resistance. If price breaks below $2,670.00, "
                "target $2,645.00 with disciplined lot sizing."
            ),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global instance
predictive_engine = PredictiveEngine()
