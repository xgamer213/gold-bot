"""
Technical Analysis & Confluence Scoring Engine for XAU/USD & Forex.
Combines Smart Money Concepts (SMC - Liquidity Sweeps, Fair Value Gaps, Market Structure Shift)
with Multi-Timeframe Trend and Volatility (ATR) to produce high-probability (Grade A+) setups.
"""

import logging
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, Any, Optional, Tuple

from core.config import settings
from core.news_engine import news_engine
from core.risk_calculator import risk_calculator

logger = logging.getLogger("TechnicalEngine")


class TechnicalEngine:
    def __init__(self):
        pass

    def _fetch_realtime_gold(self, timeframe: str = "15m", limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Fetches live real-time Spot Gold (PAXGUSDT) with ZERO latency.
        PAXG is 1:1 backed by 1 Troy Ounce of fine physical Gold in London Brink's vaults.
        Eliminates the 15-minute delay from free Yahoo Finance futures.
        """
        try:
            interval = "15m" if "15" in timeframe else ("1h" if "1h" in timeframe else ("1m" if "1m" in timeframe else "15m"))
            url = f"https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval={interval}&limit={limit}"
            res = requests.get(url, timeout=4)
            if res.status_code == 200:
                raw = res.json()
                if raw and len(raw) >= 25:
                    cols = ['OpenTime','Open','High','Low','Close','Volume','CloseTime','QAV','NumTrades','TakerBase','TakerQuote','Ignore']
                    df = pd.DataFrame(raw, columns=cols)
                    df['Datetime'] = pd.to_datetime(df['OpenTime'], unit='ms', utc=True)
                    df.set_index('Datetime', inplace=True)
                    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                        df[col] = df[col].astype(float)
                    return df[['Open', 'High', 'Low', 'Close', 'Volume']]
        except Exception as e:
            logger.debug(f"Real-time gold feed check: {e}")
        return None

    def fetch_market_data(self, symbol: str = "XAUUSD", timeframe: str = "15m", period: str = "5d") -> Optional[pd.DataFrame]:
        """
        Fetches live OHLCV data.
        Prioritizes real-time 0-delay Spot Gold feed, with yfinance as secondary fallback.
        """
        sym_clean = symbol.upper().replace("/", "")

        # 1. Prioritize zero-delay live Spot Gold feed
        if any(g in sym_clean for g in ["XAU", "GOLD"]):
            live_df = self._fetch_realtime_gold(timeframe=timeframe)
            if live_df is not None and not live_df.empty and len(live_df) >= 25:
                return live_df

        ticker_map = {
            "XAUUSD": "GC=F",
            "GOLD": "GC=F",
            "EURUSD": "EURUSD=X",
            "GBPUSD": "GBPUSD=X",
            "USDJPY": "USDJPY=X",
            "AUDUSD": "AUDUSD=X"
        }
        yf_symbol = ticker_map.get(sym_clean, sym_clean)

        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(period=period, interval=timeframe)
            min_required = 10 if "d" in timeframe.lower() else 25
            if df.empty or len(df) < min_required:
                logger.warning(f"Insufficient historical data for {yf_symbol} (got {len(df)} bars, need {min_required})")
                return None
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {yf_symbol}: {e}")
            return None

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates EMAs, ATR, RSI, and detects Fair Value Gaps and Sweeps."""
        data = df.copy()

        # 1. EMAs for Trend Confirmation
        data["EMA20"] = data["Close"].ewm(span=20, adjust=False).mean()
        data["EMA50"] = data["Close"].ewm(span=50, adjust=False).mean()
        data["EMA200"] = data["Close"].ewm(span=200, adjust=False).mean()

        # 2. Average True Range (ATR 14) for Dynamic SL/TP
        high_low = data["High"] - data["Low"]
        high_close = (data["High"] - data["Close"].shift(1)).abs()
        low_close = (data["Low"] - data["Close"].shift(1)).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        data["ATR14"] = true_range.rolling(window=14).mean()

        # 3. Relative Strength Index (RSI 14)
        delta = data["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        data["RSI14"] = 100 - (100 / (1 + rs))

        # 4. Fair Value Gap (FVG) Detection
        # Bullish FVG: Low of candle[i] > High of candle[i-2]
        data["Bullish_FVG"] = (data["Low"] > data["High"].shift(2))
        data["Bearish_FVG"] = (data["High"] < data["Low"].shift(2))

        # 5. Swing Highs and Lows (20-period rolling)
        data["Swing_High"] = data["High"].rolling(window=20).max()
        data["Swing_Low"] = data["Low"].rolling(window=20).min()

        return data

    def evaluate_live_chart(self, symbol: str = "XAUUSD") -> Dict[str, Any]:
        """
        Analyzes the current chart for Gold / Forex and computes Confluence Score.
        Combines Technicals (80 pts max) + ForexFactory News (20 pts max).
        """
        df = self.fetch_market_data(symbol, timeframe="15m", period="5d")
        if df is None:
            return {
                "signal": "NONE",
                "confluence_score": 0,
                "reason": "Market data unavailable or market closed."
            }

        df = self.compute_indicators(df)
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        current_price = float(last_row["Close"])
        atr = float(last_row["ATR14"]) if not np.isnan(last_row["ATR14"]) else 3.5

        # Query News Engine for Macro & High-Impact State
        news_eval = news_engine.evaluate_gold_threat_and_bias()
        if not news_eval["is_safe"]:
            return {
                "signal": "LOCKOUT",
                "confluence_score": 0,
                "reason": news_eval["reason"],
                "news_eval": news_eval
            }

        # Confluence Score calculation for BUY and SELL
        buy_score, buy_reasons = self._calculate_buy_confluence(df, news_eval)
        sell_score, sell_reasons = self._calculate_sell_confluence(df, news_eval)

        # Determine winning signal
        if buy_score >= settings.MIN_CONFLUENCE_SCORE and buy_score > sell_score:
            signal_type = "BUY"
            final_score = buy_score
            reasons = buy_reasons
            # Exact SL: placed below recent swing low or 1.5x ATR
            swing_low = float(df["Low"].iloc[-15:].min())
            stop_loss = round(min(swing_low - 0.5, current_price - (1.5 * atr)), 2)
        elif sell_score >= settings.MIN_CONFLUENCE_SCORE and sell_score > buy_score:
            signal_type = "SELL"
            final_score = sell_score
            reasons = sell_reasons
            # Exact SL: placed above recent swing high or 1.5x ATR
            swing_high = float(df["High"].iloc[-15:].max())
            stop_loss = round(max(swing_high + 0.5, current_price + (1.5 * atr)), 2)
        else:
            return {
                "signal": "WAIT",
                "confluence_score": max(buy_score, sell_score),
                "reason": f"No Grade-A+ setup currently. Max Confluence is {max(buy_score, sell_score)}% (Threshold: {settings.MIN_CONFLUENCE_SCORE}%). Preserving capital.",
                "current_price": current_price,
                "news_eval": news_eval
            }

        # Calculate exact risk parameters and lot sizing
        trade_plan = risk_calculator.calculate_trade_setup(
            symbol=symbol,
            action=signal_type,
            entry_price=current_price,
            stop_loss=stop_loss,
            atr_val=atr
        )

        grade = "Grade A+ (Institutional)" if final_score >= 90 else "Grade A"

        return {
            "signal": signal_type,
            "symbol": symbol,
            "grade": grade,
            "confluence_score": final_score,
            "current_price": current_price,
            "trade_plan": trade_plan,
            "reasons": reasons,
            "news_eval": news_eval
        }

    def validate_tradingview_alert(
        self,
        symbol: str,
        action: str,
        price: float,
        strategy_name: str = "TradingView_Confluence",
        provided_sl: Optional[float] = None,
        provided_tp1: Optional[float] = None,
        provided_tp2: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Validates an incoming webhook alert from TradingView.
        Cross-checks against ForexFactory economic news filter and validates risk parameters.
        """
        action = action.upper()
        news_eval = news_engine.evaluate_gold_threat_and_bias()

        # 1. Check if trading is locked due to high-impact news (e.g. CPI/NFP release in next 30m)
        if not news_eval["is_safe"]:
            return {
                "approved": False,
                "status": "REJECTED_DUE_TO_NEWS",
                "reason": f"REJECTED: TradingView {action} signal blocked! {news_eval['reason']}",
                "news_eval": news_eval
            }

        # 2. Check fundamental alignment with news
        fundamental_bias = news_eval.get("fundamental_bias", "NEUTRAL")
        confluence_score = 70  # Baseline for confirmed TradingView strategy trigger

        reasons = [f"TradingView Strategy '{strategy_name}' triggered {action} at ${price:.2f}."]

        if fundamental_bias == action:
            confluence_score += 25
            reasons.append(f"ForexFactory Fundamental Alignment: News confirms {action} bias (+25%).")
        elif fundamental_bias != "NEUTRAL" and fundamental_bias != action:
            # News is directly opposing the technical signal
            return {
                "approved": False,
                "status": "REJECTED_OPPOSING_MACRO",
                "reason": f"REJECTED: Signal is {action}, but ForexFactory news bias is strongly {fundamental_bias}! Counter-trend trades into macro flows are prohibited.",
                "news_eval": news_eval
            }
        else:
            confluence_score += 15
            reasons.append("ForexFactory Calendar: Clear of conflicting red-folder news (+15%).")

        # 3. Calculate dynamic Stop Loss if not provided by TradingView
        is_gold = any(g in symbol.upper() for g in ["XAU", "GOLD", "GC"])
        if provided_sl is None:
            # Default to 1.5% or standard gold buffer ($6.00 move)
            buffer = 6.0 if is_gold else 0.0030
            stop_loss = round(price - buffer if action == "BUY" else price + buffer, 2 if is_gold else 5)
        else:
            stop_loss = provided_sl
            buffer = abs(price - stop_loss)

        # Calculate exact lot sizing and TP1/TP2
        trade_plan = risk_calculator.calculate_trade_setup(
            symbol=symbol,
            action=action,
            entry_price=price,
            stop_loss=stop_loss,
            atr_val=buffer,
            custom_tp1=provided_tp1,
            custom_tp2=provided_tp2
        )

        grade = "Grade A+ (Institutional)" if confluence_score >= 90 else "Grade A"

        return {
            "approved": True,
            "status": "APPROVED",
            "signal": action,
            "symbol": symbol,
            "grade": grade,
            "confluence_score": confluence_score,
            "price": price,
            "trade_plan": trade_plan,
            "reasons": reasons,
            "news_eval": news_eval
        }

    def _calculate_buy_confluence(self, df: pd.DataFrame, news_eval: Dict[str, Any]) -> Tuple[int, list]:
        score = 0
        reasons = []
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        # 1. Trend Alignment (25 pts)
        if last_row["Close"] > last_row["EMA50"] > last_row["EMA200"]:
            score += 25
            reasons.append("Trend: Institutional Bullish Trend (Price > EMA50 > EMA200).")
        elif last_row["Close"] > last_row["EMA50"]:
            score += 15
            reasons.append("Trend: Short-term Bullish Structure (Price > EMA50).")

        # 2. Liquidity Sweep & Rejection (25 pts)
        # Low of prev candle swept recent lows and closed back above
        recent_low = df["Low"].iloc[-10:-2].min()
        if prev_row["Low"] < recent_low and prev_row["Close"] > recent_low:
            score += 25
            reasons.append("Liquidity: Bullish Liquidity Sweep of previous lows confirmed.")

        # 3. Fair Value Gap / Structure Shift (20 pts)
        if df["Bullish_FVG"].iloc[-3:].any():
            score += 20
            reasons.append("Smart Money: Bullish Fair Value Gap (FVG) respected.")

        # 4. News Alignment (20 pts)
        if news_eval.get("fundamental_bias") == "BULLISH":
            score += 20
            reasons.append(f"ForexFactory Macro: {news_eval.get('reason')}")
        elif news_eval.get("fundamental_bias") == "NEUTRAL":
            score += 15
            reasons.append("Macro Environment: Clear of high-impact headwinds.")

        # 5. Momentum / RSI (10 pts)
        rsi = last_row["RSI14"]
        if 40 <= rsi <= 65:
            score += 10
            reasons.append(f"Momentum: Healthy expansion zone (RSI: {rsi:.1f}).")

        return score, reasons

    def _calculate_sell_confluence(self, df: pd.DataFrame, news_eval: Dict[str, Any]) -> Tuple[int, list]:
        score = 0
        reasons = []
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        # 1. Trend Alignment (25 pts)
        if last_row["Close"] < last_row["EMA50"] < last_row["EMA200"]:
            score += 25
            reasons.append("Trend: Institutional Bearish Trend (Price < EMA50 < EMA200).")
        elif last_row["Close"] < last_row["EMA50"]:
            score += 15
            reasons.append("Trend: Short-term Bearish Structure (Price < EMA50).")

        # 2. Liquidity Sweep & Rejection (25 pts)
        recent_high = df["High"].iloc[-10:-2].max()
        if prev_row["High"] > recent_high and prev_row["Close"] < recent_high:
            score += 25
            reasons.append("Liquidity: Bearish Liquidity Sweep of previous highs confirmed.")

        # 3. Fair Value Gap / Structure Shift (20 pts)
        if df["Bearish_FVG"].iloc[-3:].any():
            score += 20
            reasons.append("Smart Money: Bearish Fair Value Gap (FVG) respected.")

        # 4. News Alignment (20 pts)
        if news_eval.get("fundamental_bias") == "BEARISH":
            score += 20
            reasons.append(f"ForexFactory Macro: {news_eval.get('reason')}")
        elif news_eval.get("fundamental_bias") == "NEUTRAL":
            score += 15
            reasons.append("Macro Environment: Clear of high-impact headwinds.")

        # 5. Momentum / RSI (10 pts)
        rsi = last_row["RSI14"]
        if 35 <= rsi <= 60:
            score += 10
            reasons.append(f"Momentum: Healthy bearish continuation zone (RSI: {rsi:.1f}).")

        return score, reasons


# Global instance
technical_engine = TechnicalEngine()
