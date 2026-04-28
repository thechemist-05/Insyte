import requests
from collections import Counter
import re

API_KEY = "e080150c2b02476790ebecbe9758772c"


def fetch_data(keyword: str, limit: int = 100) -> list[dict]:
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": keyword,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": min(limit, 100),
        "apiKey": API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            print("[data] API error:", data)
            return []

        results = []
        for article in data.get("articles", []):
            title = article.get("title") or ""
            description = article.get("description") or ""
            text = (title + " " + description).strip()

            if len(text) < 20:
                continue

            results.append({
                "text": text,
                "date": article.get("publishedAt", ""),
            })

        return results

    except Exception as e:
        print("[data] error:", e)
        return []


def fetch_trending_keywords(limit: int = 8) -> list[str]:
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "language": "en",
        "pageSize": 100,
        "apiKey": API_KEY,
    }

    STOPWORDS = {
        "with", "from", "this", "that", "have", "will", "their",
        "about", "after", "before", "there", "which", "when",
        "where", "what", "your", "more", "than", "they",
        "been", "were", "into", "over", "also", "said",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            print("[trend] API error:", data)
            return []

        words = []
        for article in data.get("articles", []):
            title = article.get("title") or ""
            description = article.get("description") or ""
            text = (title + " " + description).lower()
            tokens = re.findall(r'\b[a-z]{4,}\b', text)
            words.extend(tokens)

        filtered = [w for w in words if w not in STOPWORDS]
        freq = Counter(filtered)
        trending = [word for word, _ in freq.most_common(limit)]

        print("[trend] extracted:", trending)
        return trending

    except Exception as e:
        print("[trend] error:", e)
        return []