"""
Institutional Risk Management & Lot Size Calculation Engine.
Calculates exact position sizing for XAU/USD (Gold) and Forex pairs,
enforcing strict capital preservation, fixed dollar risk (1-2%),
and multi-tiered Take Profit (TP1, TP2, TP3) targets.
"""

from typing import Dict, Any, Optional
from core.config import settings


class RiskCalculator:
    def __init__(self, default_balance: float = None, default_risk_pct: float = None):
        self.balance = default_balance or settings.ACCOUNT_BALANCE
        self.risk_pct = default_risk_pct or settings.RISK_PERCENT

    def calculate_trade_setup(
        self,
        symbol: str,
        action: str,
        entry_price: float,
        stop_loss: float,
        balance: Optional[float] = None,
        risk_pct: Optional[float] = None,
        atr_val: Optional[float] = None,
        is_volatile: Optional[bool] = None,
        custom_tp1: Optional[float] = None,
        custom_tp2: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculates exact Stop Loss distance, Recommended Lot Size, and Take Profits.
        
        Args:
            symbol: Ticker symbol (e.g. 'XAUUSD', 'GC=F', 'EURUSD')
            action: 'BUY' or 'SELL'
            entry_price: Planned entry price
            stop_loss: Planned stop loss price
            balance: Account balance (defaults to settings.ACCOUNT_BALANCE)
            risk_pct: Risk percentage per trade (defaults to settings.RISK_PERCENT)
        """
        action = action.upper()
        sym = symbol.upper().replace("/", "").replace("=X", "").replace("=F", "")
        acc_balance = balance if balance is not None else self.balance
        risk_percentage = risk_pct if risk_pct is not None else self.risk_pct
        
        risk_amount_usd = acc_balance * (risk_percentage / 100.0)
        
        # Stop loss distance
        sl_distance = abs(entry_price - stop_loss)
        if sl_distance <= 0:
            raise ValueError("Entry price and Stop Loss cannot be the same.")

        # Sanity check action vs SL
        if action == "BUY" and stop_loss >= entry_price:
            raise ValueError(f"For a BUY signal, Stop Loss ({stop_loss}) must be below Entry ({entry_price}).")
        elif action == "SELL" and stop_loss <= entry_price:
            raise ValueError(f"For a SELL signal, Stop Loss ({stop_loss}) must be above Entry ({entry_price}).")

        # 1. Determine Contract Specs and Lot Size
        is_gold = any(g in sym for g in ["XAU", "GOLD", "GC"])
        
        if is_gold:
            # 1 Standard Lot of Gold = 100 Troy Ounces
            # $1 move in gold = $100 per 1.0 lot.
            contract_multiplier = 100.0
            lot_size = risk_amount_usd / (sl_distance * contract_multiplier)
            pip_distance = sl_distance * 10  # Typically 1 pip in Gold = $0.10
        elif "JPY" in sym:
            # JPY pairs: 1 pip = 0.01. Pip value ~ $6.50 - $10 depending on USDJPY rate
            pip_distance = sl_distance / 0.01
            pip_value_std_lot = 6.80  # approximate USD per pip for 1.0 lot USDJPY
            lot_size = risk_amount_usd / (pip_distance * pip_value_std_lot)
        else:
            # Standard USD Forex pairs (EURUSD, GBPUSD, AUDUSD)
            # 1 pip = 0.0001. 1 standard lot pip value = $10.00 USD
            pip_distance = sl_distance / 0.0001
            lot_size = risk_amount_usd / (pip_distance * 10.0)

        # Apply minimum lot size (0.01) and round to 2 decimals
        recommended_lot = max(0.01, round(lot_size, 2))
        
        # Actual risked dollars based on rounded lot size
        if is_gold:
            actual_risk_usd = recommended_lot * sl_distance * 100.0
        else:
            actual_risk_usd = recommended_lot * pip_distance * 10.0

        # 2. Calculate Tiered Take Profits
        # TP1 = 1:1.5 RR (Lock 50% profit, move SL to breakeven)
        # TP2 = 1:3.0 RR (Lock 30% profit)
        # TP3 = 1:5.0 RR (Runner for max liquidity targets)
        if custom_tp1:
            tp1 = custom_tp1
        else:
            tp1 = round(entry_price + (1.5 * sl_distance) if action == "BUY" else entry_price - (1.5 * sl_distance), 2 if is_gold else 5)

        if custom_tp2:
            tp2 = custom_tp2
        else:
            tp2 = round(entry_price + (3.0 * sl_distance) if action == "BUY" else entry_price - (3.0 * sl_distance), 2 if is_gold else 5)

        tp3 = round(entry_price + (5.0 * sl_distance) if action == "BUY" else entry_price - (5.0 * sl_distance), 2 if is_gold else 5)

        # Expected gains at targets
        gain_tp1 = round(sl_distance * 1.5 * (100.0 if is_gold else 10.0) * recommended_lot, 2)
        gain_tp2 = round(sl_distance * 3.0 * (100.0 if is_gold else 10.0) * recommended_lot, 2)
        gain_tp3 = round(sl_distance * 5.0 * (100.0 if is_gold else 10.0) * recommended_lot, 2)

        # Calculate Entry Zone
        if is_gold:
            zone_buffer = 0.75
            entry_zone = f"${entry_price - zone_buffer:.2f} - ${entry_price + zone_buffer:.2f}"
        else:
            zone_buffer = 0.0003
            entry_zone = f"{entry_price - zone_buffer:.5f} - {entry_price + zone_buffer:.5f}"

        # Evaluate Market Volatility and Risk Rate
        # High Risk: Elevated ATR (> 6.0 on Gold) or high volatility flag
        # No Risk: Stable institutional volatility with calm structure
        is_high_risk = is_volatile is True or (atr_val is not None and atr_val >= 6.0)
        if is_high_risk:
            risk_rate = "High Risk"
            risk_warning = "There's a high risk in this trade"
            risk_badge = "⚠️ There's a high risk in this trade"
        else:
            risk_rate = "No Risk"
            risk_warning = "No risk"
            risk_badge = "🛡️ No risk"

        return {
            "symbol": sym,
            "action": action,
            "entry_price": round(entry_price, 2 if is_gold else 5),
            "entry_zone": entry_zone,
            "stop_loss": round(stop_loss, 2 if is_gold else 5),
            "sl_distance_points": round(sl_distance, 2 if is_gold else 5),
            "sl_distance_pips": round(pip_distance, 1),
            "risk_rate": risk_rate,
            "risk_warning": risk_warning,
            "risk_badge": risk_badge,
            "is_volatile": is_high_risk,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "risk_reward_tp1": "1:1.5",
            "risk_reward_tp2": "1:3.0",
            "risk_reward_tp3": "1:5.0",
            "account_balance": acc_balance,
            "risk_percent": risk_percentage,
            "max_dollar_risk": round(risk_amount_usd, 2),
            "actual_dollar_risk": round(actual_risk_usd, 2),
            "recommended_lot_size": recommended_lot,
            "expected_gain_tp1": gain_tp1,
            "expected_gain_tp2": gain_tp2,
            "expected_gain_tp3": gain_tp3,
            "trade_management_rules": [
                "1. Execute entry strictly within the confirmed Entry Zone.",
                "2. When TP1 is hit, close 50% of the position immediately and move Stop Loss to Breakeven (+ spread buffer).",
                "3. When TP2 is hit, close 30% of position and trail stop under previous 15m structural swing.",
                "4. Hold remaining 20% for TP3 extended runner."
            ]
        }


# Global instance
risk_calculator = RiskCalculator()
