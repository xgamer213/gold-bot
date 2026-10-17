"""
Automated Unit & Integration Test Suite for the Gold & FOREX Trading Bot.
"""

import unittest
from core.risk_calculator import RiskCalculator
from core.news_engine import EconomicEvent, NewsEngine
from core.technical_engine import TechnicalEngine


class TestTradingBot(unittest.TestCase):
    def setUp(self):
        self.risk_calc = RiskCalculator(default_balance=10000.0, default_risk_pct=1.0)
        self.tech_engine = TechnicalEngine()

    def test_gold_lot_size_calculation(self):
        """Verify exact Gold lot sizing with standard $100/point contract specification."""
        # Balance = $10,000, 1% risk = $100 risk.
        # Entry = 2650.00, SL = 2645.00 -> $5.00 distance.
        # Expected lot size = $100 / ($5.00 * 100) = 0.20 lots.
        plan = self.risk_calc.calculate_trade_setup("XAUUSD", "BUY", 2650.0, 2645.0)
        self.assertEqual(plan["recommended_lot_size"], 0.20)
        self.assertEqual(plan["max_dollar_risk"], 100.0)
        self.assertEqual(plan["tp1"], 2657.5)  # 1:1.5 RR -> 5 * 1.5 = 7.5 pts
        self.assertEqual(plan["tp2"], 2665.0)  # 1:3.0 RR -> 5 * 3 = 15 pts

    def test_forex_lot_size_calculation(self):
        """Verify standard EUR/USD lot sizing with $10/pip per standard lot."""
        # Balance = $10,000, 1% risk = $100.
        # Entry = 1.0850, SL = 1.0820 -> 30 pips distance.
        # Expected lot size = $100 / (30 * $10) = 0.33 lots.
        plan = self.risk_calc.calculate_trade_setup("EURUSD", "BUY", 1.0850, 1.0820)
        self.assertAlmostEqual(plan["recommended_lot_size"], 0.33, places=2)
        self.assertEqual(plan["sl_distance_pips"], 30.0)

    def test_economic_event_parsing(self):
        """Verify economic event parsing and tier-1 detection."""
        event_data = {
            "title": "Non-Farm Employment Change (NFP)",
            "country": "USD",
            "date": "2026-10-16T08:30:00-04:00",
            "impact": "High",
            "forecast": "150K",
            "previous": "180K",
            "actual": "130K"
        }
        ev = EconomicEvent(event_data)
        self.assertTrue(ev.is_tier_1)
        self.assertEqual(ev.impact, "High")
        self.assertEqual(ev.country, "USD")

    def test_news_bias_analysis_cpi(self):
        """Test macro bias logic: Lower CPI = Weak USD = Bullish Gold."""
        engine = NewsEngine()
        # Mock CPI event missing expectations
        cpi_ev = EconomicEvent({
            "title": "CPI m/m",
            "country": "USD",
            "date": "2026-10-14T08:30:00-04:00",
            "impact": "High",
            "forecast": "0.5%",
            "previous": "0.4%",
            "actual": "0.2%"  # Missed forecast -> Bullish for Gold
        })
        bias, reason, pts = engine._analyze_event_bias(cpi_ev)
        self.assertEqual(bias, "BULLISH")
        self.assertEqual(pts, 25)

    def test_tradingview_alert_validation(self):
        """Verify TradingView incoming alert validation and trade plan synthesis."""
        result = self.tech_engine.validate_tradingview_alert(
            symbol="XAUUSD",
            action="BUY",
            price=2700.0,
            provided_sl=2695.0
        )
        self.assertTrue(result["approved"])
        self.assertIn("trade_plan", result)
        self.assertEqual(result["trade_plan"]["entry_price"], 2700.0)
        self.assertEqual(result["trade_plan"]["stop_loss"], 2695.0)

    def test_predictive_engine_generation(self):
        """Verify predictive outlook generates scenarios, levels, and action plan."""
        from core.predictive_engine import predictive_engine
        outlook = predictive_engine.generate_market_outlook("XAUUSD")
        self.assertIn("headline", outlook)
        self.assertIn("bias", outlook)
        self.assertIn("trigger_level", outlook)
        self.assertIn("action_plan_for_user", outlook)

    def test_personalized_email_greeting(self):
        """Verify trade signal email properly greets Ahmed and includes exact parameters."""
        from core.notifier import notifier
        alert = self.tech_engine.validate_tradingview_alert("XAUUSD", "BUY", 2680.0, provided_sl=2674.0)
        plain = notifier._build_signal_plain(
            alert["symbol"], alert["signal"], alert["grade"],
            alert["confluence_score"], alert["trade_plan"],
            alert["reasons"], alert["news_eval"], user_name="Ahmed"
        )
        self.assertIn("Hey Ahmed, how're you doing?", plain)
        self.assertIn("take this trade", plain.lower())
        self.assertIn("Entry Price          : $2680.0", plain)
        self.assertIn("Stop Loss (SL)       : $2674.0", plain)
    def test_chat_engine_dialogue(self):
        """Verify chat assistant answers greeting, lot calculation, and trade review."""
        from core.chat_engine import chat_engine
        # 1. Greeting
        greet_res = chat_engine.respond("Hey how are you?")
        self.assertIn("Hey Ahmed", greet_res)

        # 2. Lot calculation query
        lot_res = chat_engine.respond("Calculate lot size for $5000 balance and $6 SL on Gold")
        self.assertIn("RECOMMENDED LOT SIZE", lot_res)

        # 3. Trade discussion
        trade_res = chat_engine.respond("Should I buy Gold at 2685 with SL 2679?")
        self.assertIn("TRADE REVIEW FOR AHMED", trade_res)
        self.assertIn("Planned Entry: $2,685.00", trade_res)

    def test_pre_news_alert_format(self):
        """Verify 30-minute pre-news warning email contains event details and user greeting."""
        from core.notifier import notifier
        from core.news_engine import EconomicEvent
        ev = EconomicEvent({
            "title": "Non-Farm Payrolls (NFP)",
            "country": "USD",
            "date": "2026-10-16T08:30:00-04:00",
            "impact": "High",
            "forecast": "150K",
            "previous": "180K"
        })
        plain = notifier._build_pre_news_plain(ev, user_name="Ahmed")
        self.assertIn("HEY AHMED! BE READY - NEWS IN 30 MINUTES", plain)
        self.assertIn("Non-Farm Payrolls (NFP)", plain)
        self.assertIn("New trade entries are FROZEN", plain)

    def test_risk_rate_and_entry_zone(self):
        """Verify dynamic risk rate (high risk in volatile vs no risk in calm) and entry zone."""
        # Calm market
        calm_plan = self.risk_calc.calculate_trade_setup("XAUUSD", "BUY", 2680.0, 2674.0, atr_val=3.5)
        self.assertEqual(calm_plan["risk_warning"], "No risk")
        self.assertEqual(calm_plan["risk_badge"], "🛡️ No risk")
        self.assertIn("2679.25 - $2680.75", calm_plan["entry_zone"])

        # Volatile market
        volatile_plan = self.risk_calc.calculate_trade_setup("XAUUSD", "BUY", 2680.0, 2674.0, atr_val=7.5)
        self.assertEqual(volatile_plan["risk_warning"], "There's a high risk in this trade")
        self.assertEqual(volatile_plan["risk_badge"], "⚠️ There's a high risk in this trade")

        # Verify Plain signal output contains exact wording
        from core.notifier import notifier
        signal_text = notifier._build_signal_plain("XAUUSD", "BUY", "Grade A+", 95, volatile_plan, ["Test reason"], {"reason": "Clear"}, "Ahmed")
        self.assertIn("Risk Rate            : ⚠️ There's a high risk in this trade", signal_text)
        self.assertIn("Entry Zone           : $2679.25 - $2680.75", signal_text)
        self.assertIn("Stop Loss (SL)       : $2674.0", signal_text)
        self.assertIn("Take Profit 1 (TP1)  : $2689.0", signal_text)


if __name__ == "__main__":
    unittest.main()
