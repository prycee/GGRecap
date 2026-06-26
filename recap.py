#!/usr/bin/env python3
"""
Gold & Silver daily recap mailer (AI-written).

What it does, end to end:
  1. Pulls live gold + silver spot prices from a free metals API.
  2. Has Claude web-search the day's actual drivers (Fed, dollar, oil,
     geopolitics) and write a ~75-second recap + forecast around those prices.
  3. Emails the finished recap via Gmail.

Built to run free on GitHub Actions (see recap.yml), or any cron host.

REQUIRED environment variables (set these as GitHub repo "Secrets"):
  ANTHROPIC_API_KEY    Your Anthropic API key  (console.anthropic.com)
  GMAIL_ADDRESS        The Gmail account that SENDS the mail
  GMAIL_APP_PASSWORD   A Gmail *App Password* — not your normal password.
                       (Google Account > Security > 2-Step Verification >
                        App passwords. 2FA must be on to generate one.)
OPTIONAL:
  RECIPIENT            Where to send it. Default: goldengamesllc@gmail.com
  EDITION              "OPEN" or "CLOSE". If unset, picked from time of day.
"""

import os
import sys
import smtplib
import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

import requests
import anthropic

# ------------------------------- config -------------------------------
GOLD_URL    = "https://api.gold-api.com/price/XAU"   # free, no key needed
SILVER_URL  = "https://api.gold-api.com/price/XAG"
MODEL       = "claude-sonnet-4-6"
TIMEZONE    = ZoneInfo("America/New_York")
RECIPIENT   = os.environ.get("RECIPIENT", "goldengamesllc@gmail.com")
SENDER_NAME = "Golden Games Market Desk"
# ----------------------------------------------------------------------


def fetch_spot(url: str) -> float:
    """Return spot price (USD/oz). gold-api.com returns {'price': 4063.17, ...}.
    If you switch providers, change the URLs above and the key below."""
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return float(r.json()["price"])


def get_edition() -> str:
    """OPEN before noon ET, CLOSE after — unless EDITION is set explicitly."""
    edition = os.environ.get("EDITION", "").strip().upper()
    if edition in ("OPEN", "CLOSE"):
        return edition
    return "OPEN" if datetime.datetime.now(TIMEZONE).hour < 12 else "CLOSE"


def write_recap(edition: str, gold: float, silver: float) -> str:
    """Have Claude research today's drivers and write the email body."""
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    today = datetime.datetime.now(TIMEZONE).strftime("%A, %B %d, %Y")
    ratio = gold / silver

    if edition == "OPEN":
        brief = (
            "This is the MARKET OPEN edition (pre-bell, forward-looking). "
            "Cover overnight price action, the main catalyst driving metals, one "
            "live geopolitical thread, and what to watch today including key "
            "support and resistance levels for gold."
        )
        closer = "what to watch today"
    else:
        brief = (
            "This is the MARKET CLOSE edition (after the bell, recap + forecast). "
            "Cover how gold and silver finished, the decisive driver today, the "
            "longer-term backdrop (central-bank buying, major bank targets), and a "
            "forecast for the next session with key levels for gold and silver."
        )
        closer = "the forecast for the next session"

    prompt = f"""You are writing a daily precious-metals email recap for {today}.

LIVE SPOT PRICES (authoritative — use these exact numbers, do not alter them):
- Gold:   ${gold:,.2f}/oz
- Silver: ${silver:,.2f}/oz
- Gold/silver ratio: {ratio:.1f}

{brief}

Use web search to find TODAY'S real market drivers: the Fed, the US dollar,
inflation data, oil prices, and any live geopolitical events moving gold and silver.

Write ONLY the email body. Requirements:
- 150-200 words, tight and punchy, readable aloud in about 75 seconds.
- Order: prices first, then why they moved, then the geopolitical/macro thread,
  then {closer}.
- Plain text only. No markdown, no headers, no bullet symbols, no URLs or citations.
- Do not invent figures beyond the prices/ratio above and what you find in search.
  If something is uncertain, keep it qualitative rather than guessing a number.
"""

    resp = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
    )

    # Keep only the assistant's text blocks; ignore the search machinery blocks.
    text = "".join(
        b.text for b in resp.content if getattr(b, "type", "") == "text"
    ).strip()

    if not text:
        raise RuntimeError("Claude returned no text — check the API response.")
    return text


def send_email(subject: str, body: str) -> None:
    user = os.environ["GMAIL_ADDRESS"]
    pw   = os.environ["GMAIL_APP_PASSWORD"]

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"]    = f"{SENDER_NAME} <{user}>"
    msg["To"]      = RECIPIENT
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user, pw)
        server.send_message(msg)


def main() -> None:
    # Markets are closed on weekends — don't send.
    if datetime.datetime.now(TIMEZONE).weekday() >= 5:
        print("Weekend — markets closed. Skipping.")
        return

    edition = get_edition()
    gold    = fetch_spot(GOLD_URL)
    silver  = fetch_spot(SILVER_URL)
    body    = write_recap(edition, gold, silver)

    today = datetime.datetime.now(TIMEZONE).strftime("%A, %B %d, %Y")
    icon  = "\u2600\ufe0f" if edition == "OPEN" else "\U0001f319"   # sun / moon
    label = "Market Open" if edition == "OPEN" else "Market Close"
    subject = f"{icon} Gold & Silver \u2014 {label} \u2014 {today}"

    send_email(subject, body)
    print(f"Sent {edition} recap to {RECIPIENT}: "
          f"gold ${gold:,.2f}, silver ${silver:,.2f}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:                      # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
