"""
Seed the Qdrant vector store with the initial women's health policy corpus.
Run once after standing up the stack: python scripts/seed_corpus.py

Sources ingested:
  - CMS LCD/NCD PDFs (downloaded from cms.gov)
  - Payer coverage policy PDFs (Aetna, BCBS, UHC, Cigna, Humana)
  - State mandate JSON (21 states with IVF / hormone therapy coverage laws)
  - AdvaMed Women's Health CCR White Paper
  - Precedent pathway library (Markdown files in corpus/precedents/)
"""
import os, logging
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CORPUS_DIR = Path("corpus/sources")
COLLECTION = os.getenv("QDRANT_COLLECTION", "womens_health_policy")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
    separators=["\n\n", "\n", ". ", " "],
)


def seed():
    client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION not in existing:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
        )
        logger.info(f"Collection '{COLLECTION}' created")

    if not CORPUS_DIR.exists():
        logger.warning(f"Corpus directory {CORPUS_DIR} not found — create it and add policy PDFs")
        return

    loader = DirectoryLoader(str(CORPUS_DIR), glob="**/*.pdf", loader_cls=PyPDFLoader)
    raw_docs = loader.load()
    docs = splitter.split_documents(raw_docs)
    logger.info(f"Loaded {len(raw_docs)} raw docs → {len(docs)} chunks")

    Qdrant.from_documents(
        documents=docs,
        embedding=embeddings,
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        collection_name=COLLECTION,
    )
    logger.info("Corpus seeded successfully")


if __name__ == "__main__":
    seed()
