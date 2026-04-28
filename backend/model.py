import torch
from transformers import pipeline

DEVICE = 0 if torch.cuda.is_available() else -1

sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment",
    device=DEVICE,
    truncation=True,
    max_length=512,
)

emotion_pipeline = pipeline(
    "text-classification",
    model="bhadresh-savani/distilbert-base-uncased-emotion",
    device=DEVICE,
    truncation=True,
    max_length=512,
)

_BATCH_SIZE = 32


def _safe_batch(texts: list[str]) -> list[str]:
    return [t[:512] for t in texts if t and t.strip()]


def analyze_sentiment(texts: list[str]) -> list[dict]:
    clean = _safe_batch(texts)
    results = []

    for i in range(0, len(clean), _BATCH_SIZE):
        results += sentiment_pipeline(clean[i : i + _BATCH_SIZE])

    return results


def convert_to_score(results: list[dict]) -> list[float]:
    scores = []

    for r in results:
        try:
            stars = int(r["label"][0])
            scores.append(round((stars - 3) / 2, 3))
        except Exception:
            scores.append(0.0)

    return scores


def analyze_emotions(texts: list[str]) -> list[dict]:
    clean = _safe_batch(texts)
    results = []

    for i in range(0, len(clean), _BATCH_SIZE):
        results += emotion_pipeline(clean[i : i + _BATCH_SIZE])

    return results


def emotion_summary(results: list[dict]) -> dict:
    summary: dict[str, int] = {}

    for r in results:
        label = r.get("label", "unknown")
        summary[label] = summary.get(label, 0) + 1

    return dict(sorted(summary.items(), key=lambda x: -x[1]))