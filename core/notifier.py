"""
Email Notification & Alert Dispatcher.
Sends high-priority HTML emails with exact Entry, Stop Loss, Take Profit 1/2/3,
recommended Lot Size, and ForexFactory News Catalyst analysis.
"""

import smtplib
import sys
import logging
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, List

# Ensure Windows console supports Unicode / emojis safely
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from core.config import settings

logger = logging.getLogger("Notifier")


class Notifier:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.receiver = settings.NOTIFICATION_RECEIVER_EMAIL
        self.enabled = settings.EMAIL_ENABLED

    def send_trade_signal(self, setup_data: Dict[str, Any]) -> bool:
        """
        Formats and dispatches an institutional trade alert email.
        Also prints formatted signal to console.
        """
        symbol = setup_data.get("symbol", "XAUUSD")
        signal = setup_data.get("signal", "BUY")
        grade = setup_data.get("grade", "Grade A+")
        score = setup_data.get("confluence_score", 90)
        trade_plan = setup_data.get("trade_plan", {})
        reasons = setup_data.get("reasons", [])
        news_eval = setup_data.get("news_eval", {})

        # 1. Print formatted console alert
        self._print_console_signal(setup_data)

        name = settings.USER_NAME or "Ahmed"
        text_content = self._build_signal_plain(symbol, signal, grade, score, trade_plan, reasons, news_eval, user_name=name)

        # 2. Dispatch to Telegram & Discord (Instant Alerts)
        self.send_telegram_message(text_content)
        self.send_discord_message(text_content)

        # 3. Dispatch to Email
        if not self.enabled or not self.receiver or not self.username:
            logger.info("Email notifications are disabled or SMTP credentials not configured in .env. Skipping email dispatch.")
            return True

        subject = f"🚨 Hey {name}! High-Accuracy {grade} {signal}: {symbol} @ {trade_plan.get('entry_price')} (Take This Trade)"
        html_content = self._build_signal_html(symbol, signal, grade, score, trade_plan, reasons, news_eval, user_name=name)

        return self._send_email(subject, html_content, text_content)

    def send_telegram_message(self, message: str) -> bool:
        """Sends an instant notification to Ahmed's Telegram."""
        if not settings.TELEGRAM_ENABLED or not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            return False

        try:
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": message
            }
            proxies = {"http": settings.TELEGRAM_PROXY, "https": settings.TELEGRAM_PROXY} if getattr(settings, "TELEGRAM_PROXY", None) else None
            res = requests.post(url, json=payload, timeout=10, proxies=proxies)
            if res.status_code == 200:
                logger.info("Telegram notification successfully sent!")
                return True
            else:
                logger.warning(f"Telegram API response HTTP {res.status_code}: {res.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False

    def send_test_telegram(self) -> Dict[str, Any]:
        """Dispatches a test message to verify Telegram setup."""
        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            return {
                "success": False,
                "error": "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing in .env"
            }
        name = settings.USER_NAME or "Ahmed"
        msg = f"🚀 Hey {name}!\nYour Telegram alert bridge is connected successfully! You will now receive high-accuracy Gold signals and 30-min pre-news warnings directly here."
        success = self.send_telegram_message(msg)
        return {"success": success}

    def send_discord_message(self, message: str) -> bool:
        """Sends an instant notification to Ahmed's Discord channel."""
        if not settings.DISCORD_ENABLED or not settings.DISCORD_WEBHOOK_URL:
            return False

        try:
            payload = {"content": message}
            res = requests.post(settings.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            if res.status_code in [200, 204]:
                logger.info("Discord notification successfully sent!")
                return True
            else:
                logger.warning(f"Discord API response HTTP {res.status_code}: {res.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
            return False

    def send_test_discord(self) -> Dict[str, Any]:
        """Dispatches a test message to verify Discord setup."""
        if not settings.DISCORD_WEBHOOK_URL:
            return {
                "success": False,
                "error": "DISCORD_WEBHOOK_URL is missing in .env"
            }
        name = settings.USER_NAME or "Ahmed"
        msg = f"🚀 **Hey {name}!**\nYour Discord alert bridge is connected successfully! You will now receive high-accuracy Gold signals and 30-min pre-news warnings directly here."
        success = self.send_discord_message(msg)
        return {"success": success}

    def send_predictive_outlook_email(self, outlook: Dict[str, Any]) -> bool:
        """Sends a forward-looking market prediction email and Telegram alert."""
        name = settings.USER_NAME or "Ahmed"
        headline = outlook.get("headline", "Gold Market Prediction")
        
        subject = f"🔮 Hey {name}! Market Prediction: {headline}"
        html_content = self._build_predictive_html(outlook, user_name=name)
        text_content = self._build_predictive_plain(outlook, user_name=name)

        # Print to console
        self._print_console_outlook(outlook)

        # Dispatch to Telegram
        self.send_telegram_message(text_content)

        if not self.enabled or not self.receiver or not self.username:
            logger.info("Email notifications disabled. Prediction printed to console and sent to Telegram.")
            return False

        return self._send_email(subject, html_content, text_content)

    def send_pre_news_alert(self, event: Any) -> bool:
        """
        Dispatches a 30-minute advance warning to Ahmed via Telegram and Email.
        """
        name = settings.USER_NAME or "Ahmed"
        subject = f"⚠️ Hey {name}! Be Ready - High-Impact News in 30 Mins: {event.title} ({event.country})"
        
        html_content = self._build_pre_news_html(event, user_name=name)
        text_content = self._build_pre_news_plain(event, user_name=name)

        # Print warning to console
        print("\n" + "!" * 65)
        print(f" [30-MINUTE NEWS ALERT FOR {name.upper()}]")
        print("!" * 65)
        print(f"  * Event    : {event.country} {event.title} (Impact: {event.impact})")
        print(f"  * Scheduled: {event.date_str}")
        print(f"  * Forecast : {event.forecast or 'N/A'} | Previous: {event.previous or 'N/A'}")
        print("  * NOTICE   : Trading is now FROZEN. Protect open trades!")
        print("!" * 65 + "\n")

        # Dispatch to Telegram
        self.send_telegram_message(text_content)

        if not self.enabled or not self.receiver or not self.username:
            logger.info("Email notifications disabled. Pre-news warning sent to Telegram.")
            return False

        return self._send_email(subject, html_content, text_content)

    def send_market_update(self, gold_price: float, upcoming_news: List[Any], bias: str) -> bool:
        """Sends a daily or periodic market briefing email."""
        if not self.enabled or not self.receiver or not self.username:
            return False

        name = settings.USER_NAME or "Ahmed"
        subject = f"📊 Hey {name}! Daily Market Intelligence: Gold (XAU/USD) @ ${gold_price:.2f} | Bias: {bias}"
        html_content = self._build_market_update_html(gold_price, upcoming_news, bias)
        text_content = f"Daily Market Update for {name} - Gold: ${gold_price:.2f}, Bias: {bias}, Upcoming High Impact Events: {len(upcoming_news)}"

        return self._send_email(subject, html_content, text_content)

    def send_test_email(self) -> Dict[str, Any]:
        """Dispatches a test signal to verify SMTP connection."""
        if not self.username or not self.password or not self.receiver:
            return {
                "success": False,
                "error": "SMTP_USERNAME, SMTP_PASSWORD, or NOTIFICATION_RECEIVER_EMAIL is missing in .env"
            }

        mock_setup = {
            "symbol": "XAUUSD (GOLD)",
            "signal": "BUY",
            "grade": "Grade A+ (Institutional Verification)",
            "confluence_score": 95,
            "trade_plan": {
                "symbol": "XAUUSD",
                "action": "BUY",
                "entry_price": 2680.50,
                "stop_loss": 2674.50,
                "sl_distance_points": 6.00,
                "sl_distance_pips": 60.0,
                "tp1": 2689.50,
                "tp2": 2698.50,
                "tp3": 2710.50,
                "account_balance": settings.ACCOUNT_BALANCE,
                "risk_percent": settings.RISK_PERCENT,
                "max_dollar_risk": settings.ACCOUNT_BALANCE * (settings.RISK_PERCENT / 100.0),
                "recommended_lot_size": round((settings.ACCOUNT_BALANCE * (settings.RISK_PERCENT / 100.0)) / 600.0, 2),
                "expected_gain_tp1": 150.0,
                "expected_gain_tp2": 300.0,
                "trade_management_rules": [
                    "Execute immediately at 2680.50.",
                    "TP1: Close 50% lot size and move SL to 2680.50 (Breakeven).",
                    "TP2: Close 30% lot size.",
                    "TP3: Trail remaining 20% for runner."
                ]
            },
            "reasons": [
                "London Session High Swept followed by strong bullish Market Structure Shift.",
                "15m Fair Value Gap (FVG) respected with rejection wick.",
                "ForexFactory Macro Confluence: Core CPI missed forecast, weakening USD."
            ],
            "news_eval": {
                "status": "POST_NEWS_CATALYST",
                "fundamental_bias": "BULLISH",
                "reason": "Core CPI data came in softer than expected. Dollar Index (DXY) rejecting resistance."
            }
        }

        subject = "🧪 [TEST CONFIRMED] Gold & Forex Institutional Alert System"
        html = self._build_signal_html("XAUUSD", "BUY", "TEST SIGNAL", 95, mock_setup["trade_plan"], mock_setup["reasons"], mock_setup["news_eval"])
        plain = "Test Alert from FOREX & Gold Bot"

        success = self._send_email(subject, html, plain)
        return {"success": success, "recipient": self.receiver}

    def _send_email(self, subject: str, html_body: str, plain_body: str) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"Gold Sniper Bot <{self.username}>"
            msg["To"] = self.receiver

            msg.attach(MIMEText(plain_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.username, [self.receiver], msg.as_string())

            logger.info(f"Email successfully dispatched to {self.receiver}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email via {self.smtp_server}: {e}")
            return False

    def _print_console_signal(self, data: Dict[str, Any]):
        try:
            plan = data.get("trade_plan", {})
            news = data.get("news_eval", {})
            action = data.get("signal", "BUY")
            color_tag = "[BUY]" if action == "BUY" else "[SELL]"

            print("\n" + "=" * 65)
            print(f" {color_tag} INSTITUTIONAL SIGNAL TRIGGERED: {data.get('symbol')} {action} ({data.get('grade')})")
            print("=" * 65)
            print(f"  * Confluence Score   : {data.get('confluence_score')}% (Target: {settings.MIN_CONFLUENCE_SCORE}%+)")
            print(f"  * Entry Price        : ${plan.get('entry_price', 'N/A')}")
            print(f"  * Stop Loss          : ${plan.get('stop_loss', 'N/A')} (Risk: {plan.get('sl_distance_points')} pts / {plan.get('sl_distance_pips')} pips)")
            print(f"  * Take Profit 1 (1:1.5) : ${plan.get('tp1', 'N/A')} (Close 50% + Move SL to Breakeven)")
            print(f"  * Take Profit 2 (1:3.0) : ${plan.get('tp2', 'N/A')} (Target Swing High/Low)")
            print(f"  * Take Profit 3 (Runner): ${plan.get('tp3', 'N/A')}")
            print(f"  * RECOMMENDED LOT    : {plan.get('recommended_lot_size')} Lots (Account: ${plan.get('account_balance')} @ {plan.get('risk_percent')}%)")
            print(f"  * Max Risk Exposure  : ${plan.get('max_dollar_risk')}")
            print(f"  * Expected Gain TP1  : +${plan.get('expected_gain_tp1')} | TP2: +${plan.get('expected_gain_tp2')}")
            print("-" * 65)
            print(f"  News Confluence      : {news.get('status')} - {news.get('reason')}")
            print("  Technical Confluence Reasons:")
            for r in data.get("reasons", []):
                print(f"     - {r}")
            print("=" * 65 + "\n")
        except Exception as e:
            logger.error(f"Error printing signal to console: {e}")

    def _build_signal_html(self, symbol, signal, grade, score, plan, reasons, news, user_name="Ahmed") -> str:
        action_color = "#10b981" if signal == "BUY" else "#ef4444"
        reasons_html = "".join([f"<li style='margin-bottom:6px; color:#cbd5e1;'>{r}</li>" for r in reasons])

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 12px; border: 1px solid #334155; overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 24px; border-bottom: 2px solid {action_color}; text-align: center; }}
            .title {{ font-size: 24px; font-weight: bold; margin: 0; color: #f8fafc; }}
            .badge {{ display: inline-block; padding: 6px 14px; border-radius: 20px; background-color: {action_color}; color: #ffffff; font-weight: bold; font-size: 14px; margin-top: 10px; }}
            .greeting-box {{ background-color: #1e3a8a; border-left: 5px solid #3b82f6; padding: 14px 18px; border-radius: 6px; margin-bottom: 20px; font-size: 15px; color: #ffffff; line-height: 1.5; }}
            .content {{ padding: 24px; }}
            .card {{ background-color: #0f172a; border-radius: 8px; border: 1px solid #334155; padding: 16px; margin-bottom: 16px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
            .metric-box {{ background-color: #1e293b; padding: 12px; border-radius: 6px; text-align: center; }}
            .metric-label {{ font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.5px; margin-bottom: 4px; }}
            .metric-val {{ font-size: 18px; font-weight: bold; color: #f8fafc; }}
            .highlight {{ color: {action_color}; font-size: 22px; }}
            .lot-highlight {{ color: #f59e0b; font-size: 24px; font-weight: 800; }}
            .news-box {{ background-color: #172554; border-left: 4px solid #3b82f6; padding: 12px; border-radius: 4px; margin-bottom: 16px; font-size: 13px; color: #93c5fd; }}
            .footer {{ padding: 16px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #334155; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div class="title">🪙 {symbol} INSTITUTIONAL SIGNAL</div>
              <div class="badge">{signal} | {grade} ({score}% Confluence)</div>
            </div>
            <div class="content">
              
              <div class="greeting-box">
                👋 <strong>Hey {user_name}, how're you doing?</strong><br>
                I've found a clear setup of high accuracy (<strong>{score}% Confluence</strong>). Take this trade!
              </div>

              <div class="card" style="text-align:center; border: 2px solid #f59e0b;">
                <div class="metric-label">RECOMMENDED POSITION SIZE</div>
                <div class="lot-highlight">{plan.get('recommended_lot_size', '0.10')} LOTS</div>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">Based on ${plan.get('account_balance', 10000)} Account @ {plan.get('risk_percent', 1.0)}% Risk (${plan.get('max_dollar_risk', 100)} Max Loss)</div>
              </div>

              <div class="card">
                <div style="font-size: 14px; font-weight: bold; color: #94a3b8; margin-bottom: 12px;">EXECUTION SPECIFICATIONS</div>
                <div class="grid">
                  <div class="metric-box">
                    <div class="metric-label">Entry Price</div>
                    <div class="metric-val highlight">${plan.get('entry_price')}</div>
                  </div>
                  <div class="metric-box">
                    <div class="metric-label">Stop Loss (SL)</div>
                    <div class="metric-val" style="color:#ef4444;">${plan.get('stop_loss')}</div>
                  </div>
                  <div class="metric-box">
                    <div class="metric-label">Take Profit 1 (TP1)</div>
                    <div class="metric-val" style="color:#10b981;">${plan.get('tp1')}</div>
                    <div style="font-size: 11px; color: #64748b;">+$ {plan.get('expected_gain_tp1')}</div>
                  </div>
                  <div class="metric-box">
                    <div class="metric-label">Take Profit 2 (TP2)</div>
                    <div class="metric-val" style="color:#10b981;">${plan.get('tp2')}</div>
                    <div style="font-size: 11px; color: #64748b;">+$ {plan.get('expected_gain_tp2')}</div>
                  </div>
                </div>
              </div>

              <div class="news-box">
                <strong>📰 ForexFactory News Alignment:</strong><br>
                {news.get('reason', 'Market clear of conflicting high-impact shocks.')}
              </div>

              <div class="card">
                <div style="font-size: 14px; font-weight: bold; color: #94a3b8; margin-bottom: 10px;">CONFLUENCE REASONS</div>
                <ul style="padding-left: 20px; margin: 0;">
                  {reasons_html}
                </ul>
              </div>

              <div class="card" style="font-size: 12px; color: #94a3b8; line-height: 1.6;">
                <strong>⚡ TRADE MANAGEMENT PROTOCOL:</strong><br>
                1. Enter at confirmed entry.<br>
                2. When <strong>TP1</strong> is hit, close 50% and move Stop Loss to Breakeven.<br>
                3. Let remaining 50% run toward TP2 / TP3.<br>
              </div>

            </div>
            <div class="footer">
              Automated Institutional Trading System • ForexFactory & TradingView Engine
            </div>
          </div>
        </body>
        </html>
        """

    def _build_signal_plain(self, symbol, signal, grade, score, plan, reasons, news, user_name="Ahmed") -> str:
        return f"""
=========================================
🚨 HEY {user_name.upper()}! TRADE SIGNAL ({grade})
=========================================
Hey {user_name}, how're you doing?
I've found a clear setup of high accuracy ({score}% Confluence). Take this trade!

Pair                 : {symbol}
Action               : {signal}
Entry Price          : ${plan.get('entry_price')}
Stop Loss (SL)       : ${plan.get('stop_loss')}
Take Profit 1 (TP1)  : ${plan.get('tp1')}
Take Profit 2 (TP2)  : ${plan.get('tp2')}
Take Profit 3 (TP3)  : ${plan.get('tp3')}

RECOMMENDED LOT SIZE : {plan.get('recommended_lot_size')} Lots
Account Balance      : ${plan.get('account_balance')} (Risk: {plan.get('risk_percent')}%)
Max Dollar Risk      : ${plan.get('max_dollar_risk')}

ForexFactory News Confluence:
{news.get('reason')}

Technical Confluence:
{chr(10).join(['- ' + r for r in reasons])}

Trade Management:
- Close 50% at TP1, move SL to Breakeven.
=========================================
"""

    def _build_predictive_html(self, outlook: Dict[str, Any], user_name="Ahmed") -> str:
        headline = outlook.get("headline", "Market Outlook")
        bias = outlook.get("bias", "NEUTRAL")
        badge_color = "#ef4444" if "CRASH" in bias or "BEARISH" in bias else "#10b981"
        catalyst = outlook.get("upcoming_catalyst")
        cat_text = f"{catalyst.get('country')} {catalyst.get('title')} ({catalyst.get('impact')})" if catalyst else "Upcoming Macro Inflation/Rate Releases"

        return f"""
        <!DOCTYPE html>
        <html>
        <body style="background-color: #0f172a; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px;">
          <div style="max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 24px; border: 1px solid #334155;">
            
            <div style="background-color: #1e3a8a; border-left: 5px solid #3b82f6; padding: 14px 18px; border-radius: 6px; margin-bottom: 20px; font-size: 15px; color: #ffffff;">
              👋 <strong>Hey {user_name}, how're you doing?</strong><br>
              Here is your forward-looking market prediction and structural intelligence briefing for Gold (XAU/USD).
            </div>

            <div style="border-bottom: 2px solid {badge_color}; padding-bottom: 12px; margin-bottom: 16px;">
              <span style="background-color: {badge_color}; color: #ffffff; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                {bias}
              </span>
              <h2 style="color: #f8fafc; margin-top: 10px; font-size: 20px;">{headline}</h2>
            </div>

            <div style="background-color: #0f172a; padding: 16px; border-radius: 8px; margin-bottom: 16px; border: 1px solid #334155;">
              <div style="font-size: 13px; color: #94a3b8; text-transform: uppercase; margin-bottom: 8px;">Key Structural Levels</div>
              <table style="width: 100%; font-size: 14px;">
                <tr><td style="color: #94a3b8;">Current Price:</td><td style="font-weight:bold; color:#f8fafc;">${outlook.get('current_price')}</td></tr>
                <tr><td style="color: #ef4444;">Key Resistance:</td><td style="font-weight:bold; color:#ef4444;">${outlook.get('resistance')}</td></tr>
                <tr><td style="color: #10b981;">Key Support:</td><td style="font-weight:bold; color:#10b981;">${outlook.get('support')}</td></tr>
                <tr><td style="color: #f59e0b;">Break/Trigger Level:</td><td style="font-weight:bold; color:#f59e0b;">${outlook.get('trigger_level')}</td></tr>
                <tr><td style="color: #38bdf8;">Target 1:</td><td style="font-weight:bold; color:#38bdf8;">${outlook.get('target_1')}</td></tr>
              </table>
            </div>

            <div style="background-color: #172554; border-left: 4px solid #3b82f6; padding: 12px; border-radius: 4px; margin-bottom: 16px; font-size: 13px; color: #93c5fd;">
              <strong>📅 Upcoming ForexFactory Catalyst:</strong><br>
              {cat_text}
            </div>

            <div style="margin-bottom: 16px; line-height: 1.6; font-size: 14px; color: #cbd5e1;">
              <strong>🔍 Detailed Market Analysis:</strong><br>
              {outlook.get('detailed_analysis')}
            </div>

            <div style="background-color: #0f172a; border-left: 4px solid #10b981; padding: 14px; border-radius: 4px; font-size: 13px; color: #e2e8f0; line-height: 1.5;">
              <strong>🎯 Strategic Action Plan for {user_name}:</strong><br>
              {outlook.get('action_plan_for_user')}
            </div>

            <div style="text-align: center; margin-top: 20px; font-size: 11px; color: #64748b;">
              Gold Institutional Prediction Engine • ForexFactory & SMC Model
            </div>
          </div>
        </body>
        </html>
        """

    def _build_predictive_plain(self, outlook: Dict[str, Any], user_name="Ahmed") -> str:
        return f"""
=====================================================
🔮 HEY {user_name.upper()}! MARKET PREDICTION BRIEFING
=====================================================
Hey {user_name}, how're you doing?
Here is your forward-looking market prediction for Gold (XAU/USD):

Headline       : {outlook.get('headline')}
Regime / Bias  : {outlook.get('bias')}
Current Price  : ${outlook.get('current_price')}
Resistance     : ${outlook.get('resistance')}
Support        : ${outlook.get('support')}
Trigger Level  : ${outlook.get('trigger_level')}
Target 1       : ${outlook.get('target_1')}

Detailed Analysis:
{outlook.get('detailed_analysis')}

Action Plan:
{outlook.get('action_plan_for_user')}
=====================================================
"""

    def _print_console_outlook(self, outlook: Dict[str, Any]):
        name = settings.USER_NAME or "Ahmed"
        print("\n" + "=" * 65)
        print(f" [MARKET PREDICTION FOR {name.upper()}]")
        print("=" * 65)
        print(f"  * Headline    : {outlook.get('headline')}")
        print(f"  * Bias        : {outlook.get('bias')}")
        print(f"  * Price       : ${outlook.get('current_price')}")
        print(f"  * Resistance  : ${outlook.get('resistance')} | Support: ${outlook.get('support')}")
        print(f"  * Trigger     : ${outlook.get('trigger_level')} | Target: ${outlook.get('target_1')}")
        print("-" * 65)
        print(f"  Analysis:\n    {outlook.get('detailed_analysis')}")
        print(f"  Action Plan for {name}:\n    {outlook.get('action_plan_for_user')}")
        print("=" * 65 + "\n")

    def _build_market_update_html(self, gold_price: float, upcoming_news: List[Any], bias: str) -> str:
        news_items = ""
        for ev in upcoming_news:
            news_items += f"""
            <tr style="border-bottom: 1px solid #334155;">
              <td style="padding: 8px; color: #f8fafc;"><strong>{ev.country}</strong></td>
              <td style="padding: 8px; color: #cbd5e1;">{ev.title}</td>
              <td style="padding: 8px; color: #ef4444; font-weight: bold;">{ev.impact}</td>
              <td style="padding: 8px; color: #94a3b8;">{ev.forecast}</td>
            </tr>
            """
        return f"""
        <!DOCTYPE html>
        <html>
        <body style="background-color: #0f172a; color: #f8fafc; font-family: sans-serif; padding: 20px;">
          <div style="max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 10px; padding: 20px; border: 1px solid #334155;">
            <h2 style="color: #f59e0b; margin-top: 0;">📊 Daily Gold & Macroeconomic Briefing</h2>
            <p><strong>Current Gold (XAU/USD) Price:</strong> ${gold_price:.2f}</p>
            <p><strong>Fundamental Macro Bias:</strong> <span style="color:#10b981; font-weight:bold;">{bias}</span></p>
            <hr style="border-color: #334155;">
            <h3>Upcoming High-Impact ForexFactory Events (Next 24h)</h3>
            <table style="width: 100%; text-align: left; border-collapse: collapse; font-size: 13px;">
              <thead>
                <tr style="color: #94a3b8; border-bottom: 2px solid #475569;">
                  <th style="padding: 8px;">Ccy</th>
                  <th style="padding: 8px;">Event</th>
                  <th style="padding: 8px;">Impact</th>
                  <th style="padding: 8px;">Forecast</th>
                </tr>
              </thead>
              <tbody>
                {news_items if news_items else "<tr><td colspan='4' style='padding:12px; text-align:center; color:#94a3b8;'>No immediate Red-Folder events scheduled. Normal market structure active.</td></tr>"}
              </tbody>
            </table>
          </div>
        </body>
        </html>
        """

    def _build_pre_news_html(self, event: Any, user_name="Ahmed") -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <body style="background-color: #0f172a; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px;">
          <div style="max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 24px; border: 1px solid #ef4444;">
            
            <div style="background-color: #7f1d1d; border-left: 5px solid #ef4444; padding: 14px 18px; border-radius: 6px; margin-bottom: 20px; font-size: 16px; color: #ffffff;">
              [ALERT] <strong>Hey {user_name}, be ready! News coming out in 30 minutes!</strong><br>
              High-impact macroeconomic data is about to release on ForexFactory.
            </div>

            <div style="background-color: #0f172a; padding: 16px; border-radius: 8px; margin-bottom: 16px; border: 1px solid #334155;">
              <table style="width: 100%; font-size: 14px;">
                <tr><td style="color: #94a3b8; padding: 6px 0;">Event:</td><td style="font-weight:bold; color:#f8fafc;">{event.title}</td></tr>
                <tr><td style="color: #94a3b8; padding: 6px 0;">Currency:</td><td style="font-weight:bold; color:#ef4444;">{event.country} (High Impact)</td></tr>
                <tr><td style="color: #94a3b8; padding: 6px 0;">Scheduled:</td><td style="color:#f8fafc;">{event.date_str}</td></tr>
                <tr><td style="color: #94a3b8; padding: 6px 0;">Forecast:</td><td style="color:#38bdf8;">{event.forecast or 'N/A'}</td></tr>
                <tr><td style="color: #94a3b8; padding: 6px 0;">Previous:</td><td style="color:#94a3b8;">{event.previous or 'N/A'}</td></tr>
              </table>
            </div>

            <div style="background-color: #172554; border-left: 4px solid #3b82f6; padding: 14px; border-radius: 4px; margin-bottom: 16px; font-size: 13px; color: #93c5fd; line-height: 1.6;">
              <strong>[ACTION PROTOCOL FOR {user_name.upper()}]:</strong><br>
              1. <strong>NO NEW TRADES</strong>: The bot has locked new entries to prevent spread widening and slippage.<br>
              2. <strong>PROTECT OPEN TRADES</strong>: Move Stop Loss on any open Gold trades to Breakeven or take partial profits.<br>
              3. <strong>WAIT FOR POST-NEWS CONFIRMATION</strong>: Let the initial 5-10 minute spike settle. The bot will analyze Actual vs Forecast and send you the high-confluence entry!
            </div>

            <div style="text-align: center; margin-top: 20px; font-size: 11px; color: #64748b;">
              ForexFactory Macro Alert Engine • Automated News Shield
            </div>
          </div>
        </body>
        </html>
        """

    def _build_pre_news_plain(self, event: Any, user_name="Ahmed") -> str:
        return f"""
=====================================================
⚠️ HEY {user_name.upper()}! BE READY - NEWS IN 30 MINUTES
=====================================================
Hey {user_name}, be ready! High-impact news coming out in 30 minutes!

Event       : {event.country} {event.title}
Impact      : {event.impact}
Scheduled   : {event.date_str}
Forecast    : {event.forecast or 'N/A'}
Previous    : {event.previous or 'N/A'}

ACTION PLAN:
1. New trade entries are FROZEN to protect capital.
2. Protect open positions: move Stop Loss to Breakeven.
3. Wait for post-news confirmation after spreads settle.
=====================================================
"""


# Global instance
notifier = Notifier()
