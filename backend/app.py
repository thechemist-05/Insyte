import re
from collections import Counter

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.data import fetch_data, fetch_trending_keywords
from backend.utils import preprocess
from backend.model import (
    analyze_sentiment,
    convert_to_score,
    analyze_emotions,
    emotion_summary,
)

app = FastAPI(title="Insyte API", version="5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

CACHE: dict = {}


# ── helpers ────────────────────────────────────────────────────────────────────

def sentiment_distribution(scores: list[float]) -> dict:
    total = len(scores) or 1
    pos = sum(1 for s in scores if s > 0.2)
    neg = sum(1 for s in scores if s < -0.2)
    neu = len(scores) - pos - neg

    return {
        "positive": pos,
        "neutral": neu,
        "negative": neg,
        "positive_pct": round(pos / total * 100, 1),
        "negative_pct": round(neg / total * 100, 1),
    }


def trend_score(scores: list[float], tweets: list[dict]) -> float:
    if len(scores) < 8:
        return 0.0

    tweet_score_pairs = list(zip(tweets, scores))
    tweet_score_pairs.sort(key=lambda x: x[0].get("date", ""), reverse=True)
    sorted_scores = [s for _, s in tweet_score_pairs]

    split = max(1, len(sorted_scores) // 4)
    recent_avg = sum(sorted_scores[:split]) / split
    older_avg = sum(sorted_scores[split:]) / (len(sorted_scores) - split)

    return round(recent_avg - older_avg, 3)


def extract_keywords(texts: list[str], top_n: int = 5) -> list[str]:
    words: list[str] = []
    for t in texts:
        words += re.findall(r'\b[a-zA-Z]{4,}\b', t.lower())

    return [w for w, _ in Counter(words).most_common(top_n)]


def risk_level(emotions: dict) -> str:
    fear = emotions.get("fear", 0)
    anger = emotions.get("anger", 0)
    total = sum(emotions.values()) or 1
    risk = (fear + anger) / total

    if risk > 0.25:
        return "High"
    if risk > 0.05:
        return "Medium"
    return "Low"


def compute_launch_score(
    avg: float, volume: int, trend: float, emotions: dict
) -> float:
    total = sum(emotions.values()) or 1
    joy_ratio = emotions.get("joy", 0) / total

    score = (
        ((avg + 1) / 2) * 0.30
        + min(volume / 200, 1.0) * 0.1
        + ((trend + 1) / 2) * 0.15
        + joy_ratio * 0.45
    )
    return round(score * 100, 2)


def recommendation(score: float, dist: dict, risk: str) -> str:
    if score >= 70 and risk == "Low":
        return "Strong launch signal — market is favorable."
    if score >= 50:
        return "Proceed with caution — moderate sentiment."
    if risk == "High":
        return "High risk — strong negative emotions detected."
    return "Not ready — improve perception before launch."


# ── routes ─────────────────────────────────────────────────────────────────────

@app.get("/analyze")
def analyze(keyword: str = Query(...), limit: int = 80):
    if keyword in CACHE:
        return CACHE[keyword]

    raw = fetch_data(keyword, limit)
    if not raw:
        raise HTTPException(status_code=404, detail="No data found")

    tweets = preprocess(raw)
    texts = [t["text"] for t in tweets]

    scores = convert_to_score(analyze_sentiment(texts))
    avg_score = round(sum(scores) / len(scores), 4) if scores else 0.0

    emotions = emotion_summary(analyze_emotions(texts[:60]))
    dist = sentiment_distribution(scores)
    trend = trend_score(scores, tweets)
    launch = compute_launch_score(avg_score, len(texts), trend, emotions)
    risk = risk_level(emotions)

    result = {
        "keyword": keyword,
        "total_posts": len(texts),
        "language_breakdown": dict(Counter(t["lang"] for t in tweets)),
        "average_sentiment": avg_score,
        "sentiment_trend": trend,
        "distribution": dist,
        "emotions": emotions,
        "top_keywords": extract_keywords(texts),
        "risk_level": risk,
        "confidence": round(min(len(texts) / 100, 1.0), 2),
        "launch_score": launch,
        "recommendation": recommendation(launch, dist, risk),
    }

    CACHE[keyword] = result
    return result


@app.get("/trending")
def trending():
    if "trending" in CACHE:
        return CACHE["trending"]

    keywords = fetch_trending_keywords()
    if not keywords:
        raise HTTPException(status_code=500, detail="Failed to fetch trends")

    results = []
    for keyword in keywords:
        raw = fetch_data(keyword, 30)
        tweets = preprocess(raw)
        texts = [t["text"] for t in tweets]

        if not texts:
            continue

        scores = convert_to_score(analyze_sentiment(texts))
        avg = round(sum(scores) / len(scores), 3) if scores else 0.0

        results.append({
            "keyword": keyword,
            "score": avg,
            "volume": len(texts),
        })

    results.sort(key=lambda x: x["volume"], reverse=True)
    CACHE["trending"] = results
    return results