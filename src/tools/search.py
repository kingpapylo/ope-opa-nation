"""Web search tool using DuckDuckGo (no API key required)."""

import urllib.request
import urllib.parse
import json
import re


DEFINITION = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for information. Returns a list of results with titles, URLs, and snippets.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 5).",
                },
            },
            "required": ["query"],
        },
    },
}


def search(query: str, max_results: int = 5) -> str:
    """Search DuckDuckGo and return formatted results."""
    try:
        # DuckDuckGo Instant Answer API (free, no key needed)
        params = urllib.parse.urlencode({"q": query, "format": "json", "no_html": "1"})
        url = f"https://api.duckduckgo.com/?{params}"

        req = urllib.request.Request(url, headers={"User-Agent": "cli-agent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        results = []

        # Abstract (main answer)
        if data.get("AbstractText"):
            results.append(
                f"**Summary:** {data['AbstractText']}\n"
                f"Source: {data.get('AbstractURL', '')}"
            )

        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                text = topic["Text"]
                url = topic.get("FirstURL", "")
                results.append(f"• {text}\n  {url}")

        if results:
            return "\n\n".join(results[:max_results])

        # Fallback: try HTML scrape of DuckDuckGo
        return _scrape_search(query, max_results)

    except Exception as e:
        return f"Search error: {e}"


def _scrape_search(query: str, max_results: int) -> str:
    """Fallback: scrape DuckDuckGo HTML results."""
    try:
        params = urllib.parse.urlencode({"q": query})
        url = f"https://html.duckduckgo.com/html/?{params}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # Extract result snippets with simple regex
        titles = re.findall(r'class="result__title"[^>]*>.*?<a[^>]*>(.*?)</a>', html, re.DOTALL)
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</span>', html, re.DOTALL)
        urls = re.findall(r'class="result__url"[^>]*>(.*?)</a>', html, re.DOTALL)

        # Clean HTML tags
        def strip_tags(s):
            return re.sub(r"<[^>]+>", "", s).strip()

        results = []
        for i in range(min(max_results, len(snippets))):
            title = strip_tags(titles[i]) if i < len(titles) else "Result"
            snippet = strip_tags(snippets[i])
            url = strip_tags(urls[i]) if i < len(urls) else ""
            results.append(f"**{title}**\n{snippet}\n{url}")

        return "\n\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search error: {e}"
