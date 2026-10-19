"""
Configuration and Environment Settings for the FOREX & XAU/USD Trading Bot.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env file from the project root
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Settings(BaseModel):
    # Account & Risk Parameters
    ACCOUNT_BALANCE: float = Field(default=float(os.getenv("ACCOUNT_BALANCE", "10000.0")), description="Trading account balance in USD")
    RISK_PERCENT: float = Field(default=float(os.getenv("RISK_PERCENT", "1.0")), description="Risk per trade in percentage (e.g. 1.0 for 1%)")
    MAX_DAILY_RISK_PERCENT: float = Field(default=float(os.getenv("MAX_DAILY_RISK_PERCENT", "3.0")), description="Maximum drawdown tolerated per day before cooling off")
    DEFAULT_RISK_REWARD: float = Field(default=float(os.getenv("DEFAULT_RISK_REWARD", "2.0")), description="Minimum Risk to Reward Ratio")
    
    # Target Pairs
    PRIMARY_SYMBOL: str = Field(default=os.getenv("PRIMARY_SYMBOL", "XAUUSD"), description="Primary asset: Gold (XAUUSD)")
    SECONDARY_SYMBOLS: list = Field(default=["EURUSD", "GBPUSD", "USDJPY"], description="Secondary Forex pairs")
    
    # Quality & Confluence Filter
    MIN_CONFLUENCE_SCORE: int = Field(default=int(os.getenv("MIN_CONFLUENCE_SCORE", "85")), description="Minimum confluence score (0-100) to trigger a signal. Enforces high quality.")
    
    # ForexFactory & Economic News Filter
    NEWS_FILTER_ENABLED: bool = Field(default=os.getenv("NEWS_FILTER_ENABLED", "True").lower() == "true", description="Enable economic calendar news filtering")
    NEWS_PRE_EVENT_FREEZE_MINS: int = Field(default=int(os.getenv("NEWS_PRE_EVENT_FREEZE_MINS", "30")), description="Minutes BEFORE high-impact news to freeze new entries")
    NEWS_POST_EVENT_WAIT_MINS: int = Field(default=int(os.getenv("NEWS_POST_EVENT_WAIT_MINS", "10")), description="Minutes to wait AFTER news release to let spreads stabilize")
    NEWS_CATALYST_WINDOW_MINS: int = Field(default=int(os.getenv("NEWS_CATALYST_WINDOW_MINS", "120")), description="Window to trade post-news momentum with confirmed fundamental bias")
    
    # Email Notifications (SMTP)
    EMAIL_ENABLED: bool = Field(default=os.getenv("EMAIL_ENABLED", "False").lower() == "true", description="Enable Email trade notifications")
    SMTP_SERVER: str = Field(default=os.getenv("SMTP_SERVER", "smtp.gmail.com"), description="SMTP Server (e.g. smtp.gmail.com)")
    SMTP_PORT: int = Field(default=int(os.getenv("SMTP_PORT", "587")), description="SMTP Port (usually 587 for TLS)")
    SMTP_USERNAME: str = Field(default=os.getenv("SMTP_USERNAME", ""), description="Sender email address")
    SMTP_PASSWORD: str = Field(default=os.getenv("SMTP_PASSWORD", ""), description="Sender email app password")
    NOTIFICATION_RECEIVER_EMAIL: str = Field(default=os.getenv("NOTIFICATION_RECEIVER_EMAIL", ""), description="Recipient email address")
    
    # Telegram Alerts
    TELEGRAM_ENABLED: bool = Field(default=os.getenv("TELEGRAM_ENABLED", "True").lower() == "true", description="Enable Telegram instant alerts")
    TELEGRAM_BOT_TOKEN: str = Field(default=os.getenv("TELEGRAM_BOT_TOKEN", ""), description="Telegram bot API token from @BotFather")
    TELEGRAM_CHAT_ID: str = Field(default=os.getenv("TELEGRAM_CHAT_ID", ""), description="Telegram chat ID")
    TELEGRAM_PROXY: str = Field(default=os.getenv("TELEGRAM_PROXY", ""), description="Optional HTTP or SOCKS proxy URL for Telegram (e.g. http://127.0.0.1:10809)")
    
    # Discord Instant Alerts
    DISCORD_ENABLED: bool = Field(default=os.getenv("DISCORD_ENABLED", "True").lower() == "true", description="Enable Discord webhook alerts")
    DISCORD_WEBHOOK_URL: str = Field(default=os.getenv("DISCORD_WEBHOOK_URL", ""), description="Discord channel webhook URL")
    
    # User Personalization
    USER_NAME: str = Field(default=os.getenv("USER_NAME", "Ahmed"), description="User's first name for personalized direct emails")
    DAILY_OUTLOOK_EMAIL_ENABLED: bool = Field(default=os.getenv("DAILY_OUTLOOK_EMAIL_ENABLED", "True").lower() == "true", description="Enable daily predictive market outlook emails")
    
    # Webhook Server for TradingView
    WEBHOOK_HOST: str = Field(default=os.getenv("WEBHOOK_HOST", "0.0.0.0"), description="Webhook server host")
    WEBHOOK_PORT: int = Field(default=int(os.getenv("PORT", os.getenv("WEBHOOK_PORT", "8000"))), description="Webhook server port")
    WEBHOOK_SECRET_TOKEN: str = Field(default=os.getenv("WEBHOOK_SECRET_TOKEN", "GOLD_SNIPER_SECRET_KEY_9988"), description="Secret token to authenticate TradingView webhooks")


# Global instance
settings = Settings()
