"""
Main Orchestration & CLI Command Center for the Gold & FOREX Trading Bot.
Provides Webhook Server, Live Autonomous Market Scanner, ForexFactory News Monitor,
and Email Alert Dispatcher.
"""

import sys
import argparse
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler

# Ensure Windows terminal encoding safety
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from core.config import settings
from core.news_engine import news_engine
from core.technical_engine import technical_engine
from core.predictive_engine import predictive_engine
from core.chat_engine import chat_engine
from core.notifier import notifier
from core.telegram_engine import telegram_chat_engine
from core.webhook_server import app


def print_banner():
    banner = f"""
========================================================================
       GOLD (XAU/USD) & FOREX INSTITUTIONAL TRADING BOT
========================================================================
 Trader / Recipient  : {settings.USER_NAME}
 Primary Asset       : {settings.PRIMARY_SYMBOL}
 Account Balance     : ${settings.ACCOUNT_BALANCE:,.2f} USD
 Risk Per Trade      : {settings.RISK_PERCENT}% (${settings.ACCOUNT_BALANCE * (settings.RISK_PERCENT / 100):,.2f})
 Confluence Filter   : {settings.MIN_CONFLUENCE_SCORE}% Minimum Score (Grade A+ only)
 ForexFactory News   : {"ACTIVE (Pre-event freeze: " + str(settings.NEWS_PRE_EVENT_FREEZE_MINS) + "m)" if settings.NEWS_FILTER_ENABLED else "DISABLED"}
 Email Notifications : {"ENABLED (To: " + settings.NOTIFICATION_RECEIVER_EMAIL + ")" if settings.EMAIL_ENABLED else "DISABLED (Configure .env)"}
 Telegram Alerts     : {"ENABLED (Chat ID: " + str(settings.TELEGRAM_CHAT_ID) + ")" if settings.TELEGRAM_BOT_TOKEN else "PENDING BOT TOKEN (Configure .env)"}
 Webhook Port        : {settings.WEBHOOK_PORT} (TradingView Bridge)
========================================================================
"""
    print(banner)


def run_predictive_outlook():
    """Generates market prediction and emails forward-looking outlook."""
    print(f"\n[PREDICTION] Generating forward-looking market prediction for {settings.USER_NAME}...")
    outlook = predictive_engine.generate_market_outlook(settings.PRIMARY_SYMBOL)
    notifier.send_predictive_outlook_email(outlook)


def run_scheduled_scan():
    """Periodic scanner for autonomous signal generation."""
    print(f"\n[SCANNER] Running periodic confluence scan on {settings.PRIMARY_SYMBOL}...")
    result = technical_engine.evaluate_live_chart(settings.PRIMARY_SYMBOL)
    signal = result.get("signal")
    if signal in ["BUY", "SELL"]:
        notifier.send_trade_signal(result)
    else:
        print(f"[SCANNER] {result.get('reason')}")


def run_news_refresh():
    """Refreshes ForexFactory economic calendar."""
    print("\n[NEWS] Refreshing ForexFactory calendar feed...")
    news_engine.refresh_calendar(force=True)
    eval_res = news_engine.evaluate_gold_threat_and_bias()
    print(f"[NEWS] Threat Status: {eval_res['status']} | Macro Bias: {eval_res['fundamental_bias']}")


def display_news_calendar():
    """Prints this week's high-impact economic calendar."""
    print("\n" + "=" * 70)
    print(" 📰 FOREXFACTORY HIGH-IMPACT CALENDAR (CPI, NFP, FED, PPI)")
    print("=" * 70)
    events = [e for e in news_engine.events if e.impact == "High" or e.is_tier_1]
    if not events:
        print("  No High-Impact events found for the current period.")
    else:
        for ev in events:
            tier_badge = "[TIER 1]" if ev.is_tier_1 else "[HIGH]"
            print(f"  {tier_badge} [{ev.country}] {ev.title}")
            print(f"         Time: {ev.date_str} | Forecast: {ev.forecast or 'N/A'} | Prev: {ev.previous or 'N/A'}")
    print("=" * 70 + "\n")


def test_tradingview_simulation():
    """Simulates an incoming webhook from TradingView to verify signal pipeline."""
    print("\n[TEST] Simulating TradingView BUY Webhook for XAU/USD at $2690.00...")
    alert_result = technical_engine.validate_tradingview_alert(
        symbol="XAUUSD",
        action="BUY",
        price=2690.00,
        strategy_name="GoldSniper_Pine_A_Plus",
        provided_sl=2684.00
    )
    notifier.send_trade_signal(alert_result)
    print("[TEST] Simulation complete.\n")


def run_interactive_cli_chat():
    """Starts interactive terminal chat session with Ahmed."""
    name = settings.USER_NAME or "Ahmed"
    print(f"\n💬 Starting Interactive Trade Chat Session with {name}...")
    print(" Type 'exit' or 'quit' to end chat.\n")
    print(f"Bot > Hey {name}! I am your Gold & Forex trade assistant. What would you like to discuss?")
    while True:
        try:
            user_input = input(f"\n{name} > ")
            if not user_input.strip():
                continue
            if user_input.strip().lower() in ["exit", "quit", "q"]:
                print(f"\nBot > Good luck with your trading, {name}! Trade safe.\n")
                break
            response = chat_engine.respond(user_input)
            print(f"\nBot > {response}")
        except (KeyboardInterrupt, EOFError):
            print(f"\nBot > Session closed. Goodbye, {name}!\n")
            break


def test_pre_news_alert_simulation():
    """Simulates 30-minute pre-news warning email for Ahmed."""
    from core.news_engine import EconomicEvent
    name = settings.USER_NAME or "Ahmed"
    print(f"\n[TEST] Simulating 30-Minute Pre-News Alert for {name} (CPI Release)...")
    mock_event = EconomicEvent({
        "title": "CPI m/m (Consumer Price Index)",
        "country": "USD",
        "date": "2026-10-14T08:30:00-04:00",
        "impact": "High",
        "forecast": "0.4%",
        "previous": "0.3%",
        "actual": ""
    })
    notifier.send_pre_news_alert(mock_event)
    print("[TEST] 30m Pre-News simulation complete.\n")


def main():
    parser = argparse.ArgumentParser(description="Gold & FOREX Institutional Trading Bot")
    parser.add_argument(
        "--mode",
        choices=["server", "scan", "news", "predict", "chat", "telegram", "test-email", "test-telegram", "test-discord", "test-webhook", "test-news-alert"],
        default="server",
        help="Run mode: server, scan, news, predict, chat, telegram, test-email, test-telegram, test-discord, test-webhook, or test-news-alert"
    )
    args = parser.parse_args()

    print_banner()

    if args.mode == "chat":
        run_interactive_cli_chat()

    elif args.mode == "telegram":
        print(f"\n📱 Starting Telegram 2-Way Chat Bot for {settings.USER_NAME}...")
        print("Listening for messages in Telegram. Open your Telegram bot and send /start or any message!")
        print("Press CTRL+C to stop.\n")
        telegram_chat_engine.is_running = True
        try:
            telegram_chat_engine._polling_loop()
        except KeyboardInterrupt:
            print("\nTelegram bot stopped.")

    elif args.mode == "news":
        display_news_calendar()

    elif args.mode == "predict":
        run_predictive_outlook()

    elif args.mode == "scan":
        run_scheduled_scan()

    elif args.mode == "test-telegram":
        print(f"\n[TEST] Sending test Telegram alert to Ahmed...")
        res = notifier.send_test_telegram()
        if res.get("success"):
            print(f"[TEST] SUCCESS: Telegram test message sent successfully to your phone!")
        else:
            print(f"[TEST] FAILED: {res.get('error', 'Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env')}")

    elif args.mode == "test-discord":
        print(f"\n[TEST] Sending test Discord alert to Ahmed...")
        res = notifier.send_test_discord()
        if res.get("success"):
            print(f"[TEST] SUCCESS: Discord test message sent successfully!")
        else:
            print(f"[TEST] FAILED: {res.get('error', 'Check DISCORD_WEBHOOK_URL in .env')}")

    elif args.mode == "test-email":
        print("\n[TEST] Sending test email notification...")
        res = notifier.send_test_email()
        if res.get("success"):
            print(f"[TEST] SUCCESS: Test email successfully sent to {res.get('recipient')}!")
        else:
            print(f"[TEST] FAILED: {res.get('error', 'Check your SMTP credentials in .env')}")

    elif args.mode == "test-webhook":
        test_tradingview_simulation()

    elif args.mode == "test-news-alert":
        test_pre_news_alert_simulation()

    elif args.mode == "server":
        # 1. Start Telegram 2-way chat engine in background thread
        if settings.TELEGRAM_ENABLED and settings.TELEGRAM_BOT_TOKEN:
            telegram_chat_engine.start_polling_in_background()

        # 2. Start background scheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(news_engine.refresh_calendar, "interval", minutes=30)
        scheduler.add_job(run_scheduled_scan, "interval", minutes=15)
        scheduler.add_job(run_predictive_outlook, "interval", hours=12)
        # Check every 2 minutes for upcoming news in the 30-minute window
        scheduler.add_job(news_engine.check_and_trigger_30min_alerts, "interval", minutes=2)
        scheduler.start()

        # Run initial outlook in background thread so server starts instantly
        import threading
        threading.Thread(target=run_predictive_outlook, daemon=True).start()

        print(f" Starting TradingView Webhook Bridge on http://{settings.WEBHOOK_HOST}:{settings.WEBHOOK_PORT}")
        print(f" Interactive Web Chat available at: http://localhost:{settings.WEBHOOK_PORT}/chat")
        if settings.TELEGRAM_BOT_TOKEN:
            print(f" Telegram 2-Way Chat Bot: ACTIVE (Send /start in Telegram)")
        print(" Press CTRL+C to terminate.")

        try:
            uvicorn.run(app, host=settings.WEBHOOK_HOST, port=settings.WEBHOOK_PORT, log_level="info")
        except (KeyboardInterrupt, SystemExit):
            telegram_chat_engine.stop()
            scheduler.shutdown()
            print("\nShutting down bot gracefully.")


if __name__ == "__main__":
    main()
