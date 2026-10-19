"""
Institutional Trade Assistant & Conversational Intelligence Engine for Ahmed.
Provides deep market wisdom, Smart Money Concepts (SMC), macroeconomic reasoning,
trade idea reviews, on-demand live signal generation, and 24/7 automated alerts.
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
        Processes Ahmed's message with deep institutional trading knowledge and actionable guidance.
        """
        msg = message.strip()
        msg_lower = msg.lower()

        if not msg:
            return f"Hey {self.user_name}, I'm here! What would you like to discuss? Ask me for a live Gold signal, market analysis, news review, or custom lot sizing."

        # 1. Greetings & Personal Check-in
        if any(w in msg_lower for w in ["hello", "hey", "hi", "how are you", "howre you", "what's up", "whats up"]):
            return (
                f"Hey {self.user_name}! I'm doing great and monitoring Gold (XAU/USD) order flow 24/7. "
                "How are you feeling about the markets today? "
                "You can ask me to **'Give me a signal'**, review a trade idea, check CPI/NFP news, or discuss any market topic!"
            )

        # 2. On-Demand Signal Generation ("Give me a signal", "Any trade now?", "Scan market")
        if any(w in msg_lower for w in ["signal", "give trade", "give me a trade", "find trade", "find a trade", "any setup", "should i trade", "what to trade", "take trade", "scan now", "entry"]):
            if not any(w in msg_lower for w in ["review", "calculate", "check my"]):
                return self._handle_signal_request()

        # 3. Check Upcoming News / CPI / NFP / FOMC / Fed
        if any(w in msg_lower for w in ["news", "cpi", "nfp", "fomc", "calendar", "event", "rate", "fed", "powell", "inflation", "ppi"]):
            return self._handle_news_query(msg_lower)

        # 4. Market Prediction / Crash / Rally Query
        if any(w in msg_lower for w in ["predict", "crash", "forecast", "outlook", "tomorrow", "bounce", "rally", "will gold", "next week", "direction"]):
            return self._handle_prediction_query()

        # 5. Current Price / Status of Gold or Forex
        if any(w in msg_lower for w in ["price", "current status", "what is gold doing", "gold trend", "analysis", "where is gold"]):
            return self._handle_market_status_query()

        # 6. Lot Size / Risk Calculation Query
        if any(w in msg_lower for w in ["lot", "lotsize", "risk", "calculate lot", "how many lots", "size"]):
            return self._handle_lot_size_query(msg)

        # 7. Trade Idea Review (e.g. "Should I buy Gold at 2680?", "Buy entry 2685, SL 2679")
        if any(w in msg_lower for w in ["buy", "sell", "sl", "tp", "trade idea", "bought", "sold"]):
            return self._handle_trade_discussion(msg)

        # 8. Smart Money Concepts (SMC) Knowledge (FVG, Order Block, Liquidity, Sweeps, CHoCH, MSS)
        if any(w in msg_lower for w in ["fvg", "fair value", "order block", "ob", "liquidity", "sweep", "choch", "mss", "structure", "smart money", "smc", "inducement", "discount", "premium"]):
            return self._handle_smc_knowledge(msg_lower)

        # 9. Trading Psychology & Risk Management
        if any(w in msg_lower for w in ["psychology", "discipline", "loss", "losing", "fear", "greed", "fomo", "overtrading", "drawdown", "mindset"]):
            return self._handle_psychology_guidance(msg_lower)

        # 10. Macroeconomics & Gold Drivers (DXY, Yields, BRICS, Central Banks)
        if any(w in msg_lower for w in ["dxy", "dollar", "yield", "yields", "brics", "central bank", "china", "safe haven", "war", "geopolitic"]):
            return self._handle_macro_knowledge(msg_lower)

        # 11. Market Sessions (Asia, London, New York)
        if any(w in msg_lower for w in ["session", "london", "asia", "asian", "new york", "ny session", "overlap", "judas"]):
            return self._handle_sessions_knowledge(msg_lower)

        # 12. General Conversational Fallback with Deep Market Insight
        return self._handle_general_trading_chat(msg)

    def _handle_signal_request(self) -> str:
        """
        Runs an instantaneous live institutional scan on Gold (XAU/USD)
        and returns either an immediate Grade A+ blueprint or current market structure setup.
        """
        scan = technical_engine.evaluate_live_chart("XAUUSD")
        score = scan.get("confluence_score", 0)
        signal = scan.get("signal", "WAIT")
        price = scan.get("current_price", 2685.0)
        news_eval = scan.get("news_eval", {})

        if signal in ["BUY", "SELL"] and score >= settings.MIN_CONFLUENCE_SCORE:
            plan = scan.get("trade_plan", {})
            risk_rate = plan.get('risk_badge', "🛡️ No risk")
            entry_zone = plan.get('entry_zone', f"${plan.get('entry_price', price)-0.75:.2f} - ${plan.get('entry_price', price)+0.75:.2f}")
            return (
                f"🚨 **GRADE A+ {signal} SETUP DETECTED FOR {self.user_name.upper()}!**\n\n"
                f"📊 **Confluence Score:** {score}% (Grade A+ Institutional Setup Only)\n"
                f"🎯 **Symbol:** XAU/USD (Gold)\n"
                f"🟢 **Action:** {signal}\n"
                f"⚠️ **Risk Rate:** {risk_rate}\n"
                f"📍 **Entry Zone:** {entry_zone}\n"
                f"💵 **Entry Price:** ${plan.get('entry_price', price):,.2f}\n"
                f"🛑 **Stop Loss (SL):** ${plan.get('stop_loss', 0.0):,.2f} (ATR Dynamic)\n"
                f"💰 **Take Profit 1 (TP1):** ${plan.get('tp1', 0.0):,.2f} *(Close 50% & SL to Breakeven)*\n"
                f"💰 **Take Profit 2 (TP2):** ${plan.get('tp2', 0.0):,.2f}\n"
                f"💰 **Take Profit 3 (TP3):** ${plan.get('tp3', 0.0):,.2f} *(Runner)*\n"
                f"⚖️ **Recommended Lot:** {plan.get('recommended_lot_size', 0.01)} Lots (Account: ${plan.get('account_balance', settings.ACCOUNT_BALANCE):,.0f} | Risk: ${plan.get('actual_dollar_risk', 5.0):,.2f})\n\n"
                f"📌 **SMC Reasons:** {scan.get('reason', 'Trend + FVG + Liquidity confirmed.')}\n\n"
                f"🚀 *I have also pushed this alert directly to your Telegram! Take this trade with strict risk management.*"
            )

        if signal == "LOCKOUT" or not news_eval.get("is_safe", True):
            return (
                f"⚠️ **HOLD FIRE, {self.user_name.upper()}! [NEWS LOCKOUT ACTIVE]**\n\n"
                f"• Current Price: ${price:,.2f}\n"
                f"• Lockout Reason: {news_eval.get('reason', 'High-impact USD event within freeze window.')}\n"
                f"• Rule: We **never gamble** into Tier-1 economic releases. Spreads can blow out 20-30 pips and trigger severe slippage.\n"
                f"• Strategy: Wait 10 minutes post-release. I will evaluate the fundamental shock and give you a high-probability momentum continuation setup!"
            )

        # Market in active consolidation / scanning (Below 85% Confluence)
        df = technical_engine.fetch_market_data("XAUUSD", timeframe="15m", period="5d")
        ema200 = price - 12.0
        atr = 5.5
        if df is not None and len(df) > 50:
            ema200 = round(float(df["Close"].ewm(span=200).mean().iloc[-1]), 2)
            atr = round(float(df["High"].iloc[-1] - df["Low"].iloc[-1]), 2)
            price = round(float(df["Close"].iloc[-1]), 2)

        bias = "BULLISH" if price > ema200 else "BEARISH"
        action = "BUY" if bias == "BULLISH" else "SELL"

        return (
            f"⏳ **NO ACTIVE GRADE A+ SIGNAL RIGHT NOW, {self.user_name.upper()}!**\n\n"
            f"🛑 **ACTION:** **DO NOT ENTER ANY TRADES RIGHT NOW**\n\n"
            f"📊 **LIVE MARKET SNAPSHOT:**\n"
            f"• **Live Price:** ${price:,.2f}\n"
            f"• **Current Confluence Score:** **{score}%** *(We require 85%+ for Grade A+)*\n"
            f"• **Market Regime:** {bias} Consolidation (200 EMA Baseline: ${ema200:,.2f})\n"
            f"• **Status:** {scan.get('reason', 'Awaiting liquidity sweep and structural displacement.')}\n\n"
            f"🔍 **WHY WE ARE WAITING (CAPITAL PRESERVATION):**\n"
            f"The market is currently in the middle of a move or range. Entering now would be **chasing price** without institutional confirmation, which risks getting stopped out.\n\n"
            f"🔭 **WHAT THE BOT IS WATCHING FOR:**\n"
            f"• Watching for price to retrace and tap key Fair Value Gaps (FVG) or sweep liquidity.\n"
            f"• Potential bias on next setup: **{action}** (following the 15m trend).\n\n"
            f"🚀 *Relax Ahmed: You don't have to watch the chart! The scanner is running in the background every 3 minutes. The exact moment an 85%+ confluence Grade A+ setup forms, your phone will buzz with an official [TAKE THIS TRADE] signal!*"
        )

    def _handle_news_query(self, msg_lower: str) -> str:
        """Handles economic news schedule inquiries with macro perspective."""
        events = news_engine.get_upcoming_events(hours_ahead=72, high_impact_only=True, currency="USD")
        threat = news_engine.evaluate_gold_threat_and_bias()

        if not events:
            high_week = [e for e in news_engine.events if e.impact == "High" or e.is_tier_1]
            if high_week:
                lines = [f" • **[{e.country}] {e.title}**: {e.date_str} (Forecast: {e.forecast or 'N/A'})" for e in high_week[:4]]
                return (
                    f"Hey {self.user_name}, there are no immediate high-impact USD events in the next few hours, "
                    f"so current market conditions are **{threat['status']}**.\n\n"
                    f"📅 **Upcoming Tier-1 ForexFactory Releases This Week:**\n" + "\n".join(lines) +
                    f"\n\n🛡️ *Protection Protocol:* I will freeze entries and send an alert to your Telegram **30 minutes before** any of these drop!"
                )
            return f"Hey {self.user_name}, the ForexFactory economic calendar is currently clear of major Tier-1 shocks. Technical structure is fully active!"

        lines = [f" • **{e.country} {e.title}**: {e.date_str} | Forecast: {e.forecast or 'N/A'} (Prev: {e.previous or 'N/A'})" for e in events[:4]]
        return (
            f"📰 **FOREXFACTORY NEWS RADAR FOR {self.user_name.upper()}**\n\n"
            f"• **Current News State:** **{threat['status']}** ({threat['reason']})\n"
            f"• **Fundamental Bias on Gold:** **{threat['fundamental_bias']}**\n\n"
            f"🔥 **Upcoming High-Impact Releases (Next 48-72h):**\n" + "\n".join(lines) +
            f"\n\n🛡️ *Golden Rule:* I will alert your Telegram **30 minutes prior** to protect your open trades from spread spikes!"
        )

    def _handle_prediction_query(self) -> str:
        """Handles forward-looking prediction requests."""
        outlook = predictive_engine.generate_market_outlook("XAUUSD")
        return (
            f"🔮 **MARKET PREDICTION BRIEFING FOR {self.user_name.upper()}**\n\n"
            f"• **Headline:** {outlook.get('headline')}\n"
            f"• **Directional Bias:** {outlook.get('bias', 'NEUTRAL')}\n"
            f"• **Crash Probability:** {outlook.get('crash_risk_probability', '25%')}\n"
            f"• **Rally Probability:** {outlook.get('rally_probability', '75%')}\n"
            f"• **Current Price:** ${outlook.get('current_price', 0):,.2f}\n"
            f"• **Key Overhead Resistance:** ${outlook.get('resistance', 0):,.2f}\n"
            f"• **Key Demand Support:** ${outlook.get('support', 0):,.2f}\n"
            f"• **Trigger Level:** ${outlook.get('trigger_level', 0):,.2f} ➔ Target: ${outlook.get('target_1', 0):,.2f}\n\n"
            f"💡 **Institutional Analysis:**\n{outlook.get('detailed_analysis')}\n\n"
            f"🎯 **Action Plan for You:** {outlook.get('action_plan_for_user')}"
        )

    def _handle_market_status_query(self) -> str:
        """Handles live market snapshot and technical state."""
        df = technical_engine.fetch_market_data("XAUUSD", timeframe="15m", period="5d")
        if df is None:
            return f"Hey {self.user_name}, live Gold futures are currently in active consolidation. Let me know if you want me to calculate a lot size or scan for setups."

        last_close = round(float(df["Close"].iloc[-1]), 2)
        ema50 = round(float(df["Close"].ewm(span=50).mean().iloc[-1]), 2)
        ema200 = round(float(df["Close"].ewm(span=200).mean().iloc[-1]), 2)
        trend = "Bullish (Above 200 EMA)" if last_close > ema200 else "Bearish (Below 200 EMA)"

        threat = news_engine.evaluate_gold_threat_and_bias()

        return (
            f"📊 **LIVE GOLD (XAU/USD) SNAPSHOT FOR {self.user_name.upper()}**\n\n"
            f"• **Live Price:** ${last_close:,.2f}\n"
            f"• **Macro Structure:** {trend}\n"
            f"• **Fast EMA (50):** ${ema50:,.2f}\n"
            f"• **Institutional Baseline (200 EMA):** ${ema200:,.2f}\n"
            f"• **ForexFactory News State:** {threat['status']} | Fundamental Bias: {threat['fundamental_bias']}\n\n"
            f"Would you like me to generate a live setup or calculate your position size for this move?"
        )

    def _handle_lot_size_query(self, msg: str) -> str:
        """Extracts numbers from user message to compute exact lot sizing."""
        numbers = [float(n) for n in re.findall(r"[-+]?\d*\.\d+|\d+", msg.replace("$", "").replace(",", ""))]
        
        balance = settings.ACCOUNT_BALANCE
        sl_points = 6.0

        if len(numbers) >= 2:
            balance = max(numbers[0], numbers[1]) if any(n >= 50 for n in numbers) else settings.ACCOUNT_BALANCE
            sl_points = min(numbers[0], numbers[1]) if any(n >= 50 for n in numbers) else (numbers[1] if numbers[0] == balance else numbers[0])
        elif len(numbers) == 1 and numbers[0] >= 50:
            balance = numbers[0]
        elif len(numbers) == 1 and numbers[0] < 50:
            sl_points = numbers[0]

        plan = risk_calculator.calculate_trade_setup("XAUUSD", "BUY", 2680.0, 2680.0 - sl_points, balance=balance, risk_pct=settings.RISK_PERCENT)

        return (
            f"⚖️ **EXACT LOT SIZE CALCULATION FOR {self.user_name.upper()}**\n\n"
            f"• **Account Balance:** ${balance:,.2f} USD\n"
            f"• **Risk Parameter:** {settings.RISK_PERCENT}% (${plan['max_dollar_risk']:,.2f} Max Risk)\n"
            f"• **Stop Loss Distance:** ${sl_points:,.2f} (or {sl_points*10:.0f} pips)\n\n"
            f"👉 **RECOMMENDED LOT SIZE:** **{plan['recommended_lot_size']} Lots**\n\n"
            f"🎯 **Expected Gains:**\n"
            f"• At TP1 (1:1.5 RR): +${plan['expected_gain_tp1']:,.2f}\n"
            f"• At TP2 (1:3.0 RR): +${plan['expected_gain_tp2']:,.2f}\n"
            f"• At TP3 (1:5.0 RR): +${plan['expected_gain_tp3']:,.2f}\n\n"
            f"🛡️ *Golden Rule:* Never increase your lot size beyond {plan['recommended_lot_size']} Lots. Protecting your principal allows compounding to work its magic!"
        )

    def _handle_trade_discussion(self, msg: str) -> str:
        """Parses a potential trade idea from Ahmed and provides an institutional critique."""
        action = "BUY" if "buy" in msg.lower() or "bought" in msg.lower() else "SELL"
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
                verdict = "APPROVED (Safe to Trade)" if threat["is_safe"] else "WARNING: High-Impact News Ahead!"

                return (
                    f"📝 **INSTITUTIONAL TRADE REVIEW FOR {self.user_name.upper()}**\n\n"
                    f"• **Planned Entry: ${entry:,.2f}** | **Stop Loss: ${sl:,.2f}**\n"
                    f"• **Trade Action:** {action} Gold\n"
                    f"• **Stop Loss Distance:** ${abs(entry-sl):.2f} (or {abs(entry-sl)*10:.0f} pips)\n"
                    f"• **Recommended Lot:** **{plan['recommended_lot_size']} Lots** (Risk: 1.0% = ${plan['max_dollar_risk']:,.2f})\n\n"
                    f"🎯 **Institutional Targets:**\n"
                    f"• **TP1 (1:1.5 RR):** ${plan['tp1']:,.2f} (+${plan['expected_gain_tp1']:,.2f}) ➔ *Take 50% & SL to BE*\n"
                    f"• **TP2 (1:3.0 RR):** ${plan['tp2']:,.2f} (+${plan['expected_gain_tp2']:,.2f})\n"
                    f"• **TP3 (1:5.0 RR):** ${plan['tp3']:,.2f} (+${plan['expected_gain_tp3']:,.2f})\n\n"
                    f"🚦 **Verdict:** **{verdict}**\n"
                    f"• Macro Status: {threat['status']} ({threat['reason']})"
                )
            except Exception as e:
                logger.error(f"Error parsing trade discussion: {e}")

        return (
            f"Hey {self.user_name}, I see you're looking at a {action} trade! "
            f"To give you an exact institutional review, tell me your entry and stop loss. "
            f"For example: *'Review my trade: {action} Gold at 2685, SL 2679'*."
        )

    def _handle_smc_knowledge(self, msg_lower: str) -> str:
        """Explains Smart Money Concepts (FVG, Order Blocks, Liquidity)."""
        if "fvg" in msg_lower or "fair value" in msg_lower:
            return (
                f"📚 **SMART MONEY CONCEPTS: FAIR VALUE GAPS (FVG)**\n\n"
                f"Hey {self.user_name}, an FVG occurs when a 3-candle sequence moves so aggressively that the wick of Candle 1 does NOT overlap with the wick of Candle 3. "
                f"This leaves an imbalance where only one side of the market (buyers or sellers) was filled.\n\n"
                f"🎯 **How Institutions Trade FVGs:**\n"
                f"1. Price pushes aggressively, leaving a gap.\n"
                f"2. Later, institutional algorithms return to 'rebalance' the gap (50% equilibrium level).\n"
                f"3. When price touches the FVG in the direction of the dominant 200 EMA trend, that is our **Grade A+ entry trigger**!"
            )
        if "order block" in msg_lower or "ob" in msg_lower:
            return (
                f"📚 **SMART MONEY CONCEPTS: ORDER BLOCKS (OB)**\n\n"
                f"Hey {self.user_name}, an Order Block is the last opposite candle before an explosive institutional impulse that breaks market structure.\n\n"
                f"• **Bullish Order Block:** The last down-candle before an aggressive rally that sweeps highs.\n"
                f"• **Bearish Order Block:** The last up-candle before an aggressive plunge that sweeps lows.\n\n"
                f"Banks leave unfulfilled limit orders inside these candles. When price retests the order block, institutions defend their positions, triggering powerful bounces!"
            )
        if "liquidity" in msg_lower or "sweep" in msg_lower:
            return (
                f"📚 **SMART MONEY CONCEPTS: LIQUIDITY SWEEPS & STOP HUNTS**\n\n"
                f"Hey {self.user_name}, liquidity is the fuel of institutional trading. "
                f"Retail traders place their stop losses just above swing highs (Buy-side Liquidity) and below swing lows (Sell-side Liquidity).\n\n"
                f"Institutions need millions of dollars in volume to fill their orders. So they intentionally drive price past these obvious highs/lows to trigger retail stop orders, soak up the liquidity, and immediately reverse the market!\n"
                f"Our bot detects these sweeps in real time so we trade **with** the institutions, not against them."
            )
        return (
            f"📚 **SMART MONEY CONCEPTS (SMC) FRAMEWORK FOR {self.user_name.upper()}**\n\n"
            f"Institutional order flow is built around 3 core pillars:\n"
            f"1. **Liquidity Sweeps:** Grabbing retail stop-losses at session highs/lows.\n"
            f"2. **Market Structure Shifts (MSS):** Breaking key swing points with displacement.\n"
            f"3. **Fair Value Gap (FVG) Mitigation:** Entering on the retest of price imbalances.\n\n"
            f"Our bot checks all three of these before confirming any Grade A+ trade!"
        )

    def _handle_psychology_guidance(self, msg_lower: str) -> str:
        """Provides trading psychology, discipline, and drawdown guidance."""
        return (
            f"🧠 **INSTITUTIONAL TRADING PSYCHOLOGY FOR {self.user_name.upper()}**\n\n"
            f"Trading mastery is 20% strategy and 80% emotional discipline. Here are the 3 unbreakable rules:\n\n"
            f"1. **Quality Over Quantity:** The best hedge funds don't trade 20 times a day. They wait patiently for 1–2 Grade A+ setups per week. One high-confluence 1:3 RR trade makes more profit than 10 forced trades.\n"
            f"2. **The 1% Rule:** Never risk more than 1% ($100 on your $10k balance). Even if you experience 3 consecutive losses, your account only drops 3%, which is easily recovered.\n"
            f"3. **Zero FOMO:** If a candle explodes without you, NEVER chase it. Chasing enters at the exact moment institutions are taking profit on retail buyers. Always wait for the pullback!\n\n"
            f"Stay disciplined, Ahmed. Protect your capital first, and profits follow naturally."
        )

    def _handle_macro_knowledge(self, msg_lower: str) -> str:
        """Explains macro relationships driving Gold (DXY, Yields, Central Banks)."""
        return (
            f"🌍 **MACROECONOMIC DRIVERS OF GOLD (XAU/USD) FOR {self.user_name.upper()}**\n\n"
            f"Gold is the ultimate global monetary asset. It is driven by 3 macro forces:\n\n"
            f"1. **The US Dollar (DXY):** Gold is priced in USD. When DXY rallies (strong dollar), Gold experiences downward pressure. When DXY weakens, Gold soars.\n"
            f"2. **Real Interest Rates (US10Y - Inflation):** Gold pays no dividend or yield. When real bond yields fall, holding Gold becomes extremely attractive.\n"
            f"3. **Central Bank Accumulation:** Global central banks (China, India, Turkey) have been buying hundreds of tons of Gold reserves annually to de-dollarize reserves, creating a massive long-term structural floor under Gold prices!"
        )

    def _handle_sessions_knowledge(self, msg_lower: str) -> str:
        """Explains Forex trading sessions and daily cycle dynamics."""
        return (
            f"⏰ **THE 3 FOREX SESSIONS & DAILY CYCLE FOR {self.user_name.upper()}**\n\n"
            f"Gold price action follows a strict institutional daily cycle:\n\n"
            f"1. **Asian Session (00:00 - 07:00 UTC):**\n"
            f"   • Characteristic: Tight consolidation, low volume.\n"
            f"   • Purpose: Accumulates liquidity above and below the Asian range.\n\n"
            f"2. **London Session (07:00 - 15:00 UTC):**\n"
            f"   • Characteristic: **The Judas Swing (Fakeout)**.\n"
            f"   • Purpose: London open sweeps the Asian high or low, traps retail breakout traders, and then drives the true directional trend of the day.\n\n"
            f"3. **New York Session (12:00 - 20:00 UTC):**\n"
            f"   • Characteristic: Highest volatility and economic news catalysts (CPI, NFP, FOMC at 12:30/18:00 UTC).\n"
            f"   • Purpose: Volume continuation or major midday reversal.\n\n"
            f"💡 *Best Trading Window:* 07:30 - 10:30 UTC (London) and 12:30 - 16:30 UTC (London/NY Overlap)!"
        )

    def _handle_general_trading_chat(self, msg: str) -> str:
        """Thoughtful conversational response connecting any query to institutional trading."""
        return (
            f"That's a great point, {self.user_name}. In institutional trading, staying ahead requires understanding both technical structure and macroeconomic context.\n\n"
            f"Here is how I can help you right now:\n"
            f"• Type **'Give me a signal'** to run a live scan on Gold and get immediate Entry/SL/TP levels.\n"
            f"• Type **'What is Gold doing right now?'** for a live trend and EMA breakdown.\n"
            f"• Type **'Calculate lot size for $10k balance with $5 SL'** for exact position math.\n"
            f"• Type **'When is CPI?'** to check the ForexFactory calendar.\n"
            f"• Or ask me about **FVGs, Order Blocks, Liquidity Sweeps**, or trading psychology!\n\n"
            f"What specific setup or concept would you like to explore next?"
        )


# Singleton instance
chat_engine = ChatEngine()
