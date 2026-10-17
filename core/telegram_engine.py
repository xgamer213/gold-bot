"""
Telegram Interactive Chat Engine & 2-Way Bot Bridge.
Enables Ahmed to converse directly with his bot inside Telegram on mobile or desktop,
receive automated high-accuracy Gold signals, and get 30-minute pre-news warnings.
"""

import time
import logging
import threading
import requests
from typing import Dict, Any, Optional

from core.config import settings
from core.chat_engine import ChatEngine
from core.predictive_engine import predictive_engine
from core.news_engine import news_engine

logger = logging.getLogger("TelegramBot")


class TelegramChatEngine:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = str(settings.TELEGRAM_CHAT_ID)
        self.user_name = settings.USER_NAME or "Ahmed"
        self.chat_engine = ChatEngine()
        self.last_update_id = 0
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

    @property
    def proxies(self) -> Optional[Dict[str, str]]:
        proxy = getattr(settings, "TELEGRAM_PROXY", "") or ""
        if proxy:
            return {"http": proxy, "https": proxy}
        return None

    def start_polling_in_background(self):
        """Starts the Telegram polling loop in a daemon thread."""
        if not self.token:
            logger.warning("Telegram Bot Token is missing. Telegram 2-way chat will not start.")
            return

        self.is_running = True
        self._thread = threading.Thread(target=self._polling_loop, daemon=True, name="TelegramPollingThread")
        self._thread.start()
        logger.info(f"Telegram 2-way Chat Listener started for {self.user_name} (Chat ID: {self.chat_id})")

    def stop(self):
        """Stops the polling loop."""
        self.is_running = False

    def send_message(self, text: str, target_chat_id: Optional[str] = None) -> bool:
        """Sends a message to the target chat ID (defaults to Ahmed's configured chat ID)."""
        if not self.token:
            return False
        cid = target_chat_id or self.chat_id
        if not cid:
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": cid,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            res = requests.post(url, json=payload, timeout=12, proxies=self.proxies)
            if res.status_code == 200:
                return True
            # Retry without markdown if parsing failed
            payload.pop("parse_mode", None)
            res2 = requests.post(url, json=payload, timeout=12, proxies=self.proxies)
            return res2.status_code == 200
        except Exception as e:
            logger.debug(f"Failed to send Telegram message: {e}")
            return False

    def _polling_loop(self):
        """Continuously polls Telegram for incoming messages from Ahmed."""
        url = f"https://api.telegram.org/bot{self.token}/getUpdates"

        while self.is_running:
            params = {
                "offset": self.last_update_id + 1,
                "timeout": 15
            }
            try:
                res = requests.get(url, params=params, timeout=20, proxies=self.proxies)
                if res.status_code == 200:
                    data = res.json()
                    for update in data.get("result", []):
                        self.last_update_id = update["update_id"]
                        self._process_update(update)
                elif res.status_code == 409:
                    logger.warning("Telegram webhook conflict. Retrying...")
                    time.sleep(5)
                else:
                    logger.warning(f"Telegram polling HTTP {res.status_code}: {res.text}")
                    time.sleep(5)
            except requests.exceptions.RequestException as e:
                # Often connection timeout if VPN is turned off
                logger.debug(f"Telegram polling network pause: {e}")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error in Telegram polling: {e}")
                time.sleep(5)

    def _process_update(self, update: Dict[str, Any]):
        """Parses and responds to an individual Telegram message."""
        message = update.get("message") or update.get("edited_message")
        if not message:
            return

        chat = message.get("chat", {})
        sender_chat_id = str(chat.get("id", ""))
        text = message.get("text", "").strip()

        if not text:
            return

        # Security check: if chat_id is specified in .env, verify it matches Ahmed's ID
        if self.chat_id and sender_chat_id != self.chat_id:
            logger.info(f"Ignoring unauthorized Telegram message from chat ID {sender_chat_id}")
            self.send_message(
                f"Unauthorized access. This is a private institutional trading bot for {self.user_name}.",
                target_chat_id=sender_chat_id
            )
            return

        logger.info(f"Received Telegram message from {self.user_name}: {text}")

        # Dispatch command or natural language message
        response = self._handle_input(text)
        self.send_message(response, target_chat_id=sender_chat_id)

    def _handle_input(self, text: str) -> str:
        """Determines the reply based on command or conversation."""
        cmd = text.lower().strip()

        # Commands
        if cmd in ["/start", "/help", "help"]:
            return (
                f"👋 **Hey {self.user_name}! Welcome to your Institutional Trading Bot!**\n\n"
                f"I track Gold (XAU/USD) & Forex 24/7 with SMC Fair Value Gaps, Liquidity Sweeps, and ForexFactory News.\n\n"
                f"📌 **Quick Commands:**\n"
                f"• `/signal` - Run a live scan on Gold and get an immediate Grade A+ trade blueprint\n"
                f"• `/predict` - Get the latest forward-looking Gold crash/rally forecast\n"
                f"• `/news` - Check upcoming high-impact economic releases (CPI, NFP, FOMC)\n"
                f"• `/status` - Bot health & active account settings\n\n"
                f"💬 **You can also chat with me naturally!** For example:\n"
                f"• *'Give me a signal on Gold right now'*\n"
                f"• *'What is Gold doing right now?'*\n"
                f"• *'Calculate lot size for $10k balance with $6 SL on Gold'*\n"
                f"• *'What is a Fair Value Gap (FVG)?'*\n"
                f"• *'Will Gold crash this week?'*\n\n"
                f"Whenever a Grade A+ setup occurs or news is 30 mins away, I'll buzz you right here! 🚀"
            )

        if cmd in ["/signal", "signal", "/trade", "trade"]:
            return self.chat_engine._handle_signal_request()

        if cmd == "/predict":
            outlook = predictive_engine.generate_market_outlook("XAUUSD")
            return (
                f"🔮 **MARKET PREDICTION FOR {self.user_name.upper()}**\n\n"
                f"**Headline:** {outlook.get('headline')}\n"
                f"**Directional Bias:** {outlook.get('directional_bias')}\n"
                f"**Crash Probability:** {outlook.get('crash_risk_probability')}\n"
                f"**Rally Probability:** {outlook.get('rally_probability')}\n"
                f"**Key Support / Invalidation:** ${outlook.get('invalidation_level')}\n"
                f"**Macro Catalyst:** {outlook.get('macro_catalyst')}\n\n"
                f"💡 *Actionable Advice:* {outlook.get('actionable_summary')}"
            )

        if cmd == "/news":
            return self.chat_engine._handle_news_query("news")

        if cmd == "/status":
            return (
                f"⚙️ **BOT STATUS FOR {self.user_name.upper()}**\n\n"
                f"• Primary Asset: {settings.PRIMARY_SYMBOL}\n"
                f"• Balance: ${settings.ACCOUNT_BALANCE:,.2f} USD\n"
                f"• Risk per trade: {settings.RISK_PERCENT}%\n"
                f"• Min Confluence Filter: {settings.MIN_CONFLUENCE_SCORE}% (Grade A+ only)\n"
                f"• ForexFactory News Radar: ACTIVE (30m pre-event alerts)\n"
                f"• Status: 🟢 All systems operational!"
            )

        # Natural language processing via ChatEngine
        return self.chat_engine.respond(text)


# Singleton instance
telegram_chat_engine = TelegramChatEngine()
