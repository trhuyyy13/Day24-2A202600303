"""Task A.1 — Synthetic Test Set Generation.

Generate test set 50 questions từ document corpus với distribution:
- 50% simple (single-hop)
- 25% reasoning (multi-step inference)
- 25% multi-context (cross-document)

Corpus: Day 18 data (BCTC.pdf + Nghị định 13/2023 PDF).

Usage:
    python phase-a/generate_testset.py

Output:
    phase-a/testset_v1.csv  (>=50 rows, 4 columns)
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
DAY18 = ROOT / "Day18-Track3-Production-RAG"
DATA_DIR = DAY18 / "data"
OUT_CSV = ROOT / "phase-a" / "testset_v1.csv"


def load_corpus():
    """Load Day 18 PDF corpus as LangChain documents."""
    from langchain_community.document_loaders import PyPDFLoader
    docs = []
    for pdf in DATA_DIR.glob("*.pdf"):
        print(f"  Loading {pdf.name}")
        loader = PyPDFLoader(str(pdf))
        docs.extend(loader.load())
    print(f"  Loaded {len(docs)} pages from {len(list(DATA_DIR.glob('*.pdf')))} PDFs")
    return docs


def generate_with_ragas(documents, test_size: int = 50):
    """Generate using RAGAS TestsetGenerator (newer API for ragas>=0.2)."""
    from ragas.testset import TestsetGenerator
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    generator_llm = ChatOpenAI(model="gpt-4o-mini")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    generator = TestsetGenerator.from_langchain(
        llm=generator_llm,
        embedding_model=embeddings,
    )

    print(f"  Generating {test_size} questions...")
    testset = generator.generate_with_langchain_docs(
        documents,
        testset_size=test_size,
    )
    return testset.to_pandas()


def normalize_dataframe(df):
    """Normalize columns to match acceptance criteria:
    Required: question, ground_truth, contexts, evolution_type
    """
    rename_map = {
        "user_input": "question",
        "reference": "ground_truth",
        "reference_contexts": "contexts",
        "synthesizer_name": "evolution_type",
    }
    for old, new in rename_map.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})

    if "evolution_type" in df.columns:
        df["evolution_type"] = df["evolution_type"].astype(str).map(_map_evo_type)

    required = ["question", "ground_truth", "contexts", "evolution_type"]
    for col in required:
        if col not in df.columns:
            df[col] = ""
    return df[required + [c for c in df.columns if c not in required]]


def _map_evo_type(s: str) -> str:
    s = s.lower()
    if "multi_hop_specific" in s or "multi_context" in s:
        return "multi_context"
    if "multi_hop_abstract" in s or "reasoning" in s or "abstract" in s:
        return "reasoning"
    if "single_hop" in s or "simple" in s or "specific" in s:
        return "simple"
    return "simple"


def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY chưa được set trong .env", file=sys.stderr)
        sys.exit(1)

    print("[1/3] Loading corpus...")
    docs = load_corpus()
    if not docs:
        print("ERROR: Không tìm thấy PDF trong Day18-Track3-Production-RAG/data/", file=sys.stderr)
        sys.exit(1)

    print("[2/3] Generating test set với RAGAS...")
    df = generate_with_ragas(docs, test_size=50)

    print("[3/3] Normalizing & saving...")
    df = normalize_dataframe(df)
    OUT_CSV.parent.mkdir(exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    print(f"\nDone! Saved {len(df)} questions -> {OUT_CSV}")
    print("\nDistribution:")
    print(df["evolution_type"].value_counts())


if __name__ == "__main__":
    main()
