"""
Web & API tools — webpage fetch/summarize, weather, Wikipedia, email sender, file downloader.
All use only the Python standard library (no extra dependencies).
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import re
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path


# ── Webpage fetch ─────────────────────────────────────────────────────────────

FETCH_DEFINITION = {
    "type": "function",
    "function": {
        "name": "web_fetch",
        "description": "Fetch and extract the readable text content from a webpage URL.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch."},
                "max_chars": {
                    "type": "integer",
                    "description": "Maximum characters to return. Default 3000.",
                },
            },
            "required": ["url"],
        },
    },
}


def web_fetch(url: str, max_chars: int = 3000) -> str:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; OPE-OPA-NATION/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # Strip scripts, styles, tags
        html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars] + ("…" if len(text) > max_chars else "")
    except Exception as e:
        return f"Error fetching {url}: {e}"


# ── Weather ───────────────────────────────────────────────────────────────────

WEATHER_DEFINITION = {
    "type": "function",
    "function": {
        "name": "weather",
        "description": "Get current weather for a city or location using wttr.in (no API key needed).",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or location, e.g. 'Lagos', 'New York', 'London'.",
                },
            },
            "required": ["location"],
        },
    },
}


def weather(location: str) -> str:
    try:
        loc = urllib.parse.quote(location)
        url = f"https://wttr.in/{loc}?format=3"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8").strip()
    except Exception as e:
        return f"Error getting weather: {e}"


# ── Wikipedia ─────────────────────────────────────────────────────────────────

WIKIPEDIA_DEFINITION = {
    "type": "function",
    "function": {
        "name": "wikipedia",
        "description": "Search Wikipedia and return a summary of the top result.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Topic to search for."},
            },
            "required": ["query"],
        },
    },
}


def wikipedia(query: str) -> str:
    try:
        # Search for the article title
        params = urllib.parse.urlencode({"action": "query", "list": "search",
                                         "srsearch": query, "format": "json", "srlimit": 1})
        url = f"https://en.wikipedia.org/w/api.php?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "OPE-OPA-NATION/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        results = data.get("query", {}).get("search", [])
        if not results:
            return f"No Wikipedia results found for: {query}"

        title = results[0]["title"]

        # Fetch the summary
        params2 = urllib.parse.urlencode({
            "action": "query", "titles": title,
            "prop": "extracts", "exintro": "1",
            "explaintext": "1", "format": "json",
        })
        url2 = f"https://en.wikipedia.org/w/api.php?{params2}"
        req2 = urllib.request.Request(url2, headers={"User-Agent": "OPE-OPA-NATION/1.0"})
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            data2 = json.loads(resp2.read())

        pages = data2.get("query", {}).get("pages", {})
        page = next(iter(pages.values()))
        extract = page.get("extract", "No summary available.")
        extract = extract[:2000] + ("…" if len(extract) > 2000 else "")

        wiki_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title)}"
        return f"**{title}**\n{extract}\n\nSource: {wiki_url}"
    except Exception as e:
        return f"Error fetching Wikipedia: {e}"


# ── Email sender ──────────────────────────────────────────────────────────────

EMAIL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "send_email",
        "description": (
            "Send an email via Gmail SMTP. "
            "Requires GMAIL_ADDRESS and GMAIL_APP_PASSWORD environment variables."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address."},
                "subject": {"type": "string", "description": "Email subject."},
                "body": {"type": "string", "description": "Email body text."},
            },
            "required": ["to", "subject", "body"],
        },
    },
}


def send_email(to: str, subject: str, body: str) -> str:
    sender = os.environ.get("GMAIL_ADDRESS")
    password = os.environ.get("GMAIL_APP_PASSWORD")

    if not sender or not password:
        return (
            "Error: Gmail credentials not set.\n"
            "Set these environment variables:\n"
            "  export GMAIL_ADDRESS='you@gmail.com'\n"
            "  export GMAIL_APP_PASSWORD='your-app-password'\n"
            "Get an app password at: https://myaccount.google.com/apppasswords"
        )
    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(sender, password)
            server.sendmail(sender, to, msg.as_string())

        return f"Email sent to {to}"
    except Exception as e:
        return f"Error sending email: {e}"


# ── File downloader ───────────────────────────────────────────────────────────

DOWNLOAD_DEFINITION = {
    "type": "function",
    "function": {
        "name": "download_file",
        "description": "Download a file from a URL and save it to a local path.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to download from."},
                "output_path": {
                    "type": "string",
                    "description": "Local file path to save to.",
                },
            },
            "required": ["url", "output_path"],
        },
    },
}


def download_file(url: str, output_path: str) -> str:
    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; OPE-OPA-NATION/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()

        with open(output_path, "wb") as f:
            f.write(data)

        size_kb = len(data) / 1024
        return f"Downloaded {size_kb:.1f} KB → {output_path}"
    except Exception as e:
        return f"Error downloading {url}: {e}"


ALL_DEFINITIONS = [
    FETCH_DEFINITION,
    WEATHER_DEFINITION,
    WIKIPEDIA_DEFINITION,
    EMAIL_DEFINITION,
    DOWNLOAD_DEFINITION,
]
