"""
FastAPI Webhook Server for TradingView Integration.
Receives real-time alerts from TradingView Pine Script indicators/strategies,
cross-checks against ForexFactory economic news filter, calculates exact
risk & lot sizes, and broadcasts signals via Email & Console.
"""

from typing import Optional
from fastapi import FastAPI, HTTPException, Header, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from core.config import settings
from core.news_engine import news_engine
from core.technical_engine import technical_engine
from core.predictive_engine import predictive_engine
from core.chat_engine import chat_engine
from core.notifier import notifier
from core.terminal_html import get_terminal_html

app = FastAPI(
    title="XAU/USD & FOREX Institutional Trading Bot API",
    description="High-confluence trading signal engine with ForexFactory news filtering and TradingView webhook bridge.",
    version="1.0.0"
)


class TradingViewWebhookPayload(BaseModel):
    secret: Optional[str] = Field(default="", description="Secret authentication token")
    symbol: str = Field(default="XAUUSD", description="Ticker symbol (e.g. XAUUSD, EURUSD)")
    action: str = Field(default="BUY", description="Trade direction: BUY or SELL")
    price: float = Field(..., description="Trigger price on TradingView")
    stop_loss: Optional[float] = Field(default=None, description="Optional stop loss from TradingView indicator")
    tp1: Optional[float] = Field(default=None, description="Optional TP1 price")
    tp2: Optional[float] = Field(default=None, description="Optional TP2 price")
    timeframe: Optional[str] = Field(default="15m", description="Chart timeframe")
    strategy: Optional[str] = Field(default="TradingView_Confluence", description="Name of strategy trigger")


@app.get("/", response_class=HTMLResponse)
@app.get("/chart", response_class=HTMLResponse)
@app.get("/terminal", response_class=HTMLResponse)
def get_institutional_terminal():
    """Serves the live interactive Gold trading terminal and autonomous SMC bot dashboard."""
    return get_terminal_html(
        user_name=settings.USER_NAME,
        account_balance=settings.ACCOUNT_BALANCE,
        risk_percent=settings.RISK_PERCENT,
        min_confluence=settings.MIN_CONFLUENCE_SCORE
    )


@app.get("/api/info")
def get_service_info():
    return {
        "status": "online",
        "service": "Gold & Forex Institutional Trading Bot",
        "primary_symbol": settings.PRIMARY_SYMBOL,
        "confluence_threshold": f"{settings.MIN_CONFLUENCE_SCORE}%",
        "news_filter_active": settings.NEWS_FILTER_ENABLED
    }


@app.get("/api/status")
def get_system_status():
    """Returns the current market threat status, news bias, and configuration."""
    news_eval = news_engine.evaluate_gold_threat_and_bias()
    return {
        "status": "active",
        "gold_threat_level": news_eval["status"],
        "news_safe_to_trade": news_eval["is_safe"],
        "fundamental_bias": news_eval["fundamental_bias"],
        "macro_reason": news_eval["reason"],
        "account_balance": settings.ACCOUNT_BALANCE,
        "risk_percent": settings.RISK_PERCENT,
        "email_notifications": settings.EMAIL_ENABLED
    }


@app.get("/api/news")
def get_upcoming_news(hours: int = 72, currency: str = "USD"):
    """Fetches high-impact economic calendar events from ForexFactory with Gold threat status."""
    events = news_engine.get_upcoming_events(hours_ahead=hours, high_impact_only=True, currency=currency)
    threat = news_engine.evaluate_gold_threat_and_bias()
    return {
        "threat": threat,
        "hours_ahead": hours,
        "currency": currency,
        "count": len(events),
        "events": [e.to_dict() for e in events]
    }


@app.post("/api/webhook/tradingview")
def receive_tradingview_alert(payload: TradingViewWebhookPayload):
    """
    Receives alerts from TradingView.
    Enforces secret token verification, checks ForexFactory news lockout,
    computes position sizing & lot size, and dispatches email.
    """
    # 1. Security check
    if settings.WEBHOOK_SECRET_TOKEN and payload.secret != settings.WEBHOOK_SECRET_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret token."
        )

    # 2. Validate alert with Technical & News Engine
    alert_result = technical_engine.validate_tradingview_alert(
        symbol=payload.symbol,
        action=payload.action,
        price=payload.price,
        strategy_name=payload.strategy or "TradingView_Confluence",
        provided_sl=payload.stop_loss,
        provided_tp1=payload.tp1,
        provided_tp2=payload.tp2
    )

    # 3. If trade is rejected due to news lockout or conflicting macro bias
    if not alert_result.get("approved"):
        return {
            "status": "rejected",
            "message": alert_result.get("reason"),
            "news_eval": alert_result.get("news_eval")
        }

    # 4. Dispatch alert via Email and Console
    notifier.send_trade_signal(alert_result)

    return {
        "status": "success",
        "action": payload.action,
        "symbol": payload.symbol,
        "grade": alert_result.get("grade"),
        "confluence_score": alert_result.get("confluence_score"),
        "trade_plan": alert_result.get("trade_plan")
    }


@app.api_route("/api/scan", methods=["GET", "POST"])
def trigger_manual_scan(symbol: str = "XAUUSD"):
    """Triggers an on-demand institutional confluence scan for Gold or Forex."""
    result = technical_engine.evaluate_live_chart(symbol)
    if result.get("signal") in ["BUY", "SELL"]:
        notifier.send_trade_signal(result)
    return result


@app.post("/api/test-email")
def trigger_test_email():
    """Dispatches a test notification email."""
    return notifier.send_test_email()


@app.get("/api/prediction")
def get_market_prediction(symbol: str = "XAUUSD"):
    """Returns predictive market intelligence, crash warnings, and scenario targets."""
    return predictive_engine.generate_market_outlook(symbol)


@app.post("/api/send-prediction-email")
def trigger_prediction_email(symbol: str = "XAUUSD"):
    """Generates outlook and emails prediction briefing to the user."""
    outlook = predictive_engine.generate_market_outlook(symbol)
    success = notifier.send_predictive_outlook_email(outlook)
    return {
        "success": success,
        "recipient": settings.NOTIFICATION_RECEIVER_EMAIL,
        "outlook": outlook
    }


class ChatMessagePayload(BaseModel):
    message: str = Field(..., description="Message from Ahmed to the trading bot")


@app.post("/api/chat")
def handle_chat_message(payload: ChatMessagePayload):
    """Processes chat message from Ahmed and returns institutional response."""
    reply = chat_engine.respond(payload.message)
    return {
        "user": settings.USER_NAME,
        "message": payload.message,
        "response": reply
    }


@app.get("/chat", response_class=HTMLResponse)
def get_chat_interface():
    """Serves an interactive dark-themed Web Chat UI for Ahmed."""
    user = settings.USER_NAME or "Ahmed"
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>TradeDesk AI Chat - {user}</title>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; display: flex; flex-direction: column; height: 100vh; }}
        /* High-contrast scrollbar */
        ::-webkit-scrollbar {{ width: 10px; }}
        ::-webkit-scrollbar-track {{ background: #0f172a; }}
        ::-webkit-scrollbar-thumb {{ background: #475569; border-radius: 5px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #f59e0b; }}
        .header {{ background: #1e293b; padding: 16px 20px; border-bottom: 1px solid #334155; display: flex; align-items: center; justify-content: space-between; }}
        .header h1 {{ font-size: 18px; margin: 0; color: #f59e0b; display: flex; align-items: center; gap: 8px; }}
        .badge {{ background: #10b981; color: #ffffff; padding: 3px 8px; border-radius: 12px; font-size: 11px; }}
        .chat-container {{ flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; max-width: 800px; width: 100%; margin: 0 auto; box-sizing: border-box; }}
        .msg {{ max-width: 80%; padding: 12px 16px; border-radius: 10px; line-height: 1.5; font-size: 14px; white-space: pre-wrap; }}
        .msg-bot {{ background: #1e293b; border: 1px solid #334155; align-self: flex-start; color: #f1f5f9; }}
        .msg-user {{ background: #2563eb; color: #ffffff; align-self: flex-end; }}
        .input-bar {{ background: #1e293b; padding: 14px 20px; border-top: 1px solid #334155; display: flex; gap: 10px; max-width: 800px; width: 100%; margin: 0 auto; box-sizing: border-box; }}
        input {{ flex: 1; background: #0f172a; border: 1px solid #334155; color: #f8fafc; padding: 12px 16px; border-radius: 8px; font-size: 14px; outline: none; }}
        input:focus {{ border-color: #f59e0b; }}
        button {{ background: #f59e0b; color: #0f172a; border: none; padding: 12px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; transition: 0.2s; }}
        button:hover {{ background: #d97706; }}
      </style>
    </head>
    <body>
      <div class="header">
        <h1>TradeDesk AI • Assistant for {user}</h1>
        <span class="badge">Online (Gold & Forex)</span>
      </div>
      <div class="chat-container" id="chat">
        <div class="msg msg-bot">Hey {user}! I am your Gold & Forex trade partner. Ask me to review a trade idea, check CPI/NFP news, calculate lot size, or forecast Gold's next move.</div>
      </div>
      <div class="input-bar">
        <input type="text" id="userInput" placeholder="Ask about a trade, CPI news, lot size, or Gold prediction..." onkeydown="if(event.key==='Enter') send()">
        <button onclick="send()">Send</button>
      </div>
      <script>
        async function send() {{
          const input = document.getElementById('userInput');
          const text = input.value.trim();
          if (!text) return;
          const chat = document.getElementById('chat');
          
          const uDiv = document.createElement('div');
          uDiv.className = 'msg msg-user';
          uDiv.textContent = text;
          chat.appendChild(uDiv);
          input.value = '';
          chat.scrollTop = chat.scrollHeight;

          const res = await fetch('/api/chat', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ message: text }})
          }});
          const data = await res.json();
          
          const bDiv = document.createElement('div');
          bDiv.className = 'msg msg-bot';
          bDiv.textContent = data.response;
          chat.appendChild(bDiv);
          chat.scrollTop = chat.scrollHeight;
        }}
      </script>
    </body>
    </html>
    """
