import re
from collections import Counter
import pandas as pd

RISK_TERMS = {
    "phishing": ["verify your account", "password", "login", "credential", "otp"],
    "financial_scam": ["urgent payment", "send money", "wallet", "investment guaranteed", "double your money"],
    "malware": ["download this file", "install apk", "unknown attachment", "disable antivirus"],
    "coordinated_activity": ["share this everywhere", "copy and paste", "everyone post", "same message"],
}

def analyze_text(text: str) -> dict:
    normalized = str(text).lower()
    matches = [category for category, terms in RISK_TERMS.items()
               if any(term in normalized for term in terms)]
    # This is a transparent heuristic indicator, not a verdict about a person.
    score = min(95, 15 + 25 * len(matches))
    if not matches:
        score = 5
    return {
        "risk_score": score,
        "risk_labels": matches or ["no_rule_match"],
        "evidence": [term for terms in RISK_TERMS.values() for term in terms if term in normalized],
    }

def analyze_dataset(df: pd.DataFrame) -> pd.DataFrame:
    results = df["text"].apply(analyze_text).apply(pd.Series)
    return pd.concat([df.reset_index(drop=True), results], axis=1)

def filter_by_text(df: pd.DataFrame, query: str | None) -> pd.DataFrame:
    if not query:
        return df
    return df[df["text"].str.contains(query, case=False, na=False, regex=False)]

def top_terms(texts, limit=8):
    stop = {"this", "that", "with", "from", "your", "have", "will", "they", "them", "there", "about", "into", "just", "https"}
    words = re.findall(r"\b[a-zA-Z]{4,}\b", " ".join(map(str, texts)).lower())
    return Counter(w for w in words if w not in stop).most_common(limit)
