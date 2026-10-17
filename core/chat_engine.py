"""
Interactive Trade Assistant & Chat Engine for Ahmed.
Enables real-time conversation to analyze trade ideas, check upcoming news (CPI/NFP),
calculate dynamic lot sizes, evaluate market predictions, and discuss Gold/Forex setups.
"""

import re
import logging
from typing import Dict, Any, Optional

from core.config import settings
from core.news_engine import news_engine
from core.technical_engine import technical_engine
from core.predictive_engine import predictive_engine
from core.risk_calculator import risk_calculator

logger = logging.getLogger("ChatEngine")


class ChatEngine:
    def __init__(self):
        self.user_name = settings.USER_NAME or "Ahmed"

    def respond(self, message: str) -> str:
        """
        Processes Ahmed's message and returns an institutional, actionable response.
        """
        msg = message.strip()
        msg_lower = msg.lower()

        if not msg:
            return f"Hey {self.user_name}, I'm here! What would you like to discuss? You can ask me to review a trade idea, check CPI/NFP news, calculate lot sizes, or give you the latest Gold market prediction."

        # 1. Greetings
        if any(w in msg_lower for w in ["hello", "hey", "hi", "how are you", "howre you"]):
            return (
                f"Hey {self.user_name}! I'm doing great and tracking the markets 24/7. "
                "How can I help you today? You can discuss a trade with me, ask for current Gold analysis, "
                "check upcoming ForexFactory news, or calculate your lot size."
            )

        # 2. Check Upcoming News / CPI / NFP / FOMC
        if any(w in msg_lower for w in ["news", "cpi", "nfp", "fomc", "calendar", "event", "rate", "fed", "inflation"]):
            return self._handle_news_query(msg_lower)

        # 3. Market Prediction / Crash / Rally Query
        if any(w in msg_lower for w in ["predict", "crash", "forecast", "outlook", "tomorrow", "bounce", "rally", "will gold"]):
            return self._handle_prediction_query()

        # 4. Current Price / Status of Gold or Forex
        if any(w in msg_lower for w in ["price", "current status", "what is gold doing", "gold trend", "analysis"]):
            return self._handle_market_status_query()

        # 5. Lot Size / Risk Calculation Query
        if any(w in msg_lower for w in ["lot", "lotsize", "risk", "calculate lot", "how many lots"]):
            return self._handle_lot_size_query(msg)

        # 6. Trade Idea Review (e.g. "Should I buy Gold at 2680?", "Buy entry 2685, SL 2679")
        if any(w in msg_lower for w in ["buy", "sell", "entry", "sl", "tp", "trade idea", "should i"]):
            return self._handle_trade_discussion(msg)

        # 7. General Trading Wisdom & Guidance
        return (
            f"I hear you, {self.user_name}. To give you the best institutional analysis, you can ask me:\n"
            f" • 'Check my trade: BUY Gold at 2685, SL 2679, TP 2697'\n"
            f" • 'When is the next CPI or NFP release?'\n"
            f" • 'Will Gold crash tomorrow? Show me the market prediction.'\n"
            f" • 'What is the current Gold price and trend?'\n"
            f" • 'Calculate lot size for $5,000 balance with $5 SL on Gold'"
        )

    def _handle_news_query(self, msg_lower: str) -> str:
        """Handles economic news schedule inquiries."""
        events = news_engine.get_upcoming_events(hours_ahead=72, high_impact_only=True, currency="USD")
        threat = news_engine.evaluate_gold_threat_and_bias()

        if not events:
            # Check cached full week events
            high_week = [e for e in news_engine.events if e.impact == "High" or e.is_tier_1]
            if high_week:
                lines = [f" * [{e.country}] {e.title} on {e.date_str} (Forecast: {e.forecast or 'N/A'})" for e in high_week[:4]]
                return (
                    f"Hey {self.user_name}, there are no immediate high-impact USD events in the next few hours, "
                    f"so current market conditions are **{threat['status']}**.\n\n"
                    f"Here are the major Tier-1 events on this week's ForexFactory calendar:\n" + "\n".join(lines) +
                    f"\n\nRemember: I will email you 30 minutes before any of these drop!"
                )
            return f"Hey {self.user_name}, the ForexFactory economic calendar is currently clear of major Tier-1 shocks. Technical structure is active!"

        lines = [f" * **{e.country} {e.title}**: {e.date_str} | Exp: {e.forecast or 'N/A'}" for e in events[:4]]
        return (
            f"[NEWS RADAR FOR {self.user_name.upper()}]:\n"
            f"Current News Status: **{threat['status']}** ({threat['reason']})\n\n"
            f"Upcoming High-Impact Releases (Next 48-72h):\n" + "\n".join(lines) +
            f"\n\n[PROTECTION RULE]: I will freeze entries and email you **30 minutes before** these events drop so you can protect open positions!"
        )

    def _handle_prediction_query(self) -> str:
        """Handles forward-looking prediction requests."""
        outlook = predictive_engine.generate_market_outlook("XAUUSD")
        return (
            f"[MARKET PREDICTION BRIEFING FOR {self.user_name.upper()}]:\n\n"
            f"Headline: {outlook.get('headline')}\n"
            f"Regime / Bias: {outlook.get('bias')}\n"
            f"Current Price: ${outlook.get('current_price')}\n"
            f"Key Overhead Resistance: ${outlook.get('resistance')}\n"
            f"Key Demand Support: ${outlook.get('support')}\n"
            f"Trigger Level: ${outlook.get('trigger_level')} -> Target: ${outlook.get('target_1')}\n\n"
            f"Institutional Analysis:\n{outlook.get('detailed_analysis')}\n\n"
            f"Action Plan for You: {outlook.get('action_plan_for_user')}"
        )

    def _handle_market_status_query(self) -> str:
        """Handles live market snapshot and technical state."""
        df = technical_engine.fetch_market_data("XAUUSD", timeframe="15m", period="5d")
        if df is None:
            return f"Hey {self.user_name}, markets are currently closed or updating. Live Gold Futures are sitting around recent highs with technical structure in active consolidation."

        last_close = round(float(df["Close"].iloc[-1]), 2)
        ema50 = round(float(df["Close"].ewm(span=50).mean().iloc[-1]), 2)
        trend = "Bullish (Price > EMA50)" if last_close > ema50 else "Bearish (Price < EMA50)"

        threat = news_engine.evaluate_gold_threat_and_bias()

        return (
            f"[LIVE GOLD (XAU/USD) STATUS FOR {self.user_name.upper()}]:\n"
            f" * Price: ${last_close:,.2f}\n"
            f" * 15m Structure: {trend} (EMA 50: ${ema50:,.2f})\n"
            f" * ForexFactory News State: {threat['status']} | Macro Bias: {threat['fundamental_bias']}\n"
            f" * Context: {threat['reason']}\n\n"
            f"Need me to evaluate a specific trade entry or calculate your position size?"
        )

    def _handle_lot_size_query(self, msg: str) -> str:
        """Extracts numbers from user message to compute exact lot sizing."""
        numbers = [float(n) for n in re.findall(r"[-+]?\d*\.\d+|\d+", msg.replace("$", "").replace(",", ""))]
        
        balance = settings.ACCOUNT_BALANCE
        sl_points = 6.0  # default $6 on Gold

        if len(numbers) >= 2:
            balance = max(numbers[0], numbers[1]) if any(n > 500 for n in numbers) else settings.ACCOUNT_BALANCE
            sl_points = min(numbers[0], numbers[1]) if any(n > 500 for n in numbers) else (numbers[1] if numbers[0] == balance else numbers[0])
        elif len(numbers) == 1 and numbers[0] > 500:
            balance = numbers[0]
        elif len(numbers) == 1 and numbers[0] < 50:
            sl_points = numbers[0]

        plan = risk_calculator.calculate_trade_setup("XAUUSD", "BUY", 2680.0, 2680.0 - sl_points, balance=balance, risk_pct=settings.RISK_PERCENT)

        return (
            f"[LOT SIZE CALCULATION FOR {self.user_name.upper()}]:\n"
            f" * Account Balance: ${balance:,.2f} USD\n"
            f" * Risk Parameter: {settings.RISK_PERCENT}% (${plan['max_dollar_risk']:,.2f} Max Risk)\n"
            f" * Stop Loss Distance: ${sl_points:,.2f} (or {sl_points*10:.0f} pips)\n\n"
            f"RECOMMENDED LOT SIZE: {plan['recommended_lot_size']} Lots\n"
            f" * At TP1 (1:1.5 RR): +${plan['expected_gain_tp1']:,.2f}\n"
            f" * At TP2 (1:3.0 RR): +${plan['expected_gain_tp2']:,.2f}\n"
            f"Always stick to this lot size to protect your account against unexpected volatility!"
        )

    def _handle_trade_discussion(self, msg: str) -> str:
        """Parses a potential trade idea from Ahmed and provides an institutional critique."""
        action = "BUY" if "buy" in msg.lower() else ("SELL" if "sell" in msg.lower() else "BUY")
        numbers = [float(n) for n in re.findall(r"[-+]?\d*\.\d+|\d+", msg.replace("$", "").replace(",", ""))]

        if len(numbers) >= 2:
            entry = numbers[0]
            sl = numbers[1]
            if action == "BUY" and sl >= entry:
                sl = entry - abs(entry - sl) if entry != sl else entry - 6.0
            elif action == "SELL" and sl <= entry:
                sl = entry + abs(entry - sl) if entry != sl else entry + 6.0

            try:
                plan = risk_calculator.calculate_trade_setup("XAUUSD", action, entry, sl)
                threat = news_engine.evaluate_gold_threat_and_bias()

                verdict = "APPROVED (Grade A Setup)" if threat["is_safe"] else "WARNING: High-Impact News Approaching!"

                return (
                    f"[TRADE REVIEW FOR {self.user_name.upper()}]:\n\n"
                    f"Verdict: {verdict}\n"
                    f" * Asset: Gold (XAU/USD) {action}\n"
                    f" * Planned Entry: ${entry:,.2f}\n"
                    f" * Stop Loss: ${sl:,.2f} (Risk Distance: ${plan['sl_distance_points']:,.2f} / {plan['sl_distance_pips']} pips)\n"
                    f" * Take Profit 1 (1:1.5): ${plan['tp1']:,.2f} (Close 50% & move SL to Breakeven)\n"
                    f" * Take Profit 2 (1:3.0): ${plan['tp2']:,.2f}\n"
                    f" * Recommended Lot Size: {plan['recommended_lot_size']} Lots (Risk: ${plan['max_dollar_risk']:,.2f})\n\n"
                    f"ForexFactory Macro Check: {threat['reason']}\n\n"
                    f"My Advice: If 15m structure confirms this level without conflicting red-folder news, execution is solid. Stick to the recommended lot size!"
                )
            except Exception as e:
                pass

        return (
            f"Hey {self.user_name}, I'd be happy to evaluate that trade idea! "
            f"Please give me your planned Entry and Stop Loss (e.g. 'Should I BUY Gold at 2685 with SL 2679?'), "
            f"and I will calculate your exact lot size, risk-reward ratio, and cross-check it against live ForexFactory news."
        )


# Global instance
chat_engine = ChatEngine()
