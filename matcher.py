from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from models import DEFAULT_THRESHOLD, Match, Passage


def match_passages(
    output_passages: list[Passage],
    input_passages: list[Passage],
    threshold: float = DEFAULT_THRESHOLD,
) -> list[Match | None]:
    if not input_passages or not output_passages:
        return [None] * len(output_passages)

    input_texts = [p.text for p in input_passages]
    output_texts = [p.text for p in output_passages]

    vectorizer = TfidfVectorizer()
    try:
        input_tfidf = vectorizer.fit_transform(input_texts)
        output_tfidf = vectorizer.transform(output_texts)
    except ValueError:  # sklearn ValueError on empty vocabulary — never bare Exception
        return [None] * len(output_passages)

    similarity = cosine_similarity(output_tfidf, input_tfidf)

    results: list[Match | None] = []
    for out_idx, out_passage in enumerate(output_passages):
        scores = similarity[out_idx]
        best_idx = scores.argmax()
        best_score = float(scores[best_idx])

        if best_score >= threshold:
            results.append(
                Match(
                    output_passage=out_passage,
                    input_passage=input_passages[best_idx],
                    score=round(best_score, 4),
                    method="tfidf",
                )
            )
        else:
            results.append(None)

    return results
