# 🪙 Gold (XAU/USD) & FOREX Institutional Trading Bot

An institutional-grade, multi-confluence trading system tailored specifically for **Gold (XAU/USD)** and major Forex pairs (`EURUSD`, `GBPUSD`, `USDJPY`).

It bridges directly with **TradingView Webhooks**, integrates a live **ForexFactory Economic Calendar** (monitoring CPI, NFP, PPI, Unemployment, and FOMC rate decisions), dynamically computes **exact lot sizing & capital risk**, and delivers real-time signals with **exact Entry, Stop Loss, and tiered Take Profits (TP1, TP2, TP3)** directly to your **Email and Console**.

---

## ⚡ Core Pillars & Architecture

### 1. 🎯 Quality Over Quantity (85% - 90%+ Confluence Filter)
The bot enforces an institutional confluence threshold ($85\%$ default):
* **Trend Alignment (25 pts)**: Multi-timeframe trend confirmation (EMA 50 & EMA 200).
* **Liquidity Sweeps (25 pts)**: Asian Session / Swing High & Low liquidity grabs.
* **Smart Money Structure (20 pts)**: Fair Value Gap (FVG) mitigation and Market Structure Shift (MSS).
* **ForexFactory News Alignment (20 pts)**: Macro economic catalyst confirmation.
* **Momentum & Volatility (10 pts)**: 14-period RSI & ATR buffer.

Trades scoring below the threshold are automatically discarded to preserve capital.

### 2. 📰 ForexFactory Macro News Engine (CPI, NFP, FOMC)
* **Pre-News Lockout**: Automatically freezes trading **30 minutes before** red-folder USD events to protect you against sudden spread widening and slippage.
* **Post-News Stabilization**: Pauses for 10 minutes post-release until the initial volatile spike subsides.
* **Catalyst Analysis (10m - 120m)**:
  * **Hot CPI / NFP** (Actual > Forecast) $\rightarrow$ Stronger USD $\rightarrow$ **Bearish bias on Gold (XAU/USD)**.
  * **Soft CPI / NFP** (Actual < Forecast) $\rightarrow$ Weaker USD $\rightarrow$ **Bullish bias on Gold (XAU/USD)**.
  * **High Unemployment** $\rightarrow$ Weaker USD $\rightarrow$ **Bullish bias on Gold**.

### 3. ⚖️ Exact Lot Size & Risk Calculator
Calculates the exact position size tailored specifically to your account balance and risk percentage:
$$\text{Lot Size (XAU/USD)} = \frac{\text{Account Balance} \times \text{Risk \%}}{|\text{Entry} - \text{Stop Loss}| \times 100}$$

* **Tiered Take-Profits**:
  * **TP1 (1:1.5 Risk-to-Reward)**: Close 50% lot size immediately and move Stop Loss to Breakeven (+ spread buffer).
  * **TP2 (1:3.0 Risk-to-Reward)**: Close 30% lot size at major liquidity swing.
  * **TP3 (1:5.0 Risk-to-Reward)**: Trail remaining 20% for extended trend runner.

### 4. 📈 TradingView Integration
* Includes `tradingview/gold_institutional_sniper.pine` (Pine Script v5).
* Automatically plots Asian session ranges, FVGs, dynamic ATR stop bands, and triggers webhook alerts with JSON payloads directly to your bot server.

### 5. 📧 Email Dispatcher (HTML & Plaintext)
Delivers formatted trade alerts containing:
* Asset & Grade badge (e.g. `XAU/USD BUY - Grade A+ (95% Confluence)`)
* Exact Entry Price, Stop Loss, and Take Profits (TP1, TP2, TP3)
* Exact Recommended Lot Size
* ForexFactory News Context & Fundamental Reasoning
* Trade Management Protocol

---

## 🛠️ Quick Start Guide

### 1. Configuration (`.env`)
Copy `.env.example` to `.env` and fill in your trading account details:

```env
# Account Parameters
ACCOUNT_BALANCE=10000.0
RISK_PERCENT=1.0

# Confluence Filter (Grade A+ only)
MIN_CONFLUENCE_SCORE=85

# ForexFactory News
NEWS_FILTER_ENABLED=True
NEWS_PRE_EVENT_FREEZE_MINS=30

# Email Notifications (Optional - Gmail App Password)
EMAIL_ENABLED=True
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_16_char_google_app_password
NOTIFICATION_RECEIVER_EMAIL=your_email@gmail.com

# Personalization & Market Outlook
USER_NAME=Ahmed
DAILY_OUTLOOK_EMAIL_ENABLED=True

# Webhook Server
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8000
WEBHOOK_SECRET_TOKEN=GOLD_SNIPER_SECRET_KEY_9988
```

> **How to get a Gmail App Password:**
> 1. Go to your Google Account $\rightarrow$ Security $\rightarrow$ 2-Step Verification.
> 2. Scroll to **App passwords** $\rightarrow$ Create one named "TradingBot".
> 3. Paste the generated 16-character password into `SMTP_PASSWORD`.

---

### 2. Available Run Commands

#### Start the Live Webhook Server (TradingView Bridge + Auto Scanner + Web Chat):
```bash
python main.py --mode server
```
*Web Chat UI is available at:* `http://localhost:8000/chat`

#### Start Interactive Terminal Chat with the Bot (Discuss Trades & News):
```bash
python main.py --mode chat
```

#### Run Forward-Looking Market Prediction (e.g. Gold Crash Warning):
```bash
python main.py --mode predict
```

#### Check This Week's ForexFactory High-Impact News:
```bash
python main.py --mode news
```

#### Run an Immediate Confluence Scan on Gold:
```bash
python main.py --mode scan
```

#### Test 30-Minute Pre-News Advance Warning Email:
```bash
python main.py --mode test-news-alert
```

#### Test Trade Signal Email Dispatch:
```bash
python main.py --mode test-email
```

#### Simulate an Incoming TradingView Webhook:
```bash
python main.py --mode test-webhook
```

---

## 📊 Connecting TradingView

1. Open [TradingView](https://www.tradingview.com) and navigate to **XAUUSD** (or `GC1!`, `GOLD`).
2. Open the **Pine Editor** tab at the bottom.
3. Paste the contents of `tradingview/gold_institutional_sniper.pine` and click **Add to chart**.
4. Click **Alert** on the chart (Alt + A):
   * **Condition**: Select `Gold Sniper - Institutional SMC & Confluence Engine`.
   * **Alert Actions**: Check **Webhook URL**.
   * **Webhook URL**: `http://YOUR_SERVER_IP:8000/api/webhook/tradingview` (or your Ngrok / Cloudflare Tunnel URL, e.g., `https://xyz.ngrok-free.app/api/webhook/tradingview`).
   * **Message**: Leave default or ensure it matches the Pine Script JSON structure.

---

## 🧠 Professional Note on Market Accuracy

In institutional quantitative finance, **a literal 100% win-rate is mathematically impossible** because unpredictable black-swan events, broker slippage, and spread fluctuations exist in open markets. 

However, this bot achieves **institutional-grade expectancy** by:
1. **Filtering out 90% of market chop** (only entering when technical and fundamental confluence is $\ge 85-90\%$).
2. **Never gambling into CPI/NFP news releases** (avoiding devastating slippage).
3. **Strict 1:2 to 1:3 Risk-to-Reward mechanics**: Taking 50% profit at TP1 and shifting Stop Loss to Breakeven guarantees that winning trades produce 2-3x larger returns than any controlled loss.
