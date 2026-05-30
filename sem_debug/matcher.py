from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import DEFAULT_THRESHOLD, Match, Passage


def match_passages(
    output_passages: list[Passage],
    input_passages: list[Passage],
    threshold: float = DEFAULT_THRESHOLD,
    semantic: bool = False,
) -> tuple[list[Match], list[tuple[Passage, float]]]:
    if not input_passages or not output_passages:
        return [], [(p, 0.0) for p in output_passages]

    input_texts = [p.text for p in input_passages]
    output_texts = [p.text for p in output_passages]

    vectorizer = TfidfVectorizer()
    try:
        input_tfidf = vectorizer.fit_transform(input_texts)
        output_tfidf = vectorizer.transform(output_texts)
    except ValueError:  # sklearn ValueError on empty vocabulary — never bare Exception
        return [], [(p, 0.0) for p in output_passages]

    similarity = cosine_similarity(output_tfidf, input_tfidf)

    matched: list[Match] = []
    unattributed: list[tuple[Passage, float]] = []
    for out_idx, out_passage in enumerate(output_passages):
        scores = similarity[out_idx]
        best_idx = scores.argmax()
        best_score = float(scores[best_idx])

        if best_score >= threshold:
            matched.append(
                Match(
                    output_passage=out_passage,
                    input_passage=input_passages[best_idx],
                    score=round(best_score, 4),
                    method="tfidf",
                )
            )
        else:
            unattributed.append((out_passage, best_score))

    if semantic and unattributed:
        try:
            import sentence_transformers
        except ModuleNotFoundError:
            raise ImportError(
                "sentence-transformers is required for semantic matching. "
                "Install it: pip install -r requirements-semantic.txt"
            )

        model = sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2")
        unat_texts = [p.text for p, _ in unattributed]
        input_texts = [p.text for p in input_passages]
        unat_emb = model.encode(unat_texts)
        input_emb = model.encode(input_texts)
        sem_sim = cosine_similarity(unat_emb, input_emb)

        survived: list[tuple[Passage, float]] = []
        for i, (passage, tfidf_score) in enumerate(unattributed):
            sem_scores = sem_sim[i]
            best_sem_idx = sem_scores.argmax()
            best_sem_score = float(sem_scores[best_sem_idx])
            if best_sem_score >= threshold:
                matched.append(
                    Match(
                        output_passage=passage,
                        input_passage=input_passages[best_sem_idx],
                        score=round(best_sem_score, 4),
                        method="semantic",
                    )
                )
            else:
                survived.append((passage, tfidf_score))
        unattributed = survived

    return matched, unattributed
