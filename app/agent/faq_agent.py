from pathlib import Path
from typing import List, Tuple
import random
import yaml
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class CyberFAQAgent:
    def __init__(self, kb_path: Path | None = None, min_similarity: float = 0.15):
        if kb_path is None:
            kb_path = Path(__file__).parent / "knowledge_base.yaml"
        
        # Ensure path is absolute
        kb_path = Path(kb_path).resolve()
        
        if not kb_path.exists():
            raise FileNotFoundError(f"Knowledge base not found at {kb_path}")
        
        with open(kb_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.faq = data.get("faq", [])
        self.tips = data.get("tips", [])
        self.min_similarity = min_similarity

        # Build corpus including both questions and answers for better matching
        corpus = []
        for item in self.faq:
            q = item.get("question", "")
            a = item.get("answer", "")
            cat = item.get("category", "")
            # Combine all text for better semantic matching
            corpus.append(f"{q} {a} {cat}")
        
        self.df = pd.DataFrame(self.faq)
        
        # Improved French tokenization
        french_stop_words = [
            'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 
            'mais', 'donc', 'car', 'ni', 'est', 'sont', 'a', 'ai', 'as', 'ont',
            'ce', 'ces', 'cet', 'cette', 'se', 'sa', 'son', 'ses', 'il', 'elle',
            'nous', 'vous', 'ils', 'elles', 'je', 'tu', 'mon', 'ma', 'mes'
        ]
        
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=1000,
            stop_words=french_stop_words,
            lowercase=True,
            strip_accents='unicode',
            token_pattern=r'\b\w+\b'
        )
        self.matrix = self.vectorizer.fit_transform(corpus)

    def answer(self, query: str) -> Tuple[str, float, dict]:
        if not query or not query.strip():
            return (
                "Veuillez poser une question liée à la cybersécurité.",
                0.0,
                {}
            )

        vec = self.vectorizer.transform([query])
        sims = cosine_similarity(vec, self.matrix)[0]
        best_idx = int(sims.argmax())
        best_score = float(sims[best_idx])
        best_row = self.df.iloc[best_idx].to_dict()

        if best_score >= self.min_similarity:
            return best_row.get("answer", ""), best_score, best_row

        fallback = (
            "Je n'ai pas une réponse précise pour cette question. "
            "Voici quelques conseils généraux : évitez de cliquer sur des liens "
            "suspects, utilisez des mots de passe robustes (12+ caractères), "
            "activez la MFA partout où c'est possible. "
            "Pour les incidents ou questions spécifiques, contactez l'équipe cybersécurité."
        )
        return fallback, best_score, {}

    def tip(self) -> str:
        if not self.tips:
            return (
                "Astuce: Activez l'authentification multifacteur et ne réutilisez pas vos mots de passe."
            )
        return random.choice(self.tips)

    def search(self, query: str, top_k: int = 3) -> List[Tuple[dict, float]]:
        """Return top_k related FAQ entries with their similarity scores."""
        if not query or not query.strip():
            return []
        vec = self.vectorizer.transform([query])
        sims = cosine_similarity(vec, self.matrix)[0]
        idxs = sims.argsort()[::-1][:top_k]
        results = []
        for i in idxs:
            score = float(sims[int(i)])
            if score >= 0.10:  # Only return relevant results
                results.append((self.df.iloc[int(i)].to_dict(), score))
        return results
