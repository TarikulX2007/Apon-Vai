#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2-in-1 Proxy Balance Checker Bot (OWL Proxy & IP Cook)"""

import os
import sys
import time
import html
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from datetime import datetime
from typing import Tuple

try:
    import telebot
    from telebot import types
except ImportError:
    os.system(f"{sys.executable} -m pip install pyTelegramBotAPI requests")
    import telebot
    from telebot import types

# Robust HTTP session with connection pooling and transient auto-retry
_session = requests.Session()
_retries = Retry(
    total=2,
    backoff_factor=0.5,
    status_forcelist=[502, 503, 504],
    raise_on_status=False
)
_adapter = HTTPAdapter(max_retries=_retries, pool_connections=20, pool_maxsize=50)
_session.mount("http://", _adapter)
_session.mount("https://", _adapter)

# UTF-8 console setup
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Config
BOT_TOKEN = "8807512141:AAFep2LBQJzQ-4MnySBlIAXRYp-Rd3axssU"
API_BASE_URL = os.getenv("PROXY_CHECKER_API_BASE", "http://204.12.218.86:31957")
MB_CHECKER_WEBSITE = "http://204.12.218.86:31957/"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
user_last_query = {}

# Custom Premium Emojis
PE = {
    "search": '<tg-emoji emoji-id="5463352748751753567">🔍</tg-emoji>',
    "dot": '<tg-emoji emoji-id="5352638632278660622">🔹</tg-emoji>',
    "user": '<tg-emoji emoji-id="5352861489541714456">👤</tg-emoji>',
    "package": '<tg-emoji emoji-id="5821344131208714546">📦</tg-emoji>',
    "chart": '<tg-emoji emoji-id="5353032893096567467">📊</tg-emoji>',
    "storage": '<tg-emoji emoji-id="5352721946054268944">📁</tg-emoji>',
    "pin": '<tg-emoji emoji-id="5352922460897452503">📍</tg-emoji>',
    "active": '<tg-emoji emoji-id="5192812028632274956">🟢</tg-emoji>',
    "depleted": '<tg-emoji emoji-id="5377620300965888937">🔴</tg-emoji>',
    "calendar": '<tg-emoji emoji-id="5352585194295564660">📅</tg-emoji>',
    "globe": '<tg-emoji emoji-id="5336972142066047577">🌐</tg-emoji>',
    "ok": '<tg-emoji emoji-id="5352694861990501856">✅</tg-emoji>',
    "no": '<tg-emoji emoji-id="5420130255174145507">❌</tg-emoji>',
    "warn": '<tg-emoji emoji-id="5336944168944047463">⚠️</tg-emoji>',
    "bolt": '<tg-emoji emoji-id="5213101149195882720">⚡</tg-emoji>',
    "hourglass": '<tg-emoji emoji-id="5175181110572745347">⏳</tg-emoji>',
    "refresh": '<tg-emoji emoji-id="6012661228910939253">🔄</tg-emoji>',
    "key": '<tg-emoji emoji-id="5197288647275071607">🔑</tg-emoji>',
    "link": '<tg-emoji emoji-id="5420517437885943844">🔗</tg-emoji>',
    "rocket": '<tg-emoji emoji-id="5352597830089347330">🚀</tg-emoji>',
}

_RENDER_MAP = {
    "🔍": ("5463352748751753567", "🔍"),
    "🔎": ("5463352748751753567", "🔎"),
    "🔹": ("5352638632278660622", "🔹"),
    "👤": ("5352861489541714456", "👤"),
    "📦": ("5821344131208714546", "📦"),
    "📊": ("5353032893096567467", "📊"),
    "📉": ("5353032893096567467", "📉"),
    "📈": ("5352877703043258544", "📈"),
    "📁": ("5352721946054268944", "📁"),
    "💾": ("5352721946054268944", "💾"),
    "📍": ("5352922460897452503", "📍"),
    "📌": ("5318986077455795572", "📌"),
    "🧭": ("5352922460897452503", "🧭"),
    "🟢": ("5192812028632274956", "🟢"),
    "🔴": ("5377620300965888937", "🔴"),
    "📅": ("5352585194295564660", "📅"),
    "📆": ("5352585194295564660", "📆"),
    "🌐": ("5336972142066047577", "🌐"),
    "✅": ("5352694861990501856", "✅"),
    "❌": ("5420130255174145507", "❌"),
    "⚠️": ("5336944168944047463", "⚠️"),
    "⚡": ("5213101149195882720", "⚡"),
    "⚡️": ("5213101149195882720", "⚡️"),
    "⏳": ("5175181110572745347", "⏳"),
    "⌛": ("5337172996211648018", "⌛"),
    "🔄": ("6012661228910939253", "🔄"),
    "🔑": ("5197288647275071607", "🔑"),
    "🔗": ("5420517437885943844", "🔗"),
    "🚀": ("5352597830089347330", "🚀"),
    "•": ("5352638632278660622", "•"),
}

# ---------------- Colored (styled) inline buttons ----------------
import threading
_style_state = threading.local()

_BTN_STYLES = {
    # callback_data: (style, premium icon emoji id)
    "chk_refresh": ("success", "6012661228910939253"),  # green + refresh
    "chk_another": ("primary", "5463352748751753567"),  # blue + search
    "chk_close":   ("danger",  "5420130255174145507"),  # red + cross
}

class _StyledInlineButton(types.InlineKeyboardButton):
    """Inline button with color + premium icon. Falls back to plain if styles are switched off."""
    _extra = None
    def to_dict(self):
        d = super().to_dict()
        if getattr(_style_state, "off", False) or not self._extra:
            return d
        d["style"], d["icon_custom_emoji_id"] = self._extra
        return d

def IB(text: str, callback_data: str) -> types.InlineKeyboardButton:
    btn = _StyledInlineButton(text, callback_data=callback_data)
    btn._extra = _BTN_STYLES.get(callback_data)
    return btn

def _safe_wrap(fn):
    """If Telegram rejects the colored buttons, retry once with plain buttons so the checker never breaks."""
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if "not modified" in str(e).lower() or not kwargs.get("reply_markup") and len(args) < 5:
                raise
            _style_state.off = True
            try:
                return fn(*args, **kwargs)
            finally:
                _style_state.off = False
    return wrapper

bot.send_message = _safe_wrap(bot.send_message)
bot.edit_message_text = _safe_wrap(bot.edit_message_text)

def R(text: str) -> str:
    """Replaces raw unicode emojis with custom premium emoji tags."""
    for em, (eid, fb) in _RENDER_MAP.items():
        text = text.replace(em, f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>')
    return text

def clean_proxy_input(raw: str) -> str:
    """Strips email prefix if 6-part string is provided."""
    q = raw.strip()
    parts = q.split(":")
    if len(parts) >= 6 and "@" in parts[0]:
        return f"{parts[2]}:{parts[3]}:{parts[4]}:{parts[5]}"
    return q

def format_proxy_check_view(query: str) -> Tuple[str, bool, types.InlineKeyboardMarkup]:
    """Queries Gateway API and formats HTML report with progress bar."""
    query = clean_proxy_input(query)
    api_url = f"{API_BASE_URL}/api/check"

    try:
        resp = _session.get(api_url, params={"query": query}, timeout=30)
        data = resp.json()
    except Exception as exc:
        err_txt = (
            f"{PE['no']} <b>Proxy Gateway Offline</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{PE['warn']} Error: <code>{html.escape(str(exc))}</code>\n\n"
            "Please try again in a few moments."
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            IB("Try Again", callback_data="chk_another"),
            IB("Close", callback_data="chk_close")
        )
        return err_txt, False, markup

    if data.get("status") == "success":
        provider = data.get("provider", "owl").lower()
        header = f"{PE['search']} <b>{provider.upper()} PROXY · ACCOUNT INFO</b>"

        username = data.get("username", query)
        info = data.get("data", {})
        total_display = info.get("total_display") or f"{info.get('total_mb', 0)} MB"
        used_display = info.get("used_display") or f"{info.get('used_mb', 0)} MB"
        remaining_display = info.get("remaining_display") or f"{info.get('remaining_mb', 0)} MB"
        pct = info.get("percentage_remaining", 0)

        # 12-char progress bar
        filled = max(0, min(12, int(round((pct / 100.0) * 12))))
        bar = "█" * filled + "░" * (12 - filled)

        status_tag = f"{PE['active']} Active" if info.get("is_active") else f"{PE['depleted']} Depleted"
        checked_at = data.get("checked_at") or datetime.now().strftime("%d %b %Y, %I:%M %p (BD Time)")

        msg = (
            f"{header}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{PE['user']} <b>Username:</b>\n"
            f"<code>{html.escape(str(username))}</code>\n\n"
            f"{PE['package']} <b>Total Data:</b>    {total_display}\n"
            f"{PE['chart']} <b>Used Data:</b>     {used_display}\n"
            f"{PE['storage']} <b>Remaining:</b>     <b>{remaining_display}</b>\n\n"
            f"[{bar}]  {pct}% remaining\n\n"
            f"{PE['pin']} <b>Status:</b> {status_tag}\n"
            f"{PE['calendar']} <b>Checked at:</b> {checked_at}\n\n"
    #        f"{PE['globe']} <b>MB checker website:</b> {MB_CHECKER_WEBSITE}"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            IB("Refresh", callback_data="chk_refresh"),
            IB("Check Another", callback_data="chk_another")
        )
        markup.add(IB("Close", callback_data="chk_close"))

        return msg, True, markup
    else:
        err_msg = data.get("message") or "Proxy or username not found in database."
        msg = (
            f"{PE['no']} <b>PROXY CHECK FAILED</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{PE['warn']} <b>{html.escape(err_msg)}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{PE['globe']} <b>MB checker website:</b> {MB_CHECKER_WEBSITE}"
        )
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            IB("Check Another", callback_data="chk_another"),
            IB("Close", callback_data="chk_close")
        )
        return msg, False, markup

def format_bulk_check_view(lines: list) -> Tuple[str, types.InlineKeyboardMarkup]:
    """Bulk proxy check via /api/check/bulk."""
    bulk_url = f"{API_BASE_URL}/api/check/bulk"
    try:
        cleaned_queries = [clean_proxy_input(l) for l in lines[:100]]
        resp = _session.post(bulk_url, json={"queries": cleaned_queries}, timeout=45).json()
        if resp.get("status") == "success":
            msg = (
                f"{PE['bolt']} <b>BULK PROXY REPORT</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{PE['package']} <b>Total Checked:</b> {resp.get('total', len(lines))}\n"
                f"{PE['active']} <b>Active:</b> {resp.get('active_count', 0)}\n"
                f"{PE['depleted']} <b>Depleted:</b> {resp.get('depleted_count', 0)}\n"
                f"{PE['no']} <b>Not Found:</b> {resp.get('not_found_count', 0)}\n"
                f"{PE['storage']} <b>Remaining Data:</b> <b>{resp.get('total_remaining_display', '0 MB')}</b>\n\n"
                f"{PE['globe']} <b>MB checker website:</b> {MB_CHECKER_WEBSITE}"
            )
        else:
            msg = (
                f"{PE['no']} <b>BULK CHECK FAILED</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{PE['warn']} {html.escape(resp.get('message', 'Unknown bulk error'))}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{PE['globe']} <b>MB checker website:</b> {MB_CHECKER_WEBSITE}"
            )
    except Exception as exc:
        msg = (
            f"{PE['no']} <b>Bulk Gateway Offline</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{PE['warn']} Error: <code>{html.escape(str(exc))}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{PE['globe']} <b>MB checker website:</b> {MB_CHECKER_WEBSITE}"
        )

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        IB("Check Another", callback_data="chk_another"),
        IB("Close", callback_data="chk_close")
    )
    return msg, markup

def get_prompt_text_and_kb() -> Tuple[str, types.InlineKeyboardMarkup]:
    """Returns main prompt and cancel button."""
    txt = (
        f"{PE['search']} <b>PROXY & IP BALANCE CHECK (2-in-1)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Send your full proxy or username (OWL Proxy or IP Cook):\n\n"
        f"{PE['dot']} <b>Full Proxy:</b> <code>host:port:username:password</code>\n"
        f"{PE['dot']} <b>Username:</b>   <code>username</code>\n"
        f"{PE['dot']} <b>Port:User:</b>  <code>port:username</code>\n"
        f"{PE['dot']} <b>User:Pass:</b>  <code>username:password</code>\n"
        f"{PE['dot']} <b>Port:User:Pass:</b> <code>port:username:password</code>\n"
        f"{PE['dot']} <b>Host:Port:User:</b> <code>host:port:username</code>\n\n"
        f"{PE['globe']} <b>MB checker website:</b> {MB_CHECKER_WEBSITE}\n\n"
        "<i>/cancel to abort</i>"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(IB("Cancel", callback_data="chk_close"))
    return txt, markup

# ---------------- Blue "CHECK PROXY MB" keyboard button ----------------
MAIN_BTN_TEXT = "CHECK PROXY MB"
MAIN_BTN_ICON_ID = "5463352748751753567"  # premium search emoji

class _StyledKeyboardButton(types.KeyboardButton):
    """KeyboardButton with blue style + premium emoji icon (works on any telebot version)."""
    def to_dict(self):
        d = super().to_dict()
        d["style"] = "primary"                      # blue button
        d["icon_custom_emoji_id"] = MAIN_BTN_ICON_ID  # premium search emoji before text
        return d

def get_main_keyboard(styled: bool = True) -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True)
    if styled:
        kb.add(_StyledKeyboardButton(MAIN_BTN_TEXT))
    else:
        kb.add(types.KeyboardButton("\U0001F50D " + MAIN_BTN_TEXT))  # plain fallback
    return kb

@bot.message_handler(commands=["start"])
def handle_start_cmd(message: types.Message):
    welcome = f"{PE['search']} <b>Welcome!</b>\nTap the button below to check your proxy balance."
    try:
        bot.send_message(message.chat.id, welcome, reply_markup=get_main_keyboard(True))
    except Exception:
        bot.send_message(message.chat.id, welcome, reply_markup=get_main_keyboard(False))

@bot.message_handler(commands=["check"])
def handle_start(message: types.Message):
    text, markup = get_prompt_text_and_kb()
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: bool(m.text) and MAIN_BTN_TEXT in m.text.upper())
def handle_main_button(message: types.Message):
    text, markup = get_prompt_text_and_kb()
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(commands=["cancel"])
def handle_cancel(message: types.Message):
    user_last_query.pop(message.chat.id, None)
    bot.send_message(message.chat.id, f"{PE['no']} <b>Check session cancelled.</b>")

@bot.message_handler(func=lambda msg: True)
def handle_incoming_query(message: types.Message):
    raw_text = message.text.strip()
    if not raw_text or raw_text.startswith("/"):
        return

    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    if not lines:
        return

    if len(lines) > 1:
        wait_msg = bot.reply_to(message, f"{PE['hourglass']} <i>Checking bulk proxy balances...</i>")
        report_text, markup = format_bulk_check_view(lines)
        bot.edit_message_text(report_text, message.chat.id, wait_msg.message_id, reply_markup=markup)
        return

    single_query = lines[0]
    user_last_query[message.chat.id] = single_query

    wait_msg = bot.reply_to(message, f"{PE['hourglass']} <i>Verifying proxy balance...</i>")
    report_text, ok, markup = format_proxy_check_view(single_query)
    bot.edit_message_text(report_text, message.chat.id, wait_msg.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_checker_callbacks(call: types.CallbackQuery):
    data = call.data

    if data == "chk_close":
        user_last_query.pop(call.message.chat.id, None)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        bot.answer_callback_query(call.id, "Closed")
        return

    if data == "chk_another":
        text, markup = get_prompt_text_and_kb()
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=markup)
        bot.answer_callback_query(call.id, "Send proxy or username:")
        return

    if data == "chk_refresh":
        last_query = user_last_query.get(call.message.chat.id)
        if not last_query:
            bot.answer_callback_query(call.id, "Query expired. Please send proxy again.", show_alert=True)
            return

        bot.answer_callback_query(call.id, "Refreshing live balance...")
        report_text, ok, markup = format_proxy_check_view(last_query)
        try:
            bot.edit_message_text(report_text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except Exception:
            pass
        return

def run():
    print("=" * 75, flush=True)
    print("   [+] 2-in-1 Proxy Balance Checker Bot Starting...", flush=True)
    print(f"   API Gateway Base URL: {API_BASE_URL}", flush=True)
    print(f"   MB Checker Website:   {MB_CHECKER_WEBSITE}", flush=True)
    print("=" * 75, flush=True)

    try:
        me = bot.get_me()
        print(f"[OK] Bot connected successfully: @{me.username} (ID: {me.id})", flush=True)
    except Exception as e:
        print(f"[!] Warning connecting to Telegram getMe: {e}", flush=True)

    print("[RUN] Starting polling loop...", flush=True)
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=15, skip_pending=True)
        except Exception as exc:
            print(f"[!] Polling exception: {exc}. Reconnecting in 3s...", flush=True)
            time.sleep(3)

if __name__ == "__main__":
    run()
